import time
import hmac

from pyramid.view import view_config
from sys import hexversion

from ..models import faillog
from ..utils import logprint, send, devsay


@view_config(route_name='client', renderer="json")
def client(request):
    """Handle Client arrival announcements."""
    referer = request.headers['Referer'] if 'referer' in request.headers else None
    possiblefake = False

    if 'X-Client-Signature' in request.headers:
        settings = request.registry.settings
        client_secret = settings['client_secret'] if 'client_secret' in settings else None
        header_signature = request.headers['X-Client-Signature']
        logprint(f"HMAC signature was passed by referrer.")
        sha_name, signature = header_signature.split('=')
        if sha_name != 'sha1':
            logprint("Signature not in SHA1 format, aborting.")
            return

        mac = hmac.new(bytes(client_secret, 'utf8'), msg=request.body, digestmod='sha1')
        if hexversion >= 0x020707F0:
            if not hmac.compare_digest(str(mac.hexdigest()), str(signature)):
                logprint("Signature mismatch, possible fake call!")
                possiblefake = True
        else:
            if not str(mac.hexdigest()) == str(signature):
                logprint("Signature mismatch! GitHub event not parsed.")
                logprint(f"{mac.hexdigest()} vs {str(signature)}")
                devsay(f"Invalid MAC in Client message: {str(signature)}")
                possiblefake = True
    elif referer != "https://clients.fuelrats.com:7778/":
        logprint(f"Client announcer called with invalid referer: {referer}")
        devsay(f"Someone tried to call the client announcer with an invalid referer '{referer}'! Absolver!")
        possiblefake = True
    else:
        logprint("Non-signed request from valid referer.")
    try:
        cmdrname = request.params['cmdrname']
        system = request.params['system']
        platform = request.params['platform']
        o2status = request.params['EO2']
    except NameError:
        logprint("Missing parameters to Client announcement call.")
        devsay("Parameters were missing in a Client announcement call!")

    if 'extradata' not in request.params:
        message = f"Incoming Client: {cmdrname} - System: {system} - Platform: {platform} - O2: {o2status}"
    else:
        extradata = request.params['extradata']
        message = f"Incoming Client: {cmdrname} - System: {system} - Platform: {platform} - O2: {o2status} - {extradata}"

    send("#fuelrats", message, "No Short for you!")
    if possiblefake:
        send("#ratchat", f"[Client Announcer] Warning! The arriving case is not passing validation information!","")
    return
