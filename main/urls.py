from rest_framework.routers import DefaultRouter
from rest_framework import routers
from django.urls import path, include
from .views import *

# router = DefaultRouter()
# router.register()

# urlpatterns = router.urls

app_name = 'main'

user_router = routers.SimpleRouter(trailing_slash=False)
user_router.register("users", ProfileViewSet, basename="users")

store_router = routers.SimpleRouter(trailing_slash=False)
store_router.register("stores", StoreViewSet, basename="stores")



urlpatterns = [
    path("", include(user_router.urls)),
    path("", include(store_router.urls)),
    path('login', LoginView.as_view(), name='authLogin'),
    path('me', MeView.as_view(), name='authMe'),
]