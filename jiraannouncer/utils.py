import logging
import graypy
import pickle
import re
import sys
import time
from xmlrpc.client import ServerProxy, Error
from .models.usagelog import UsageLog
from pyramid import threadlocal

logging.basicConfig(filename='webhook.log', level=logging.DEBUG)
graylogger = logging.getLogger('gray_logger')
graylogger.setLevel(logging.DEBUG)

handler = graypy.GELFUDPHandler('5.9.19.231', 5090)
graylogger.addHandler(handler)

log = logging.getLogger(__name__)
registry = threadlocal.get_current_registry()


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
    """Send resulting message to IRC over XMLRPC."""
    message = message.replace('\n', ' ').replace('\r', '')
    serverurl = request.registry.settings['xml_proxy']
    proxy = ServerProxy(serverurl)
    try:
        messagesplit = [message[i:i + 475] for i in range(0, len(message), 475)]
        for msgpart in messagesplit:
            log.debug(f"Sending to {channel}...")
            log.debug(proxy.command("botserv", "ABish", f"say {channel} {msgpart}"))
            time.sleep(0.5)
        pickle.dump(msgshort, open("lastmessage.p", "wb"))
    except Error as err:
        log.critical("ERROR" + str(err))
    except:
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
