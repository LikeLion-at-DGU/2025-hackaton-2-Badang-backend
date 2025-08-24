# serializers.py
from rest_framework import serializers
from .models import *
from main.models import *
from newsletter.models import Newsletter
from django.core.files.storage import default_storage

# 사용자가 직접 입력하는 키워드
class KeywordsInputReq(serializers.Serializer):
    keyword = serializers.CharField()

# 관리자가 트렌드 입력할 때 사용
class TrendInputReq(serializers.Serializer):
    trends = serializers.ListField(
        child=serializers.CharField(max_length=100),
        allow_empty=False
    )

# 키워드 응답용
class KeywordRes(serializers.ModelSerializer):
    keywordImageUrl = serializers.SerializerMethodField()

    class Meta:
        model = Keyword
        fields = "__all__"

    def get_keywordImageUrl(self, obj):
        """
        DB에는 상대 경로(path)일 수도, 절대 URL일 수도 있음.
        - 절대 URL이면 그대로 반환
        - 상대 경로이면 default_storage.url()로 절대 URL을 만들어 반환
        """
        path = obj.keywordImageUrl
        if not path:
            return None
        if isinstance(path, str) and path.startswith(("http://", "https://")):
            return path
        try:
            return default_storage.url(path.lstrip("/"))
        except Exception:
            return None

    getKeywordImageUrl = get_keywordImageUrl

# 트렌드 응답용
class TrendRes(serializers.ModelSerializer):
    keywords = KeywordRes(many=True, read_only=True)
    class Meta:
        model = Trend
        fields = ["id", "trendData", "createdAt", "keywords"]
        
class NewsletterRes(serializers.ModelSerializer):
    class Meta:
        model = Newsletter
        fields = [
            "id", 
            "title",
            "thumbnail",
            "isUserMade",
            "createdAt",
            "isLiked",
            "firstContent", 
            "secondContent", 
            "feedback"
        ]