import hmac

from pyramid.view import view_config
from sys import hexversion

from ..utils import send, devsay
import logging

log = logging.getLogger(__name__)


@view_config(route_name='fcms', renderer="json")
def fcms(request):
    try:
        data = request.json_body
    except:
        log.error("Failed to decode JSON from body. Dump:")
        log.debug(request.body)
        devsay("A FCMS payload couldn't be decoded. NoLifeKing, check the logfile!",
               request)
        return

    carrier = data['carrier_callsign']
    target_system = data['calendar_arrivalSystem']
    departure_system = data['current_starsystem']
    jump_time = data['calendar_end'] if 'calendar_end' in data else None

    if jump_time is None:
        send(
            "#announcerdev",
            f"[FCMS] Carrier {carrier} cancelled their scheduled jump",
            "I don't use shorts",
            request
        )
    else:
        send(
            "#announcerdev",
            f"[FCMS] Carrier {carrier} is will travel from {departure_system} to {target_system} at {jump_time}",
            "I don't use shorts",
            request
        )

    return
