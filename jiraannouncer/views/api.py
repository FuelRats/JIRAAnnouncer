import hmac
from sys import hexversion

from pyramid.view import view_config

from ..utils import send, devsay
import logging

log = logging.getLogger(__name__)


@view_config(route_name='api', renderer="json")
def api(request):
    """Handle custom channel requests from the API."""
    settings = request.registry.settings
    api_secret = settings['api_secret'] if 'api_secret' in settings else None

    header_signature = request.headers['X-Api-Signature']
    if header_signature is None:
        log.error("No signature sent by API, aborting message")
        devsay("No signature sent by API for botserv message!", request)
    sha_name, signature = header_signature.split('=')
    if sha_name != 'sha1':
        log.error(f"Invalid signature format in API message, was {sha_name}")

    mac = hmac.new(bytes(api_secret, 'utf8'), msg=request.body, digestmod='sha1')

    if hexversion >= 0x020707F0:
        if not hmac.compare_digest(str(mac.hexdigest()), str(signature)):
            log.critical("Signature mismatch, API event ignored!")
    else:
        if not str(mac.hexdigest()) == str(signature):
            log.critical("Signature mismatch! API event ignored.")
            log.critical(f"{mac.hexdigest()} vs {str(signature)}")
            devsay(f"Invalid MAC in API message: {str(signature)}", request)

    try:
        data = request.jsonbody
        channel = data['channel']
        if not channel:
            log.error("No channel specified in API message, aborting.")
            return
        send(channel, data['message'], "", request)
    except:
        log.critical("Well, something done fucked up, exception in body parsing/sending.")
