import time
import urllib

import simplejson
from pyramid.view import view_config

from ..utils import send, getlast, devsay
import logging

log = logging.getLogger(__name__)
OFFSET = 5


@view_config(route_name='travis', renderer="json")
def travis(request):
    """Handle TravisCI events"""
    lastmessage = getlast()
    data = request.body.decode('utf-8')
    repo = request.headers['Travis-Repo-Slug']
    if not data.startswith("payload="):
        log.error("Error in Travis input, expected \"payload=\"")
        return
    try:
        request = simplejson.loads(urllib.parse.unquote(data[8:]))
    except simplejson.errors.JSONDecodeError:
        log.error(f"Error loading Travis payload: {data}")
        devsay("Travis couldn't decode a payload! Absolver, check the log.", request)
        return

    if "FuelRats/pipsqueak3" in repo:
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
        log.warn("Duplicate message, skipping:")
        log.debug(message1)
        log.debug(message2)
    else:
        for channel in channels:
            send(channel, message1, msgshort1, request)
        time.sleep(0.5)
        for channel in channels:
            send(channel, message2, msgshort2, request)
