from pyramid.response import Response
from pyramid.view import view_config
import colander
from deform import Form, ValidationFailure


class Drill(colander.MappingSchema):
    clientname = colander.SchemaNode(colander.String())
    system = colander.SchemaNode(colander.String())
    platform = colander.SchemaNode(colander.String(), validator=colander.OneOf('PC', 'PS', 'XB'))
    overseer = colander.SchemaNode(colander.String())


@view_config(route_name='drill', renderer='../templates/mytemplate.jinja2')
def my_view(request):
    schema = Drill()
    drillform = Form(schema, buttons=('submit',))

    if 'submit' in request.POST:
        controls = request.POST.items()

        try:
            appstruct = drillform.validate(controls)
        except ValidationFailure as e:
            return {'form': e.render()}
    else:
        try:
            schema = Drill()
            drillform = Form(schema, buttons=('submit',))
            drillform.render()
        except:
            return
