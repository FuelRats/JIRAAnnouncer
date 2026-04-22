import stripe
from pyramid.httpexceptions import HTTPError
from pyramid.view import view_config
from ..utils import send
import logging
import pickle
import os
from datetime import datetime

log = logging.getLogger(__name__)

PICKLE_FILE = "donation_totals.p"

MONTHLY_GOAL = 350.0  # USD

def load_donation_totals():
    if os.path.exists(PICKLE_FILE):
        with open(PICKLE_FILE, "rb") as f:
            return pickle.load(f)
    return {}

def save_donation_totals(totals):
    with open(PICKLE_FILE, "wb") as f:
        pickle.dump(totals, f)

def get_current_month():
    now = datetime.utcnow()
    return f"{now.year}-{now.month:02d}"

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
        decimalplace = len(str(payment_intent.amount))-2
        amount = float(f'{str(payment_intent.amount)[:decimalplace]}.{str(payment_intent.amount)[decimalplace:]}')
        if payment_intent.metadata.get('id_cart'):
            ptype = "store purchase"
        else:
            ptype = "donation"
        usd_amount = amount / 1.57
        if payment_intent.currency == 'usd':
            numsnickers = str(round(usd_amount))
            usd_value = amount
        elif payment_intent.currency == 'eur':
            numsnickers = str(round(usd_amount / 0.92))
            usd_value = amount / 0.92
        elif payment_intent.currency == 'gbp':
            numsnickers = str(round(usd_amount / 0.77))
            usd_value = amount / 0.77
        elif payment_intent.currency == 'cad':
            numsnickers = str(round(usd_amount / 1.44))
            usd_value = amount / 1.44
        elif payment_intent.currency == 'aud':
            numsnickers = str(round(usd_amount / 1.58))
            usd_value = amount / 1.58
        elif payment_intent.currency == 'nzd':
            numsnickers = str(round(usd_amount / 1.75))
            usd_value = amount / 1.75
        else:
            numsnickers = 'an unknown amount of'
            usd_value = 0.0

        currency = payment_intent.currency
        if currency == 'aud':
            currency = 'dollary-doos'

        # Only count donations (not store purchases)
        if ptype == "donation" and usd_value > 0:
            totals = load_donation_totals()
            month = get_current_month()
            totals[month] = totals.get(month, 0.0) + usd_value
            save_donation_totals(totals)
            percent = (totals[month] / MONTHLY_GOAL) * 100
            percent_str = f"Donation goal: {percent:.1f}% of ${MONTHLY_GOAL:.0f} reached this month!"
        else:
            percent_str = None

        msg = (f'[\x0315Stripe\x03] A {ptype} of \x0315{str(amount)}\x03 {currency.upper()} '
               f'was made. This equals about {numsnickers} snickers!')
        if percent_str:
            msg += f" {percent_str}"

        print(msg)
        send(f'#{request.registry.settings["stripe_channel"]}', msg, 'No!', request)
    return
