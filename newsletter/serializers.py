from rest_framework import serializers
from main.models import Store
from .models import Newsletter

class NewsletterListSerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(source="createdAt")
    isUserMade = serializers.BooleanField(source="isUserMade")
    keyword = serializers.CharField(source="keyword.name", read_only=True)
    
    class Meta:
        model = Newsletter
        fields = ['id', 'title', 'thumbnail', 'createdAt', 'isUserMade', 'keyword']

class NewsletterListResponseSerializer(serializers.Serializer):
    newsletters = NewsletterListSerializer(many=True)
    hasMore = serializers.BooleanField(default=False)
    
class NewsletterSerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(source='created_at', format='%Y-%m-%d', read_only=True)
    storeName = serializers.CharField(source='store.name', read_only=True)
    userName = serializers.CharField(source='user.profileName', read_only=True)

    class Meta:
        model = Newsletter
        # 실제 Newsletter 모델의 필드명에 맞게 작성
        fields = [
            'id', 'title', 'content', 'createdAt', 
            'storeName', 'userName'
        ]