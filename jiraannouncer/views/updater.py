from pyramid.view import view_config


@view_config(route_name='updater', renderer="json")
def updater(request):
    """Handle updates to OS files through github pulls."""
    # subprocess.call()
