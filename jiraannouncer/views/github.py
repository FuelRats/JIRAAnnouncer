import hmac
import time
import logging
from json import JSONDecodeError

from sys import hexversion

from pyramid.view import view_config

from ..utils import jsondump, send, getlast, demarkdown, devsay
from ..models import githubmodels

log = logging.getLogger(__name__)


@view_config(route_name='github', renderer="json")
def github(prequest):
    """Handle GitHub events."""
    settings = prequest.registry.settings
    github_secret = settings['github_secret'] if 'github_secret' in settings else None
    lastmessage = getlast()
    data = prequest.body
    message = ""
    domessage = True
    gitrecord = None
    timestamp = int(time.time())

    if 'X-GitHub-Event' not in prequest.headers:
        log.error("Malformed request to GitHub webhook handler (Missing X-Github-Event)")
        devsay(
             "[\x0315GitHub\x03] Malformed request to GitHub webhook handler (Missing X-GitHub-Event header)")
        return

    if github_secret is not None:
        header_signature = prequest.headers['X-Hub-Signature']
        if header_signature is None:
            log.critical("No signature sent in GitHub event, aborting.")
            return
        sha_name, signature = header_signature.split('=')
        if sha_name != 'sha1':
            log.critical("Signature not in SHA1 format, aborting.")
            return

        mac = hmac.new(bytes(github_secret, 'utf8'), msg=prequest.body, digestmod='sha1')

        if hexversion >= 0x020707F0:
            if not hmac.compare_digest(str(mac.hexdigest()), str(signature)):
                log.critical("Signature mismatch, GitHub event not parsed!")
                return
        else:
            # Well, aren't you a special snowflake?
            if not str(mac.hexdigest()) == str(signature):
                log.critical("Signature mismatch! GitHub event not parsed.")
                log.debug(f"{mac.hexdigest()} vs {str(signature)}")
                devsay(f"Invalid MAC in GitHub message: {str(signature)}")
                return

    event = prequest.headers['X-GitHub-Event']
    try:
        request = prequest.json_body
    except JSONDecodeError:
        log.error("Error loading GitHub payload:")
        log.debug(data)
        devsay("A GitHub payload failed to decode to JSON!")
        return
    domessage = True

    if 'repository' in request and request['repository']['name'] in ["pipsqueak3", "limpet", "MechaChainsaw"]:
        channels = ['#mechadev']
    else:
        channels = ['#rattech']

    if event == 'issues':
        message = (f"\x0314 {request['sender']['login']} \x03{request['action']} issue #{request['issue']['number']}"
                   f": \"{request['issue']['title']}\" in \x0306{request['repository']['name']}\x03. \x02\x0311"
                   f"{request['issue']['html_url']}\x02\x03")
        gitrecord = githubmodels.GitHubMessage(action=request['action'] or None, timestamp=timestamp,
                                               number=request['issue']['number'] or None,
                                               issue=request['issue'] or None, comment=None,
                                               repository=request['repository'] or None, organization='NA',
                                               sender=request['sender'], pull_request=None,
                                               changes=None)
    elif event == 'issue_comment':
        lastrecord = prequest.dbsession.query(githubmodels.GitHubMessage).order_by(
            githubmodels.GitHubMessage.id.desc()).first()
        log.debug(lastrecord)
        if lastrecord.issue is not None:
            log.debug(f"lastrecord: {lastrecord.issue['number']} current: {request['issue']['number']}")
            if lastrecord.issue['number'] == request['issue']['number'] and lastrecord.sender['login'] == \
                    request['sender']['login']:
                if (time.time() - lastrecord.timestamp) < 300:
                    log.info("Suppressing comment by same user on same GitHub issue within 300s.")
                    return
        message = (f"\x0314 {request['sender']['login']} \x03{request['action']} comment on issue #"
                   f"{request['issue']['number']}: \"{demarkdown(request['comment']['body'])}\" in \x0306"
                   f"{request['repository']['name']}\x03. \x02\x0311{request['comment']['html_url']}\x02\x03")
        gitrecord = githubmodels.GitHubMessage(action=request['action'] or None, timestamp=timestamp,
                                               number=request['issue']['number'] or None,
                                               issue=request['issue'] or None, comment=request['comment'] or None,
                                               repository=request['repository'] or None, organization='NA',
                                               sender=request['sender'], pull_request=None,
                                               changes=None)

    elif event == 'pull_request':
        gitrecord = githubmodels.GitHubMessage(action=request['action'] or None, timestamp=timestamp,
                                               number=None,
                                               issue=None, comment=None,
                                               repository=request['repository'] or None, organization='NA',
                                               sender=request['sender'], pull_request=request['pull_request'] or None,
                                               changes=None)
        if 'id' in request['pull_request']['head']['repo'] and request['pull_request']['head'][
                'repo']['id'] == request['repository']['id']:
            headref = request['pull_request']['head']['ref']
        else:
            headref = request['pull_request']['head']['label']
        if request['action'] == 'review_requested':
            message = (f"\x0314 {request['sender']['login']} \x03requested a review from\x0314 "
                       f"{', '.join(x['login'] for x in request['pull_request']['requested_reviewers'])}"
                       f" \x03of pull request #{str(request['number'])}: "
                       f"\"{demarkdown(request['pull_request']['title'])}\""
                       f" from \x0306{headref}\x03 to \x0306 {request['pull_request']['base']['ref']}"
                       f"\x03 in \x0306{request['repository']['name']}\x03. \x02\x0311"
                       f"{request['pull_request']['html_url']}\x02\x03")
        else:
            message = (f"\x0314 {request['sender']['login']} \x03"
                       f"{'merged' if request['pull_request']['merged'] else request['action']}"
                       f" pull request #{str(request['number'])}: "
                       f"\"{demarkdown(request['pull_request']['title'])}"
                       f"\" from \x0306{headref}\x03 to \x0306{request['pull_request']['base']['ref']}"
                       f"\x03 in \x0306{request['repository']['name']}\x03. \x02\x0311" 
                       f"{request['pull_request']['html_url']}\x02\x03")
    elif event == 'pull_request_review':
        log.debug("pull request review event:")
        gitrecord = githubmodels.GitHubMessage(action=request['action'] or None, timestamp=timestamp,
                                               number=None, issue=None, comment=None,
                                               repository=request['repository'] or None,
                                               organization='NA',
                                               sender=request['sender'],
                                               pull_request=request['pull_request'] or None,
                                               changes=None)
        if request['action'] == "commented":
            log.info("Probable duplicate review comment event ignored.")
            return

        if request['action'] == "submitted":
            log.debug("Review Submitted")
            action = request['review']['state']
        else:
            log.debug(f"Review action: {request['action']}")
            action = request['action']

        message = (f"\x0314 {request['sender']['login']} \x03{action}\x03 review of\x0314" 
                   f" {request['pull_request']['user']['login']} \x03's pull request #"
                   f"{str(request['pull_request']['number'])}: "
                   f"\"{demarkdown(request['review']['body'] or '')}\" "
                   f"in \x0306{request['repository']['name']}\x03. "
                   f"\x02\x0311{request['review']['html_url']}\x02\x03")
        log.debug(f"Raw message: {message}")
    elif event == 'pull_request_review_comment':
        if request['comment']['user']['login'] == "houndci-bot":
            message = (f"Style errors found on pull request #{str(request['pull_request']['number'])}: \""
                       f"{request['pull_request']['title']}\" in \x0306{request['repository']['name']}")
        else:
            lastrecord = prequest.dbsession.query(githubmodels.GitHubMessage).order_by(
                githubmodels.GitHubMessage.id.desc()).first()
            if lastrecord.pull_request is not None:
                log.debug(f"lastrecord: {lastrecord.pull_request['number']} "
                         f"current: {request['pull_request']['number']}")
                if lastrecord.pull_request['number'] == request['pull_request']['number'] and \
                        lastrecord.sender['login'] == request['sender']['login']:
                    if (time.time() - lastrecord.timestamp) < 300:
                        log.info("Suppressing comment on same as last GitHub message.")
                        return
            log.debug(f"GitHub review comment/commit comment body: {prequest.json_body}")
            message = (f"\x0314 {request['sender']['login']} \x03{request['action']} comment " 
                       f"on pull request #{str(request['pull_request']['number'])}: "
                       f"\"{demarkdown(request['comment']['body'])}\" "
                       f"in \x0306{request['repository']['name']}\x03. "
                       f"\x02\x0311{request['comment']['html_url']}\x02\x03")
    elif event == 'push':
        if not request['commits']:
            domessage = False
            message = "Empty commit event ignored"
        elif len(request['commits']) == 1:
            message = (f"\x0314 {request['sender']['login']} \x03pushed "
                       f"{request['commits'][0]['id'][:7]}: \"" 
                       f"{request['commits'][0]['message']}\" to "
                       f"\x0306{request['repository']['name']}/"
                       f"{request['ref'].split('/')[-1]}\x03. \x02\x0311{request['compare']}\x02\x03")
        else:
            message = (f"\x0314 {request['sender']['login']} \x03pushed {str(len(request['commits']))} "
                       f"commits to \x0306" 
                       f"{request['repository']['name']}/{request['ref'].split('/')[-1]}\x03. \x02\x0311"
                       f"{request['compare']}\x02\x03")
        gitrecord = githubmodels.GitHubMessage(action=None, timestamp=timestamp,
                                               number=None,
                                               issue=None, comment=None,
                                               repository=request['repository'] or None, organization='NA',
                                               sender=request['sender'], pull_request=None,
                                               changes=request['commits'])
    elif event == 'commit_comment':
        message = (f"\x0314 {request['sender']['login']} \x03commented on commit"
                   f" \"{request['comment']['commit_id'][:7]}"
                   f"\" to \x0306{request['repository']['name']}\x03. "
                   f"\x02\x0311{request['comment']['html_url']}\x02\x03")
        gitrecord = githubmodels.GitHubMessage(action=None, timestamp=timestamp,
                                               number=None,
                                               issue=None, comment=request['comment'] or None,
                                               repository=request['repository'] or None, organization='NA',
                                               sender=request['sender'], pull_request=None,
                                               changes=None)
    elif event == 'create':
        if request['ref_type'] in {'tag', 'branch'}:
            message = (f"\x0314 {request['sender']['login']} \x03created "
                       f"{request['ref_type']} \"{request['ref']}\""
                       f" in \x0306{request['repository']['name']} \x03.")
            gitrecord = None
        else:
            log.debug(f"Unhandled create ref: {request['ref_type']}")
            devsay(f"An unhandled create ref was passed to GitHub: "
                   f"{request['ref_type']}. Absolver should implement!")
            return
    elif event == 'status':
        log.info("Ignored github status event")
        return
    elif event == 'release':
        message = (f"\x0314New release\x03 \x0311{request['name']}\x03 from {request['repository']} by\x0314 "
                   f"{request['sender']} \x03(\x02\x0311{request['url']}\x03)")
    else:
        log.debug(f"GitHub unhandled event: {event}")
        jsondump(request)
        devsay(f"An unhandled GitHub event was passed: {event}. Absolver should implement!")
        return
    msgshort = {"time": time.time(), "type": event, "key": "GitHub", "full": message}
    if gitrecord is not None:
        prequest.dbsession.add(gitrecord)
        timeout = time.time() - 3600
        oldrecords = prequest.dbsession.query(githubmodels.GitHubMessage).\
            filter(githubmodels.GitHubMessage.timestamp < timeout)
        if oldrecords.count() > 0:
            log.info(f"Deleted {oldrecords.count()} old GitHub messages.")
            prequest.dbsession.query(githubmodels.GitHubMessage).\
                filter(githubmodels.GitHubMessage.timestamp < timeout).delete()
    if lastmessage['full'] == message:
        log.info("Duplicate message, skipping:")
        log.info(message)
    else:
        if domessage:
            if request['sender']['login'] == "dependabot[bot]" and event != "pull_request":
                log.info("Discarding Dependabot message.")
                return
            for channel in channels:
                send(channel, f"[\x0315GitHub\x03] {message}", msgshort)
