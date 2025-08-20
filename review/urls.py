from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import ReviewAnalysisViewSet

app_name = "review"

default_router = DefaultRouter(trailing_slash=False)
default_router.register(r'analysis', ReviewAnalysisViewSet, basename='analysis')

urlpatterns = [
    path('', include(default_router.urls)),
]

