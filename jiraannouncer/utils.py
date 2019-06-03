import re
import time
import pickle
import sys
import logging

from xmlrpc.client import ServerProxy, Error

logging.basicConfig(filename='webhook.log', level=logging.DEBUG)


def logprint(string):
    """Convert input to string, and print to log, ignoring non-ascii characters."""
    logging.debug(str(string).encode('ascii', 'ignore').decode())


def jsondump(string):
    """Convert input to string, and dump to jsondump file, ignoring non-ascii characters."""
    dumpfile = open("jsondump.log", "a")
    dumpfile.write(time.strftime("[%H:%M:%S]", time.gmtime()) + ":\n")
    dumpfile.write(str(string).encode('ascii', 'ignore').decode() + "\n")
    dumpfile.close()


def demarkdown(string):
    """Remove markdown features from and limit length of messages"""
    string = re.sub('>.*(\n|$)', '', string).replace('`', '').replace('#', '')
    string = re.sub('\n.*', '', string)
    return string[:300] + ('...' if len(string) > 300 else '')


def send(channel, message, msgshort):
    """Send resulting message to IRC over XMLRPC."""
    message = message.replace('\n', ' ').replace('\r', '')
    proxy = ServerProxy("https://irc.eu.fuelrats.com:6080/xmlrpc")
    try:
        messagesplit = [message[i:i + 475] for i in range(0, len(message), 475)]
        for msgpart in messagesplit:
            logprint(time.strftime("[%H:%M:%S]", time.gmtime()) + " Sending to " + channel + "...")
            logprint(proxy.command("botserv", "ABish", "say " + channel + " " + msgpart))
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
            logprint("Error loading pickle")
            lastmessage = {'type': " ", 'key': " ", 'time': 0, 'full': " "}
    except:
        logprint("Error loading pickle (Exception)")
        lastmessage = {'type': " ", 'key': " ", 'time': 0, 'full': " "}
    return lastmessage
