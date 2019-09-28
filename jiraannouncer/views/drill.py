from pyramid.httpexceptions import HTTPBadRequest
from pyramid.view import view_config
import colander
from deform import Form, ValidationFailure, widget
from ..utils import send
import logging

log = logging.getLogger(__name__)


class Drill(colander.MappingSchema):
    platforms = (('PC', 'PC'), ('XB', 'XBox'), ('PS', 'PS4'))
    channels = (('#drillrats', '#drillrats'), ('#drillrats2', '#drillrats2'),
                ('#drillrats3', '#drillrats3'))
    client_name = colander.SchemaNode(colander.String())
    system = colander.SchemaNode(colander.String(),
                                 widget=widget.AutocompleteInputWidget(
                                     values='https://system.api.fuelrats.com/search?xhr=True'))
    platform = colander.SchemaNode(colander.String(),
                                   widget=widget.SelectWidget(values=platforms),
                                   validator=colander.OneOf(('PC', 'XB', 'PS'))
                                   )
    channel = colander.SchemaNode(colander.String(),
                                  widget=widget.SelectWidget(values=channels),
                                  validator=colander.OneOf(('#drillrats', '#drillrats2', '#drillrats3')))
    overseer = colander.SchemaNode(colander.String())


@view_config(route_name='drill', renderer='../templates/form.jinja2')
def my_view(request):
    schema = Drill()
    drillform = Form(schema, buttons=('submit',))
    if 'submit' in request.POST:
        controls = request.POST.items()

        try:
            appstruct = drillform.validate(controls)
            cmdrname = appstruct.pop("client_name", "InvalidClient")
            system = appstruct.pop("system", "InvalidSystem")
            platform = appstruct.pop("platform", "InvalidPlatform")
            o2status = "OK"
            channel = appstruct.pop("channel", "InvalidChannel")
            overseer = appstruct.pop("overseer", "InvalidSeer")
            message = f"Incoming Client: {cmdrname} - System: {system} - Platform: {platform} - O2: {o2status} - Language: English (en-US)"
            send(channel, message, "No short for you!", request)
            logging.info(f"Client announcement for Overseer {overseer} made in {channel}. Client: {cmdrname}")
        except ValidationFailure as e:
            logging.error(f"Validation failed for a call to the drill client announcer!")
            return {'form': e.render()}
        return {'form': 'Completed!', 'appstruct': appstruct}
    else:
        rendered_form = drillform.render()
    return dict(form=rendered_form)
