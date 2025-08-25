from django.urls import path
from .views import TrendsToKeywordView, GetTrendApi, CreateKeywordView

app_name = "trend"

urlpatterns = [
    # 트렌드 데이터로 AI 키워드 생성
    path("createtrends", TrendsToKeywordView.as_view(), name="create-from-trends"),
    # 사용자 직접 키워드 생성
    path("keywords", CreateKeywordView.as_view(), name="create-keyword"),
]