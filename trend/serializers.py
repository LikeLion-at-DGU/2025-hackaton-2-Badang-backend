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
    keywordImageUrl = serializers.SerializerMethodField()  # 응답에서만 'URL' 제공

    class Meta:
        model = Keyword
        fields = ["id", "keywordName", "keywordImageUrl", "status", "isImage"]

    def get_keywordImageUrl(self, obj):
        # DB엔 path가 들어있다고 가정
        if obj.keywordImageUrl:
            return default_storage.url(obj.keywordImageUrl)
        return None

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