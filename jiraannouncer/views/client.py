import time

from pyramid.view import view_config

from ..models import faillog
from ..utils import logprint, send, devsay


@view_config(route_name='client', renderer="json")
def client(request):
    """Handle Client arrival announcements."""
    referer = request.headers['Referer'] if 'referer' in request.headers else None

    if referer != "https://clients.fuelrats.com:7778/":
        logprint(f"Client announcer called with invalid referer: {referer}")
        devsay(f"Someone tried to call the client announcer with an invalid referer '{referer}'! Absolver!")
        possiblefake=True
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
