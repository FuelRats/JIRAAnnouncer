from pyramid.view import view_config

from ..utils import send
import logging

log = logging.getLogger(__name__)

notifyTypes = {
    'buildStarted': '\x0311Build Started\x03',
    'buildInterrupted': '\x0307\x02Build Interrupted\x03\x02',
    'buildFinished': '\x0303Build Finished\x03',
    'changesLoaded': '\x0311Changes Loaded\x03'
}
buildresults = {
    'running': '\x0308Running\x03',
    'failure': '\x02\x0304Failure\x03\x02',
    'success': '\x0303Success\x03'
}


@view_config(route_name='teamcity', renderer='json')
def teamcity(request):
    """Handle TeamCity CI webhooks."""
    if 'channel' in request.GET.keys():
        channel = f"#{request.GET.getone('channel')}"
        log.debug(f"Targeting channel {channel}")
    else:
        channel = "#rattech"
    log.debug(f"TeamCity called!")
    try:
        jsonbody = request.json_body
    except:
        log.error("Error loading TeamCity JSON data!")
        return
    if 'build' in jsonbody:
        build = jsonbody['build']
    else:
        build = {}
        log.warn("No buildinfo in TeamCity call!")
    notifytype = build['notifyType']
    if 'buildType' in build['extraParameters']:
        if build['extraParameters']['buildType'] == 'deployment':
            message = f"\x0315[\x0306TeamCity\x0315]\x03 {build['projectName']} - " \
                        f"deploying from {build['agentName']}"
            send(channel, message, '', request)
    message = f"\x0315[\x0306TeamCity\x0315]\x03 {build['projectName']} - " \
        f"{notifyTypes[notifytype]} on {build['agentName']}: Build #\x0315{build['buildId']}\x03 " \
        f"{buildresults[build['buildResult']]} (\x0315{build['buildStatusUrl']}\x03)"
    send(channel, message, '', request)
    if build['buildResultDelta'] == 'fixed':
        message = f"\x0315[\x0306TeamCity\x0315]\x03 Yay! {build['projectName']} builds fixed!"
        send(channel, message, '', request)
    elif build['buildResultDelta'] == 'broken':
        message = f"\x0315[\x0306TeamCity\x0315]\x03 Alert! Builds for {build['projectName']}" \
            f" have started failing!"
        send(channel, message, '', request)
    return
