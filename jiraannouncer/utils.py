import base64
import logging
import graypy
import pickle
import re
import sys
import time
import requests
from .models.usagelog import UsageLog
from pyramid import threadlocal

logging.basicConfig(filename='webhook.log', level=logging.DEBUG)
graylogger = logging.getLogger('gray_logger')
graylogger.setLevel(logging.DEBUG)

handler = graypy.GELFUDPHandler('5.9.19.231', 5090)
graylogger.addHandler(handler)

log = logging.getLogger(__name__)
registry = threadlocal.get_current_registry()


def from_hex(mystr):
    print(mystr)
    try:
        return bytes.fromhex(mystr).decode('utf-8')
    except TypeError:
        return "Unregistered Carrier"
    except ValueError:
        return "Unregistered Carrier"


def logprint(string):
    """Convert input to string, and print to log, ignoring non-ascii characters."""
    logging.debug(str(string).encode('ascii', 'ignore').decode())
    graylogger.debug(str(string).encode('ascii', 'ignore').decode())


def devsay(string, request):
    """Sends a message to the Announcer dev channel for debugging/reporting purposes."""
    send("#announcerdev", string, '', request)


def jsondump(string):
    """Convert input to string, and dump to jsondump file, ignoring non-ascii characters."""
    with open("jsondump.log", "a") as dumpfile:
        dumpfile.write(time.strftime("[%H:%M:%S]", time.gmtime()) + ":\n")
        dumpfile.write(str(string).encode('ascii', 'ignore').decode() + "\n\n")


def demarkdown(string):
    """Remove markdown features from and limit length of messages"""
    string = re.sub('>.*(\n|$)', '', string).replace('`', '').replace('#', '')
    string = re.sub('\n.*', '', string)
    string = re.sub('&gt;', '>', string)
    return string[:300] + ('...' if len(string) > 300 else '')


def send(channel, message, msgshort, request):
    """Send resulting message to IRC via Anope JSON-RPC (BotServ SAY)."""
    message = message.replace('\n', ' ').replace('\r', '')
    print(f"Host: {request.host} host URL: {request.host_url}")
    if '.dev' in request.host:
        serverurl = request.registry.settings['rpc_devproxy']
        token = request.registry.settings['rpc_devtoken']
    else:
        serverurl = request.registry.settings['rpc_proxy']
        token = request.registry.settings['rpc_token']
    print(f"Proxy: {serverurl}")
    # Anope 2.1 expects the raw token base64-encoded in a Bearer header.
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + base64.b64encode(token.encode()).decode(),
    }
    try:
        messagesplit = [message[i:i + 475]
                        for i in range(0, len(message), 475)]
        for msgpart in messagesplit:
            log.debug(f"Sending to {channel}...")
            payload = {
                'jsonrpc': '2.0',
                'method': 'anope.command',
                'params': ['ABish', 'BotServ', f'say {channel} {msgpart}'],
                'id': 1,
            }
            response = requests.post(serverurl, json=payload, headers=headers,
                                     timeout=10)
            response.raise_for_status()
            log.debug(response.text)
            result = response.json()
            if result.get('error'):
                log.critical("ERROR" + str(result['error']))
            time.sleep(0.5)
        pickle.dump(msgshort, open("lastmessage.p", "wb"))
    except requests.RequestException as err:
        log.critical("ERROR" + str(err))
    except Exception:
        log.critical("Error sending message")
        log.critical(sys.exc_info())
        return


def getlast():
    try:
        lastmessage = pickle.load(open("lastmessage.p", "rb"))
        log.info("Pickle loaded")
        if not all(key in lastmessage for key in ('type', 'key', 'time', 'full')):
            log.warn("Error loading pickle (Missing key)")
            lastmessage = {'type': " ", 'key': " ", 'time': 0, 'full': " "}
    except pickle.UnpicklingError:
        log.error("Error loading pickle (Exception)")
        lastmessage = {'type': " ", 'key': " ", 'time': 0, 'full': " "}
    return lastmessage


def logusage(request):
    logrecord = UsageLog(timestamp=int(time.time()), caller_ip=request.headers['X-Forwarded-For'],
                         endpoint=request.path_url, body=request.body)
    request.dbsession.add(logrecord)
