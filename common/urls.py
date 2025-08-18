from django.urls import path
from .views import TestHaikuView

app_name = 'common'

urlpatterns = [
    path("ai", TestHaikuView.as_view()),
]
