from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework.authtoken.models import Token

from .models import Order
from .serializers import OrderSerializer


# Create your views here.

def validate_user_session(user_id, token):
    return Token.objects.filter(key=token, user_id=user_id).exists()


@csrf_exempt
def add(request, id, token):
    if not validate_user_session(id, token):
        return JsonResponse({'error': 'please login again', 'code': '600'})

    if request.method == "POST":
        user_id = id
        transaction_id = request.POST['transaction_id']
        amount = request.POST['amount']
        products = request.POST['products']

        total_pro = len([p for p in products.split(',') if p.strip()])

        UserModel = get_user_model()

        try:
            user = UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return JsonResponse({'error': 'user does not exists'})

        ordr = Order(
            user=user,
            product_names=products,
            total_products=total_pro,
            transaction_id=transaction_id,
            total_amount=amount,
        )
        ordr.save()
        return JsonResponse({'success': True, 'error': False, 'msg': 'Order placed successfully'})

    return JsonResponse({'error': 'Invalid request method'}, status=405)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('id')
    serializer_class = OrderSerializer
