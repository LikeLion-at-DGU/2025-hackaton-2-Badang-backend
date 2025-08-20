from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import SeedTrendsApi, GetTrendApi
# router = DefaultRouter()
# router.register()

# urlpatterns = router.urls
app_name = "trends"

urlpatterns = [
    path("seed", SeedTrendsApi.as_view()),
    path("<int:trend_id>", GetTrendApi.as_view()),
]