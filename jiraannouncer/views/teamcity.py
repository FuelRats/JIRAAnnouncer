import simplejson
import time

from pyramid.view import view_config

from ..utils import logprint, jsondump, send, getlast, demarkdown, devsay

notifyTypes = {
    'buildStarted': '\x0311Build Started\x03',
    'buildInterrupted': '\x0307\x02Build Interrupted\x03\x02',
    'buildFinished': '\x0303Build Finished\x03'
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
        channel = request.GET.getone('channel')
        logprint(f"Targeting channel #{channel}")
    else:
        channel = "#rattech"
    logprint(f"TeamCity called!")
    try:
        jsonbody = request.json_body
    except:
        logprint("Error loading TeamCity JSON data!")
        return
    if 'build' in jsonbody:
        build = jsonbody['build']
    else:
        build = {}
        logprint("No buildinfo in TeamCity call!")
    notifytype = build['notifyType']

    message = f"\x0315[\x0306TeamCity\x0315]\x03 {build['projectName']} - " \
        f"{notifyTypes[notifytype]} on {build['agentName']}: Build #\x0315{build['buildId']}\x03 " \
        f"{buildresults[build['buildResult']]} (\x0315{build['buildStatusUrl']}\x03)"
    send(channel, message, '')
    if build['buildResultDelta'] == 'fixed':
        message = f"\0315[\x0306TeamCity\x0315]\x03 Yay! {build['projectName']} builds fixed!"
        send(channel, message, '')
    elif build['buildResultDelta'] == 'broken':
        message = f"\x0315[\x0306TeamCity\x0315]\x03 Alert! Builds for {build['projectName']}" \
            f" have started failing!"
        send(channel, message, '')
    return
