import simplejson
from pyramid.view import view_config

from ..utils import send
import logging

log = logging.getLogger(__name__)
prefixOptions = {
    'none': "\x0303",
    'major': "\x02\x0304",
    'maintenance': "\x02\x0307",
    'minor': "\x02\x0307"
}
suffixOptions = {
    'none': "\x03",
    'major': "\x03\x02",
    'maintenance': "\x03\x02",
    'minor': "\x03\x02"
}
statusOptions = {
    'completed': "(\x0303Completed\x03)",
    'scheduled': "(\x0307Scheduled\x03)",
    'in_progress': "(\x0308In progress\x03)",
    'verifying': "(\x0311Verifying\x03)",
    'investigating': "(\x0313Investigating\x03)",
    'identified': "(\x0306Identified\x03)",
    'monitoring': "(\x0315Monitoring\x03)",
    'resolved': "(\x0303Resolved\x03)"
}
componentOptions = {
    'degraded_performance': "Degraded performance",
    'major_outage': "Major outage",
    'operational': "Operational",
    'under_maintenance': "Under maintenance",
    'partial_outage': "Partial outage"
}


@view_config(route_name='statuspage', renderer='json')
def statuspage(request):
    """Handle StatusPage updates"""
    if request.body is None:
        log.error("Empty StatusPage request received, aborting.")
        return
    shortlink = ""
    data = simplejson.loads(request.body)
    status_prefix = prefixOptions[data['page']['status_indicator']]
    status_suffix = suffixOptions[data['page']['status_indicator']]
    status_name = f"{status_prefix}{data['page']['status_description']}{status_suffix}"
    if 'incident' in data:
        shortlink = data['incident']['shortlink']
        message = (f"[{data['incident']['name'] or ''}] {data['incident']['incident_updates'][0]['body'][:64]}..."
                   f"{statusOptions[data['incident']['status']]} {data['incident']['scheduled_for'] or ''}"
                   f"{'-' if data['incident']['scheduled_for'] is not None else ''}"
                   f"{data['incident']['scheduled_until'] or ''}"
                   )
    elif data['component_update'] is not None:
        message = (f"[Component: {data['component']['name']}] went from "
                   f"{componentOptions[data['component_update']['old_status']] or ''} to "
                   f"{componentOptions[data['component_update']['new_status']] or ''}"
                   )
    else:
        message = "Something went horribly wrong in Statuspage processing."
    send("#ratchat", f"{status_name} {message} {shortlink or ''}", "No shorts today.")
    return
