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
        amount = float(f'{str(payment_intent.amount)[:decimalplace]}.{str(payment_intent.amount)[decimalplace:]}')
        if payment_intent.metadata.get('id_cart'):
            ptype="store purchase"
        else:
            ptype="donation"
        if payment_intent.currency=='usd':
            numsnickers = str(round(amount / 1.48))
        elif payment_intent.currency == 'eur':
            numsnickers = str(round(amount / 1.25))
        elif payment_intent.currency == 'gbp':
            numsnickers = str(round(amount / 0.65))
        elif payment_intent.currency == 'cad':
            numsnickers = str(round(amount / 1.11))
        elif payment_intent.currency == 'aud':
            numsnickers = str(round(amount / 0.99))
        elif payment_intent.currency == 'nzd':
            numsnickers = str(round(amount / 0.88))
        else:
            numsnickers = 'an unknown amount of'
            
        currency = payment_intent.currency
        if currency == 'aud':
            currency = 'dollary-doos'
            
            
        print(f'[\x0315Stripe\x03] A {ptype} of \x0315{str(amount)}\x03 {currency.upper()} '
             f'was made. This equals about {numsnickers} snickers!')
        send(f'#{request.registry.settings["stripe_channel"]}',
             f'[\x0315Stripe\x03] A {ptype} of \x0315{str(amount)}\x03 {currency.upper()} '
             f'was made. This equals about {numsnickers} snickers!', 'No!', request)
