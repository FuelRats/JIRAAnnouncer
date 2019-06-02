import time
import simplejson
import urllib

from pyramid.view import view_config

from ..utils import logprint, send, getlast

OFFSET = 5


@view_config(route_name='travis', renderer="json")
def travis(request):
    """Handle TravisCI events"""
    lastmessage = getlast()
    data = request.body.decode('utf-8')
    repo = request.headers['Travis-Repo-Slug']
    if not data.startswith("payload="):
        logprint("Error in Travis input, expected \"payload=\"")
        return
    try:
        request = simplejson.loads(urllib.parse.unquote(data[8:]))
    except:
        logprint("Error loading Travis payload:")
        logprint(data)
        return

    if repo == "FuelRats/pipsqueak3":
        channels = ['#mechadev']
    else:
        channels = ['#rattech']
        message1 = ("[\x0315TravisCI\x03] \x0306" + repo + "\x03#" + request['number'] +
                    " (\x0306" + request['branch'] + "\x03 - " + request['commit'][:7] +
                    " : \x0314" + request['author_name'] + "\x03): " + request['result_message'])
        message2 = ("[\x0315TravisCI\x03] Change view: \x02\x0311" + request['compare_url'] +
                    "\x02\x03 Build details: \x02\x0311" + request['build_url'] + "\x02\x03")
        msgshort1 = {"time": time.time(), "type": "Travis", "key": repo, "full": message1}
        msgshort2 = {"time": time.time(), "type": "Travis", "key": repo, "full": message2}
        if lastmessage['full'] == message2:
            logprint("Duplicate message, skipping:")
            logprint(message1)
            logprint(message2)
        else:
            for channel in channels:
                send(channel, message1, msgshort1)
            time.sleep(0.5)
            for channel in channels:
                send(channel, message2, msgshort2)
