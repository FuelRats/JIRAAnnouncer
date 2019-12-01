from pyramid.view import view_config
import colander
from deform import Form, ValidationFailure, widget
from ..utils import send
import logging

log = logging.getLogger(__name__)


class DrillOutline(colander.MappingSchema):
    platforms = (('PC', 'PC'), ('XB', 'XBox'), ('PS', 'PS4'))
    channels = (('#drillrats', '#drillrats'), ('#drillrats2', '#drillrats2'),
                ('#drillrats3', '#drillrats3'))
    client_name = colander.SchemaNode(colander.String(),
                                      description="Damsel's CMDR name. (NOT the Drillee's name!)")
    system = colander.SchemaNode(colander.String(),
                                 widget=widget.AutocompleteInputWidget(
                                     values='https://system.api.fuelrats.com/search', min_length=3),
                                 description="Rescue system, i.e where the Damsel is located.")
    platform = colander.SchemaNode(colander.String(),
                                   widget=widget.SelectWidget(values=platforms),
                                   validator=colander.OneOf(('PC', 'XB', 'PS')),
                                   description="Which platform the damsel is on."
                                   )
    o2status = colander.SchemaNode(colander.String(),
                                   widget=widget.CheckboxWidget(true_val="Not OK",
                                                                false_val="OK"),
                                   description="Code Red cases should only be used in Dispatch drills.",
                                   title="Code Red?")
    channel = colander.SchemaNode(colander.String(),
                                  widget=widget.SelectWidget(values=channels),
                                  validator=colander.OneOf(('#drillrats', '#drillrats2', '#drillrats3')),
                                  description="Which channel to send the case to.")
    overseer = colander.SchemaNode(colander.String(),
                                   description="Who is overseeing the drill.")


@view_config(route_name='outliner', renderer='../templates/form.jinja2')
def my_view(request):
    return
