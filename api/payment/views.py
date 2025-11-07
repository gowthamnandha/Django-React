import os

import braintree
from django.core.exceptions import ImproperlyConfigured
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token


BRAINTREE_ENVIRONMENT = os.environ.get('BRAINTREE_ENVIRONMENT', 'Sandbox')
_gateway = None


def get_gateway():
    global _gateway
    if _gateway is None:
        merchant_id = os.environ.get('BRAINTREE_MERCHANT_ID')
        public_key = os.environ.get('BRAINTREE_PUBLIC_KEY')
        private_key = os.environ.get('BRAINTREE_PRIVATE_KEY')

        if not all([merchant_id, public_key, private_key]):
            raise ImproperlyConfigured('Braintree credentials are not configured.')

        environment = getattr(braintree.Environment, BRAINTREE_ENVIRONMENT, braintree.Environment.Sandbox)
        _gateway = braintree.BraintreeGateway(
            braintree.Configuration(
                environment,
                merchant_id=merchant_id,
                public_key=public_key,
                private_key=private_key,
            )
        )
    return _gateway


def validate_user_session(user_id, token):
    return Token.objects.filter(key=token, user_id=user_id).exists()


@csrf_exempt
def generate_token(request, id, token):
    if not validate_user_session(id, token):
        return JsonResponse({'error': 'invalid session, please login again'})
    gateway = get_gateway()
    return JsonResponse({'clientToken': gateway.client_token.generate(), 'success': True})


@csrf_exempt
def process_payment(request, id, token):
    if not validate_user_session(id, token):
        return JsonResponse({'error': 'invalid session, please login again'})

    nonce_from_the_client = request.POST["PaymentMethodNonce"]
    amount_from_the_client = request.POST['amount']

    gateway = get_gateway()
    result = gateway.transaction.sale({
        "amount": amount_from_the_client,
        "payment_method_nonce": nonce_from_the_client,
        "options": {
            "submit_for_settlement": True
        }
    })

    if result.is_success:
        return JsonResponse({
            "success": result.is_success,
            'transaction': {'id': result.transaction.id, 'amount': result.transaction.amount}
        })
    else:
        return JsonResponse({'error': True, 'success': False})
