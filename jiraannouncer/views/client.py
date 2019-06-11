import time

from pyramid.view import view_config

from ..models import faillog
from ..utils import logprint, send


@view_config(route_name='client', renderer="json")
def client(request):
    """Handle Client arrival announcements."""
    referer = request.headers['Referer'] if 'referer' in request.headers else None

    if referer != "https://clients.fuelrats.com:7778/":
        logprint(f"Client announcer called with invalid referer: {referer}")
        return
    try:
        cmdrname = request.params['cmdrname']
        system = request.params['system']
        platform = request.params['platform']
        o2status = request.params['EO2']
    except NameError:
        logprint("Missing parameters to Client announcement call.")
        model = faillog.FailLog(timestamp=time.time(), headers=request.headers, endpoint="client", body=request.body)

        query = request.dbsession.query(faillog.FailLog)

    if 'extradata' not in request.params:
        message = f"Incoming Client: {cmdrname} - System: {system} - Platform: {platform} - O2: {o2status}"
    else:
        extradata = request.params['extradata']
        message = f"Incoming Client: {cmdrname} - System: {system} - Platform: {platform} - O2: {o2status} - {extradata}"

    send("#fuelrats", message, "No Short for you!")
    return
