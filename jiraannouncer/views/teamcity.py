import simplejson
import time

from pyramid.view import view_config

from ..utils import logprint, jsondump, send, getlast, demarkdown, devsay

notifyTypes = {
    'buildStarted': '\x0307Build Started\x03',
    'buildInterrupted': '\x03\x02Build Interrupted\x03',
    'buildFinished': '\x0303Build Finished\x03'
}
buildresults = {
    'running': '\x0308Running\x03',
    'failure': '\x02\x0304Failure\x03',
    'successful': '\x0303Successful\x03'
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
    message = f"\x0303[TeamCity]\x03 {build['projectName']} - {notifyTypes[build['notifyType']]}: {build['text']}"
    send("#rattech", message, '')
    return
