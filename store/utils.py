# utils.py
from .models import Cart

def calculate_total_price(user):
    cart_items = Cart.objects.filter(user=user)
    total_price = sum(item.total_price for item in cart_items)
    return total_price
# utils.py
#import amazon_pay.client

#from django.conf import settings
'''
def get_amazon_pay_client():
    config = settings.AMAZON_PAY
    client = amazon_pay.client.AmazonPayClient(
        merchant_id=config['merchant_id'],
        access_key=config['access_key'],
        secret_key=config['secret_key'],
        sandbox=config['sandbox'],
        currency_code=config['currency_code'],
        region=config['region']
    )
    return client
    '''
