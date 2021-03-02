import hmac

import requests
from pyramid.view import view_config
from sys import hexversion

from ..utils import send, devsay
import logging

log = logging.getLogger(__name__)


@view_config(route_name='client', renderer="json")
def client(request):
    """Handle Client arrival announcements."""
    referer = request.headers['Referer'] if 'referer' in request.headers else None
    possiblefake = False

    if 'X-Client-Signature' in request.headers:
        settings = request.registry.settings
        client_secret = settings['client_secret'] if 'client_secret' in settings else None
        fr_token = settings['fr_token'] if 'fr_token' in settings else None
        api_url = settings['fr_url'] if 'fr_url' in settings else None
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
                possiblefake = True
        else:
            if not str(mac.hexdigest()) == str(signature):
                log.error("Signature mismatch! GitHub event not parsed.")
                log.error(f"{mac.hexdigest()} vs {str(signature)}")
                devsay(f"Invalid MAC in Client message: {str(signature)}", request)
                possiblefake = True
    elif referer != "https://clients.fuelrats.com:7778/":
        log.error(f"Client announcer called with invalid referer: {referer}")
        browser = request.user_agent
        if 'iPhone' in browser or 'Android' in browser:
            # Client is using an iPhone/iPad that does not forward referrer.
            send('#ratchat', f"[Client Announcer] Warning! The incoming client is using a phone or tablet device that"
                             f" does not preserve connections if switching apps/sleeping!", "", request)
        elif 'PlayStation 4' in browser or 'PLAYSTATION' in browser:
            send('#ratchat', f"[Client Announcer] Warning! The incoming client is using a known BROKEN browser that"
                             f" will not let them send to chat channels!", "", request)
        else:
            possiblefake = True
            devsay(f"Someone tried to call the client announcer with an invalid referer '{referer}'! Absolver!",
                   request)

    else:
        log.warn("Non-signed request from valid referer.")
    try:
        cmdrname = request.params['cmdrname']
        system = request.params['system']
        platform = request.params['platform']
        o2status = request.params['EO2']
    except NameError:
        log.critical("Missing parameters to Client announcement call.")
        devsay("Parameters were missing in a Client announcement call!", request)
    if system == "" or platform == "" or o2status == "":
        send("#ratchat", f"[Client Announcer] Client {cmdrname} has connected through the rescue page,"
                         f" but has not submitted system information! No automated r@tsignal sent!")
        log.warn(f"Client {cmdrname} connected with an empty required field. System: {system}"
                 f" Platform: {platform} o2status: {o2status}")
        return
    if system.lower() in ["sabiyhan"]:
        send("#ratchat", f"[Client Announcer] ALERT! Arriving client {cmdrname} submitted a system name known"
                         f" to cause a game client crash. Proceed with caution!")
        log.warn(f"Client {cmdrname} used blocked system name {system} in an attempt to crash game clients.")
    if 'extradata' not in request.params:
        message = f"Incoming Client: {cmdrname} - System: {system} - Platform: {platform} - O2: {o2status}"
    else:
        extradata = request.params['extradata']
        message = f"Incoming Client: {cmdrname} - System: {system} - Platform: {platform} - O2: {o2status} - {extradata}"
    rescues = requests.get(f'{api_url}/rescues?filter[status]=open', headers={'Accept': 'application/json',
                                                                               'Authorization':
                                                                                   f'Bearer:{fr_token}'}).json()
    active_cases = []
    try:
        for rescue in rescues['data']:
            active_cases.append(rescue['attributes']['clientNick'])
        if cmdrname in active_cases:
            log.warn(f"Suppressing active case announcement for client {cmdrname}")
        else:
            send("#fuelrats", message, "No Short for you!", request)
            if possiblefake:
                send("#ratchat",
                     f"[Client Announcer] Warning! The arriving case is not passing validation information!",
                     "", request)
    except:
        print("Failed to parse rescue data, not attempting to suppress repeat cases.")
        send("#fuelrats", message, "No Short for you!", request)
        if possiblefake:
            send("#ratchat",
                 f"[Client Announcer] Warning! The arriving case is not passing validation information!",
                 "", request)
    return
