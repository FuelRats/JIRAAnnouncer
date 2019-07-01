import simplejson
import time

from pyramid.view import view_config

from ..utils import logprint, jsondump, send, getlast, demarkdown, devsay

notifyTypes = {
    'buildStarted': '\x0302Build Started\x03',
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
    message = ''
    logprint(f"TeamCity called!")
    try:
        jsonbody = simplejson.loads(request.body)
    except simplejson.JSONDecodeError:
        logprint("Error loading TeamCity JSON data!")
        return
    if 'build' in jsonbody:
        build = jsonbody['build']
    else:
        build = {}
        logprint("No buildinfo in TeamCity call!")
    notifytype = build['notifyType']

    message = f"\x0315[\x0306TeamCity\x0315]\x03 {build['projectName']} - " \
        f"{notifyTypes[notifytype]}: Build #\x0315{build['buildId']}\x03 " \
        f"{buildresults[build['buildResult']]} (\x0315{build['buildStatusUrl']}\x03)"
    send("#rattech", message, '')
    return
