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
        raw = getattr(obj, "keywordImageUrl", None) or getattr(obj, "keywordImagePath", None)
        if not raw:
            return None

        if isinstance(raw, str) and raw.startswith(("http://", "https://")):
            parsed = urlparse(raw)
            # 이미 서명돼 있으면 그대로
            if parsed.query:
                return raw
            # 쿼리 없으면 키 뽑아서 재서명
            key = parsed.path.lstrip("/")
            return default_storage.url(key)

        # 상대 경로면 스토리지로 서명 URL 생성
        url = default_storage.url(str(raw).lstrip("/"))

        req = self.context.get("request")
        return req.build_absolute_uri(url) if (req and url.startswith("/")) else url

# 트렌드 응답용
class TrendRes(serializers.ModelSerializer):
    keywords = KeywordRes(many=True, read_only=True)

    class Meta:
        model = Trend
        fields = ["id", "trendData", "createdAt", "keywords"]
