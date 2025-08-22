# serializers.py
from rest_framework import serializers
from .models import *
from main.models import *
from newsletter.models import Newsletter

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
    class Meta:
        model = Keyword
        fields = ["keywordName", "keywordImageUrl", "status", "isImage", "keywordCreatedAt"]

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