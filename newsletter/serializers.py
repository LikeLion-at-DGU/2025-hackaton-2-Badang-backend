from rest_framework import serializers
from django.core.files.storage import default_storage
from main.models import Store
from trend.models import Keyword
from .models import Newsletter

class KeywordRes(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = "__all__" 
        
class NewsletterListSerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(format='%Y-%m-%d')
    isUserMade = serializers.BooleanField()
    keyword = KeywordRes(many=True, read_only=True)

    class Meta:
        model = Newsletter
        fields = [
            "id",
            "title",
            "firstContent",
            "secondContent",
            "createdAt",
            "isUserMade",
            "isLiked",
            "reviewAnalysisId",
            "keyword",   # 중첩 결과로 전체 Keyword 필드들 반환
        ]

class NewsletterListResponseSerializer(serializers.Serializer):
    newsletters = NewsletterListSerializer(many=True)
    hasMore = serializers.BooleanField(default=False)
    
class NewsletterSerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(format='%Y-%m-%d')
    storeName = serializers.CharField(source='store.name', read_only=True)
    userName = serializers.CharField(source='user.profileName', read_only=True)
    keywords = serializers.StringRelatedField(many=True, read_only=True)
    reviewAnalysisId = serializers.PrimaryKeyRelatedField(source='review_analysis', read_only=True)

    class Meta:
        model = Newsletter
        fields = [
            'id', 'title', 'firstContent', 'secondContent', 'createdAt', 
            'storeName', 'userName', 'keywords', 'reviewAnalysisId', 'isUserMade', 'isLiked'
        ]