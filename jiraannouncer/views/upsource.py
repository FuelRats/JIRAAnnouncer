import simplejson

from pyramid.view import view_config

from ..utils import send, demarkdown, devsay
import logging

log = logging.getLogger(__name__)


@view_config(route_name='upsource', renderer='json')
def upsource(request):
    """Handle UpSource webhooks."""
    message = ''
    if 'channel' in request.GET.keys():
        channel = f"#{request.GET.getone('channel')}"
        log.debug(f"Targeting channel {channel}")
    else:
        channel = "#announcerdev"
    log.debug(f"Raw UpSource data: {request.body}")
    try:
        jsonbody = simplejson.loads(request.body)
    except simplejson.JSONDecodeError:
        log.error("Error loading UpSource JSON data!")
        log.error(request.body)
        devsay(f"Error loading UpSource JSON data!", request)
        return
    event = jsonbody['dataType']
    if 'data' in jsonbody:
        data = jsonbody['data']
    else:
        data = {}
    if event == 'ReviewCreatedFeedEventBean':
        message = f"New review in {data['projectId']} {data['majorVersion']+'.' or ''}" \
            f"{data['minorVersion'] or ''} - {demarkdown(data['message'])} ({demarkdown(data['author'])}"
    elif event == 'NewRevisionEventBean':
        message = f"New revision: {data['revisionId']} by {demarkdown(data['author'])}:" \
            f" \"{demarkdown(data['message'])}\""
    else:
        log.warn(f"Unhandled UpSource event: {event}")
    send(channel, message, '', request)
