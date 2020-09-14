import stripe
from pyramid.httpexceptions import HTTPError

from pyramid.view import view_config

from ..utils import send
import logging

log = logging.getLogger(__name__)


@view_config(route_name='stripe', renderer="json")
def mystripe(request):
    stripe.api_key = request.registry.settings['stripe_key']
    data = request.json_body
    try:
        event = stripe.Event.construct_from(data, stripe.api_key)
    except ValueError as e:
        print(f"Invalid payload: {e}")
        return HTTPError(detail='Invalid payload')
    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object
        decimalplace = len(str(payment_intent.amount))-2  # Fucking Stripe.
        send(f'#{request.registry.settings["stripe_channel"]}',
             f'[\x0315Stripe\x03] A donation of \x0315{str(payment_intent.amount)[:decimalplace]}.'
             f'{str(payment_intent.amount)[decimalplace:]}\x03 {payment_intent.currency.upper()} '
             f'was made.',
             'No!', request)
