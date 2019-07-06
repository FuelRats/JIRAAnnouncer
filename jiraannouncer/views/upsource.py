import simplejson

from pyramid.view import view_config

from ..utils import logprint, send, demarkdown, devsay


@view_config(route_name='upsource', renderer='json')
def upsource(request):
    """Handle UpSource webhooks."""
    message = ''
    if 'channel' in request.GET.keys():
        channel = f"#{request.GET.getone('channel')}"
        logprint(f"Targeting channel {channel}")
    else:
        channel = "#announcerdev"
    logprint(f"Raw UpSource data: {request.body}")
    try:
        jsonbody = simplejson.loads(request.body)
    except simplejson.JSONDecodeError:
        logprint("Error loading UpSource JSON data!")
        logprint(request.body)
        devsay(f"Error loading UpSource JSON data!")
        return
    event = jsonbody['dataType']
    if 'data' in jsonbody:
        data = jsonbody['data']
    else:
        data = {}
    if event == 'ReviewCreatedFeedEventBean':
        message = f"New review in {data['projectId']} {data['majorVersion']+'.' or ''}" \
            f"{data['minorVersion'] or ''} - {demarkdown(data['message'])} ({data['author']}"
    elif event == 'NewRevisionEventBean':
        message = f"New revision: {data['revisionId']} by {data['author']}: \"{demarkdown(data['message'])}\""
    else:
        logprint(f"Unhandled UpSource event: {event}")
    send(channel, message, '')
