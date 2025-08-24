from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import *
from newsletter.serializers import NewsletterSerializer
from .services import *
from newsletter.selectors import getNewsletterDetail
from .models import *
from main.models import Store
from newsletter.views import createNewsletter
from newsletter.services import createNewsletterByUser


class DomainError(Exception):
    pass


class TrendsToKeywordView(APIView):
    def post(self, request):
        req = TrendInputReq(data=request.data)
        req.is_valid(raise_exception=True)

        trend, _ = saveKeywordsFromTrends(req.validated_data["trends"])

        # 커밋 이후 DB에서 다시 읽기 (키워드 프리패치)
        trendRefetched = Trend.objects.prefetch_related("keywords").get(id=trend.id)

        trendOut = TrendRes(trendRefetched, context={"request": request}).data
        # 굳이 바깥으로 keywords를 중복 노출할 필요 없으면 trendOut만 내려도 OK
        return Response(
            {
                "message": "트렌드와 키워드가 생성되었습니다.",
                "statusCode": 201,
                "data": {
                    "trend": trendOut,
                    "keywords": trendOut["keywords"],  # 필요 없으면 이 라인은 삭제해도 됨
                },
            },
            status=status.HTTP_201_CREATED,
        )
        
class CreateKeywordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user.profile
            me = user.stores.first()
            if me is None:
                raise DomainError("request 를 보낸 유저에게는 가게가 없습니다.")
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        req = KeywordsInputReq(data=request.data)
        req.is_valid(raise_exception=True)
        keyword = req.validated_data["keyword"]

        try:
            
            kw = keywordSaveByUserSync(keyword, me)

            if kw.status != "succeeded" or not kw.keywordImageUrl:
                return Response({"detail": "키워드 이미지 생성에 실패했습니다."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            news = createNewsletterByUser(me.id, kw)
            
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"detail": "키워드 생성에 실패했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            news = createNewsletterByUser(me.id, kw)  # kw는 Keyword 인스턴스
            kwData = KeywordRes(kw).data
            newsData = NewsletterSerializer(news, context={'request': request}).data

            return Response({
                "message": "키워드와 뉴스레터를 생성했습니다.",
                "statusCode": 200,
                "data": {
                    "keyword": kwData,       # 여기의 keywordImageUrl은 serializer에서 URL로 변환됨
                    "newsletter": newsData
                }
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({"detail": "뉴스레터 생성에 실패했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetTrendApi(APIView):
    def get(self, request, trend_id):
        trend = get_object_or_404(Trend, id=trend_id)
        out = TrendRes(trend, context={"request": request})
        return Response(out.data)