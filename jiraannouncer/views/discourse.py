import hmac
import time
import logging
from json import JSONDecodeError

from sys import hexversion

from pyramid.view import view_config

from ..utils import jsondump, send, devsay

log = logging.getLogger(__name__)


@view_config(route_name='discourse', renderer="json")
def discourse(prequest):
    """Handle Discourse events."""
    settings = prequest.registry.settings
    discourse_secret = settings['discourse_secret'] if 'discourse_secret' in settings else None
    data = prequest.body
    message = ""
    domessage = True

    if 'X-Discourse-Event-Signature' not in prequest.headers:
        log.error("Malformed request to Discourse webhook handler (Missing X-Discourse-Event-Signature)")
        devsay(
             "[\x0315Discourse\x03] Malformed request to Discourse webhook handler (Missing "
             "X-Discourse-Event-Signature header)",
             prequest)
        return {'error': 'MAC verification failed!'}

    if discourse_secret is not None:
        header_signature = prequest.headers['X-Discourse-Event-Signature']
        if header_signature is None:
            log.critical("No signature sent in Discourse event, aborting.")
            return {'error': 'MAC verification failed!'}
        sha_name, signature = header_signature.split('=')
        if sha_name != 'sha256':
            log.critical("Signature not in SHA256 format, aborting.")
            return {'error': 'MAC verification failed!'}
        mac = hmac.new(bytes(discourse_secret, 'utf8'), msg=prequest.body, digestmod='sha256')

        if hexversion >= 0x020707F0:
            if not hmac.compare_digest(str(mac.hexdigest()), str(signature)):
                log.critical("Signature mismatch, Discourse event not parsed!")
                return {'error': 'MAC verification failed!'}
        else:
            # Well, aren't you a special snowflake?
            if not str(mac.hexdigest()) == str(signature):
                log.critical("Signature mismatch! Discourse event not parsed.")
                log.debug(f"{mac.hexdigest()} vs {str(signature)}")
                devsay(f"Invalid MAC in Discourse message: {str(signature)}", prequest)
                return {'error': 'MAC verification failed!'}
    try:
        request = prequest.json_body
    except JSONDecodeError:
        log.error("Error loading Discourse payload:")
        log.debug(data)
        devsay("A Discourse payload failed to decode to JSON!", prequest)
        return {'error': 'Not a valid JSON payload!'}
    domessage = True

    if prequest.headers['X_DISCOURSE_EVENT'] != 'post_created':
        log.warning('Skipped non post created event from Discourse: '+prequest.headers['X_DISCOURSE_EVENT'])
    else:
        # TODO: Add channel directing for categories.
        message = (f"New post by \x0314{request['post']['username']}\x03 in [\x0314{request['post']['category_slug']}\x03]" 
                   f" '\x0303{request['post']['topic_title']}\x03' ("
                   f"https://discourse.fuelrats.com/t/{request['post']['topic_slug']}/"
                   f"{request['post']['topic_id']}/{request['post']['post_number']})")
        msgshort = {"time": time.time(), "type": "post", "key": "Discourse", "full": message}
        send('#rattech', f"[\x0313Discourse\x03] {message}", msgshort, prequest)
    return {}
