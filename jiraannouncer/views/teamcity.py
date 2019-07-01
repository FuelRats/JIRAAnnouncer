import simplejson
import time

from pyramid.view import view_config

from ..utils import logprint, jsondump, send, getlast, demarkdown, devsay


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
    message = f"[TeamCity] {build['projectName']} - {build['notifyType']}: {build['text']}"
    send("#rattech", message, '')
    return
