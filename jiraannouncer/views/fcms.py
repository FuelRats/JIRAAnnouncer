import time

from pyramid.view import view_config

from ..utils import send, devsay, from_hex
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
    carrier_name = from_hex(data['carrier_vanity_name'])
    target_system = data['calendar_arrivalSystem'] if 'calendar_arrivalSystem' in data else None
    departure_system = data['current_starsystem'] if 'current_starsystem' in data else None
    jump_time = data['calendar_start']

    if target_system is None and departure_system is None:
        log.info('Ignored FCMS webhook event')
        return

    if jump_time is None:
        message = f"[\x0315FCMS\x03] \x02{carrier_name} ({carrier})\x02 cancelled their scheduled jump"
    else:
        message = f"[\x0315FCMS\x03] \x02{carrier_name} ({carrier})\x02 is will travel from \x02{departure_system}\x02 to \x02{target_system}\x02 at \x02{jump_time}\x02"

    msgshort = {"time": time.time(), "type": "FCMS",
                "key": "FCMS", "full": message}

    send("#announcerdev", message, msgshort, request)

    return
