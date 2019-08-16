import hmac

from pyramid.view import view_config
from sys import hexversion

from ..utils import send, devsay
import logging
from prometheus_client import Counter


log = logging.getLogger(__name__)
announcer_client_requests = Counter('announcer_client_requests', 'Cumulative calls to Client announcer')
announcer_client_unsigned = Counter('announcer_client_unsigned', 'Unsigned calls to Client announcer')
announcer_client_noref = Counter('announcer_client_noref', 'Unsigned calls with no or invalid referer')
announcer_client_signed = Counter('announcer_client_signed', 'Signed calls to Client announcer')
announcer_client_signfail = Counter('announcer_client_failed', 'Calls to announcer failing HMAC check')


@view_config(route_name='client', renderer="json")
def client(request):
    """Handle Client arrival announcements."""
    referer = request.headers['Referer'] if 'referer' in request.headers else None
    possiblefake = False
    announcer_client_requests.inc()

    if 'X-Client-Signature' in request.headers:
        settings = request.registry.settings
        client_secret = settings['client_secret'] if 'client_secret' in settings else None
        header_signature = request.headers['X-Client-Signature']
        log.debug("HMAC signature was passed by referrer.")
        sha_name, signature = header_signature.split('=')
        if sha_name != 'sha1':
            log.error("Signature not in SHA1 format, aborting.")
            possiblefake = True

        mac = hmac.new(bytes(client_secret, 'utf8'), msg=request.body, digestmod='sha1')
        if hexversion >= 0x020707F0:
            if not hmac.compare_digest(str(mac.hexdigest()), str(signature)):
                log.error("Signature mismatch, possible fake call!")
                announcer_client_signfail.inc()
                possiblefake = True
        else:
            if not str(mac.hexdigest()) == str(signature):
                log.error("Signature mismatch! GitHub event not parsed.")
                log.error(f"{mac.hexdigest()} vs {str(signature)}")
                devsay(f"Invalid MAC in Client message: {str(signature)}", request)
                possiblefake = True
                announcer_client_signfail.inc()
    elif referer != "https://clients.fuelrats.com:7778/":
        log.error(f"Client announcer called with invalid referer: {referer}")
        devsay(f"Someone tried to call the client announcer with an invalid referer '{referer}'! Absolver!",
               request)
        possiblefake = True
        announcer_client_noref.inc()
    else:
        log.warn("Non-signed request from valid referer.")
        announcer_client_unsigned.inc()
    try:
        cmdrname = request.params['cmdrname']
        system = request.params['system']
        platform = request.params['platform']
        o2status = request.params['EO2']
    except NameError:
        log.critical("Missing parameters to Client announcement call.")
        devsay("Parameters were missing in a Client announcement call!", request)

    if 'extradata' not in request.params:
        message = f"Incoming Client: {cmdrname} - System: {system} - Platform: {platform} - O2: {o2status}"
    else:
        extradata = request.params['extradata']
        message = f"Incoming Client: {cmdrname} - System: {system} - Platform: {platform} - O2: {o2status} - {extradata}"

    send("#fuelrats", message, "No Short for you!", request)
    if possiblefake:
        send("#ratchat",
             f"[Client Announcer] Warning! The arriving case is not passing validation information!",
             "", request)
    return
