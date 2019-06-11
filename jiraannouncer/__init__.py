from pyramid.config import Configurator


# from pyramid_scheduler import Scheduler


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('pyramid_jinja2')
    config.include('.models')
    config.include('.routes')
    # config.include('pyramid_scheduler')
    config.scan()
    return config.make_wsgi_app()

# def webhook_updates(reason=None):
# ...gets executed every 10 minutes with an optional reason...


# def handle_request_often(request):
#    request.registry.scheduler.add_date_job(webhook_updates, minutes=1)
