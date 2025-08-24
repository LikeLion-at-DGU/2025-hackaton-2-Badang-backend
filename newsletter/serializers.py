from rest_framework import serializers
from django.core.files.storage import default_storage
from main.models import Store
from trend.models import Keyword
from .models import Newsletter

# ✅ trend의 KeywordRes 재사용
from trend.serializers import KeywordRes

class NewsletterListSerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(format='%Y-%m-%d')
    isUserMade = serializers.BooleanField()
    keywords = KeywordRes(many=True, read_only=True)

    reviewAnalysisId = serializers.IntegerField(source='reviewAnalysis.id', read_only=True)
    storeName = serializers.CharField(source='store.name', read_only=True)
    userName = serializers.CharField(source='store.user.profileName', read_only=True)

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
            "storeName",
            "userName",
            "keywords"
        ]

class NewsletterListResponseSerializer(serializers.Serializer):
    newsletters = NewsletterListSerializer(many=True)
    hasMore = serializers.BooleanField(default=False)

class NewsletterSerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(format='%Y-%m-%d')
    storeName = serializers.CharField(source='store.name', read_only=True)
    userName = serializers.CharField(source='user.profileName', read_only=True)
    keywords = KeywordRes(many=True, read_only=True)
    reviewAnalysisId = serializers.PrimaryKeyRelatedField(source='review_analysis', read_only=True)

    class Meta:
        model = Newsletter
        fields = [
            'id', 'title', 'firstContent', 'secondContent', 'createdAt',
            'storeName', 'userName', 'keywords', 'reviewAnalysisId', 'isUserMade', 'isLiked'
        ]
