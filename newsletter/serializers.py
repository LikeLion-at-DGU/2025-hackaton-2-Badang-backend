from rest_framework import serializers
from main.models import Store
from .models import Newsletter

class NewsletterListSerializer(serializers.ModelSerializer):
    # 날짜는 YYYY-MM-DD 포맷으로 반환
    createdAt = serializers.DateTimeField(format='%Y-%m-%d')
    isUserMade = serializers.BooleanField()
    keyword = serializers.SerializerMethodField()
    # 썸네일은 URL로 반환
    thumbnail = serializers.SerializerMethodField()
    
    class Meta:
        model = Newsletter
        fields = ['id', 'title', 'thumbnail', 'createdAt', 'isUserMade', 'keyword']

    def get_thumbnail(self, obj):
        request = self.context.get('request')
        if not obj.thumbnail:
            return ""
        try:
            url = obj.thumbnail.url
        except Exception:
            return ""
        if request is None:
            return url
        return request.build_absolute_uri(url)

    def get_keyword(self, obj):
        first = obj.keywords.first()
        return first.keywordName if first is not None else ""

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