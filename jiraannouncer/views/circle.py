import time

import simplejson
from pyramid.view import view_config

from ..utils import logprint, jsondump, send, getlast

OFFSET = 5


@view_config(route_name='circle', renderer="json")
def circle(request):
    """Handle CircleCI events"""
    lastmessage = getlast()
    try:
        data = simplejson.loads(request.body)['payload']
    except simplejson.errors.JSONDecodeError:
        logprint("Failed to decode JSON from Circle. Dump:")
        logprint(request.body)
        return
    if 'reponame' not in data:
        logprint("No repository name in request!")
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

    if 'compare' not in data:
        if len(data['all_commit_details']) > 0:
            compareurl = data['all_commit_details'][0]['commit_url']
        elif len(data['pull_requests']) > 0:
            compareurl = data['pull_requests'][0]['url']
        else:
            compareurl = "\x0302null\x0a3"
    else:
        compareurl = data['compare']
    message1 = f"""
                [\x0315CircleCI\x03] \x0306 {data['reponame'] or ''}/{data['reponame'] or ''}
                 \x03#{data['build_num'] or ''} (\x0306{data['branch'] or ''}\x03 -  
                 {data['vcs_revision'][:7] or ''} : \x0314 {data['user']['login'] or ''}
                 \x03: {data['outcome'] or ''}
                """
    message2 = f"""
                [\x0315CircleCI\x03] Change view: \x02\x0311{compareurl}
                \x02\x03 Build details: \x02\x0311 {data['build_url'] or ''}\x02\x03    
                """

    msgshort1 = {"time": time.time(), "type": "Circle", "key": data['reponame'], "full": message1}
    msgshort2 = {"time": time.time(), "type": "Circle", "key": data['reponame'], "full": message2}
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
