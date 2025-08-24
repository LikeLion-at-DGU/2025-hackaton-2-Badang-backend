from rest_framework.routers import DefaultRouter
from rest_framework import routers
from django.urls import path, include
from .views import *

# router = DefaultRouter()
# router.register()

# urlpatterns = router.urls

app_name = 'main'


urlpatterns = [
    # 인증 관련 URL
    path('signup', signupView.as_view(), name='signup'),         # 회원가입
    path('login', loginView.as_view(), name='login'),           # 로그인
    path('logout', logoutView.as_view(), name='logout'),         # 로그아웃
    path('token', tokenRefreshView.as_view(), name='token_refresh'), # 토큰 갱신
    path('me/', meView.as_view(), name='me'),

    path('stores', storeView.as_view(), name='store'), 
]