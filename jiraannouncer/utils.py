import logging
import graypy
import pickle
import re
import sys
import time
from xmlrpc.client import ServerProxy, Error
from .models.usagelog import UsageLog

logging.basicConfig(filename='webhook.log', level=logging.DEBUG)
graylogger = logging.getLogger('gray_logger')
graylogger.setLevel(logging.DEBUG)

handler = graypy.GELFUDPHandler('5.9.19.231', 5090)
graylogger.addHandler(handler)


def logprint(string):
    """Convert input to string, and print to log, ignoring non-ascii characters."""
    logging.debug(str(string).encode('ascii', 'ignore').decode())
    graylogger.debug(str(string).encode('ascii', 'ignore').decode())


def devsay(string):
    """Sends a message to the Announcer dev channel for debugging/reporting purposes."""
    send("#announcerdev", string, '')


def jsondump(string):
    """Convert input to string, and dump to jsondump file, ignoring non-ascii characters."""
    with open("jsondump.log", "a") as dumpfile:
        dumpfile.write(time.strftime("[%H:%M:%S]", time.gmtime()) + ":\n")
        dumpfile.write(str(string).encode('ascii', 'ignore').decode() + "\n\n")


def demarkdown(string):
    """Remove markdown features from and limit length of messages"""
    logprint(f"Demarkdown of string: {string}")
    string = re.sub('>.*(\n|$)', '', string).replace('`', '').replace('#', '')
    string = re.sub('\n.*', '', string)
    string = re.sub('&gt;', '>', string)
    return string[:300] + ('...' if len(string) > 300 else '')


def send(channel, message, msgshort):
    """Send resulting message to IRC over XMLRPC."""
    message = message.replace('\n', ' ').replace('\r', '')
    proxy = ServerProxy("https://irc.eu.fuelrats.com:6080/xmlrpc")
    try:
        messagesplit = [message[i:i + 475] for i in range(0, len(message), 475)]
        for msgpart in messagesplit:
            logprint(f"{time.strftime('[%H:%M:%S]', time.gmtime())} Sending to {channel}...")
            logprint(proxy.command("botserv", "ABish", f"say {channel} {msgpart}"))
            # logprint(msgpart)
            time.sleep(0.5)
        pickle.dump(msgshort, open("lastmessage.p", "wb"))
    except Error as err:
        logprint("ERROR" + str(err))
    except:
        logprint("Error sending message")
        logprint(sys.exc_info())
        return


def getlast():
    try:
        lastmessage = pickle.load(open("lastmessage.p", "rb"))
        logprint("Pickle loaded")
        if not all(key in lastmessage for key in ('type', 'key', 'time', 'full')):
            logprint("Error loading pickle (Missing key)")
            lastmessage = {'type': " ", 'key': " ", 'time': 0, 'full': " "}
    except pickle.UnpicklingError:
        logprint("Error loading pickle (Exception)")
        lastmessage = {'type': " ", 'key': " ", 'time': 0, 'full': " "}
    return lastmessage


def logusage(request):
    logrecord = UsageLog(timestamp=int(time.time()), caller_ip=request.headers['X-Forwarded-For'],
                         endpoint=request.path_url, body=request.body)
    request.dbsession.add(logrecord)
