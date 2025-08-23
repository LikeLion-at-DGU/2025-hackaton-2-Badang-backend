from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, NotFound
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404

from .selectors import getNewsletterList
from .selectors import searchNewsletters
from .serializers import NewsletterListSerializer, NewsletterSerializer
from .services import createNewsletter
from .models import Newsletter
from .selectors import getNewsletterDetail

from main.models import Store, Profile
from review.models import ReviewAnalysis
from trend.models import Keyword

# Create your views here.
class NewsletterViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    
    queryset = Newsletter.objects.all()
    serializer_class = NewsletterSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return NewsletterListSerializer
        return NewsletterSerializer

    def list(self, request, *args, **kwargs):
        storeId = request.query_params.get('storeId')
        cursor = request.query_params.get('cursor')
        limit = request.query_params.get('limit', 9)

        if not storeId:
            return Response(
                {"error":"BadRequest","message":"storeId 값이 필요합니다.","statusCode":400},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 프로필, 가게 정보 검사
        try:
            store = get_object_or_404(Store, id=storeId)
            limit = int(limit)
            
        except (ValueError, TypeError):
            return Response({
                "error": "BadRequest",
                "message": "limit 값이 유효하지 않은 숫자입니다.",
                "statusCode": 400
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Store.DoesNotExist:
            # 인증 또는 권한 문제인 경우 명세의 401 응답 형태로 반환
            return Response({
                "error": "forbidden Error",
                "message": "유효하지 않은 회원 정보입니다",
                "statuscode": 401
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        newsletters, hasMore = getNewsletterList(store=store, cursor=cursor, limit=limit)
        serializer = self.get_serializer(newsletters, many=True, context={"request": request})

        responseData = {
            "message": "뉴스레터 목록을 성공적으로 조회하였습니다.",
            "statusCode": 200,
            "data": {
                "newsletters": serializer.data,
                "hasMore": hasMore
            }
        }
            
        return Response(responseData, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None, *args, **kwargs):
        print(f"디버그: retrieve 메서드 호출. 전달된 pk: {pk}")

        try:
            # pk 값을 정수로 명시적으로 변환
            news_id = int(pk)
            print(f"디버그: 정수로 변환된 news_id: {news_id}")
            
            newsletter_obj = getNewsletterDetail(news_id)
            
            print(f"디버그: 데이터베이스에서 객체 발견. ID: {newsletter_obj.id}")
            
            serializer = self.get_serializer(newsletter_obj)
            
            responseData = {
                "message": "뉴스레터 상세 정보를 성공적으로 조회하였습니다.",
                "statusCode": 200,
                "data": serializer.data
            }

            return Response(responseData, status=status.HTTP_200_OK)

        # 예외 처리 블록을 더 구체적으로 나눕니다.
        except ValueError:
            return Response(
                {"error": "BadRequest", "message": "유효하지 않은 뉴스레터 ID입니다.", "statusCode": 400},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Newsletter.DoesNotExist:
            # 객체가 존재하지 않을 때만 이 메시지를 반환하도록 명확히 분리
            return Response(
                {"error": "NotFound", "message": "해당 뉴스레터를 찾을 수 없습니다", "statusCode": 404},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # 예상치 못한 다른 예외가 발생하면 출력
            print(f"디버그: 예상치 못한 오류 발생 - {e}")
            return Response(
                {"error": "Internal Server Error", "message": "서버 내부 오류가 발생했습니다.", "statusCode": 500},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def search(self, request, *args, **kwargs):
        query = request.query_params.get('query')
        keyword = request.query_params.get('keyword')
        is_user_made = request.query_params.get('isUserMade')
        is_liked = request.query_params.get('isLiked')
        page = request.query_params.get('page')
        limit = request.query_params.get('limit', 9)

        try:
            limit = int(limit)
        
        except (ValueError, TypeError):
            return Response({
                "error": "BadRequest",
                "message": "limit 값이 유효하지 않습니다",
                "statusCode": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            results, hasMore = searchNewsletters(query=query, keyword=keyword, is_user_made=is_user_made, is_liked=is_liked, page=page, limit=limit)
        
        except ValueError as e:
            return Response({
                "error": "BadRequest",
                "message": str(e),
                "statusCode": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = NewsletterListSerializer(results, many=True, context={"request": request})

        return Response({
            "message": "뉴스레터 검색 성공",
            "statusCode": 200,
            "data": {
                "newsletters": serializer.data
            },
            "hasMore": hasMore
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'])
    def like(self, request, pk=None):
        try:
            newsletter = get_object_or_404(Newsletter, id=pk)
        except Exception:
            return Response({"error": "NotFound", "message": "해당 뉴스레터를 찾을 수 없습니다", "statusCode": 404}, status=status.HTTP_404_NOT_FOUND)

        if newsletter.isLiked:
            message = "찜하기 성공"
        else:
            message = "찜하기 해제 성공"

        newsletter.isLiked = not bool(newsletter.isLiked)
        newsletter.save()

        return Response({
            "message": message,
            "statusCode": 200,
            "data": {"isLiked": newsletter.isLiked}
        }, status=status.HTTP_200_OK)


    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        # detail=True 이므로 URL의 {pk}를 storeId로 사용합니다.
        storeId = pk

        if request.method != 'POST':
            return Response({"error": "Method Not Allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        try:
            new_newsletter = createNewsletter(storeId=storeId)

            return Response({
                "message": "뉴스레터가 성공적으로 생성되었습니다.",
                "data": NewsletterSerializer(new_newsletter, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)

        except (ValueError, Store.DoesNotExist, ReviewAnalysis.DoesNotExist, Keyword.DoesNotExist) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
