from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NewsletterViewSet, createNewsletterTest

app_name = "newsletter"

default_router = DefaultRouter(trailing_slash=False)
default_router.register(r'newsletters', NewsletterViewSet, basename='newsletter')

urlpatterns = [
    path('', include(default_router.urls)),
    path('create/<int:storeId>/', createNewsletterTest, name='create_newsletter'), # 뉴스레터 생성 테스트용 URL
]