from pyramid.config import Configurator


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.add_static_view('static', 'deform:static')
    config.add_static_view('pyramid-static', 'jiraannouncer:static')
    config.include('pyramid_jinja2')
    config.include('.models')
    config.include('.routes')
    config.include('pyramid_prometheus')
    config.scan()
    return config.make_wsgi_app()
