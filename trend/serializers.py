from rest_framework import serializers
from django.core.files.storage import default_storage
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
    # 카멜케이스 메서드명 사용
    keywordImageUrl = serializers.SerializerMethodField(method_name="getKeywordImageUrl")

    class Meta:
        model = Keyword
        fields = "__all__"

    def getKeywordImageUrl(self, obj):
        """
        - DB 값이 절대 URL이면 그대로 반환
        - 상대 경로(스토리지 키)이면 default_storage.url() → 필요 시 request.build_absolute_uri()로 절대화
        """
        pathOrUrl = getattr(obj, "keywordImageUrl", None) or getattr(obj, "keywordImagePath", None)
        if not pathOrUrl:
            return None

        if isinstance(pathOrUrl, str) and pathOrUrl.startswith(("http://", "https://")):
            return pathOrUrl

        try:
            url = default_storage.url(pathOrUrl.lstrip("/"))
        except Exception:
            return None

        req = self.context.get("request")
        return req.build_absolute_uri(url) if (req and isinstance(url, str) and url.startswith("/")) else url

# 트렌드 응답용
class TrendRes(serializers.ModelSerializer):
    keywords = KeywordRes(many=True, read_only=True)

    class Meta:
        model = Trend
        fields = ["id", "trendData", "createdAt", "keywords"]
