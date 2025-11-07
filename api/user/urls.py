from rest_framework import routers
from django.urls import include, path

from . import views

router = routers.DefaultRouter()
router.register(r'', views.UserViewSet)

urlpatterns = [
    path('login/', views.EmailAuthTokenView.as_view(), name='signin'),
    path('logout/', views.LogoutView.as_view(), name='signout'),
    path('logout/<int:id>/', views.LogoutView.as_view(), name='signout-legacy'),
    path('', include(router.urls)),
]
