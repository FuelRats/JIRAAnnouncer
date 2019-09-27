from pyramid.response import Response
from pyramid.view import view_config
import colander
from deform import Form, ValidationFailure, widget


class Drill(colander.MappingSchema):
    clientname = colander.SchemaNode(colander.String())
    system = colander.SchemaNode(colander.String())
    platform = colander.SchemaNode(colander.String())
    overseer = colander.SchemaNode(colander.String())


@view_config(route_name='drill', renderer='../templates/form.jinja2')
def my_view(request):
    schema = Drill()
    drillform = Form(schema, buttons=('submit',))
    rendered_form = drillform.render()
    if 'submit' in request.POST:
        controls = request.POST.items()

        try:
            appstruct = drillform.validate(controls)
        except ValidationFailure as e:
            return {'form': e.render()}
        return {'form': None, 'appstruct': appstruct}
    else:
        try:
            schema = Drill()

        except:
            return
    return dict(form=rendered_form)
