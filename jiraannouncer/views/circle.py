import time

import simplejson
from pyramid.view import view_config

from ..utils import jsondump, send, getlast
import logging

log = logging.getLogger(__name__)
OFFSET = 5


@view_config(route_name='circle', renderer="json")
def circle(request):
    """Handle CircleCI events"""
    lastmessage = getlast()
    try:
        data = simplejson.loads(request.body)['payload']
    except simplejson.errors.JSONDecodeError:
        log.critical("Failed to decode JSON from Circle. Dump:")
        log.debug(request.body)
        return
    if 'reponame' not in data:
        log.warn("No repository name in request!")
        data['reponame'] = "Unset"
        channels = ['#rattech']
    else:
        if data['reponame'] == "pipsqueak3":
            if data['username'] == "FuelRats":
                channels = ['#mechadev']
            else:
                jsondump(data)
                return
        else:
            channels = ['#rattech']

    if 'compare' not in data or data['compare'] is None:
        log.debug(f"No compare URL in CircleCI data, dumping: {data}")
        if len(data['all_commit_details']) > 0:
            compareurl = data['all_commit_details'][0]['commit_url']
        elif len(data['pull_requests']) > 0:
            compareurl = data['pull_requests'][0]['url']
        else:
            compareurl = "\x0302null\x0a3"
    else:
        compareurl = data['compare']
        log.debug(f"Setting to data field compare: {data['compare']}")
        log.debug(f"Full dump: {data}")
    message1 = f"""
                [\x0315CircleCI\x03] \x0306 {data['reponame'] or ''}/{data['reponame'] or ''}
                 \x03#{data['build_num'] or ''} (\x0306{data['branch'] or ''}\x03 -  
                 {data['vcs_revision'][:7] or ''} : \x0314 {data['user']['login'] or ''}
                 \x03: {data['outcome'] or ''}
                """
    message2 = f"""
                [\x0315CircleCI\x03] Change view: \x02\x0311{compareurl or data['compare']}
                \x02\x03 Build details: \x02\x0311 {data['build_url'] or ''}\x02\x03    
                """

    msgshort1 = {"time": time.time(), "type": "Circle", "key": data['reponame'], "full": message1}
    msgshort2 = {"time": time.time(), "type": "Circle", "key": data['reponame'], "full": message2}
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
