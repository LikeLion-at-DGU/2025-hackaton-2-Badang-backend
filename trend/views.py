from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .serializers import *
from .services import *
from .models import *


class SeedTrendsApi(APIView):
    def post(self, request):
        
        req = TrendInputReq(data=request.data)
        req.is_valid(raise_exception=True)

        trend = saveSingleKeywordToDB(req.validated_data["trends"])
        out = TrendRes(trend, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)

class GetTrendApi(APIView):
    def get(self, request, trend_id):
        trend = get_object_or_404(Trend, id=trend_id)
        out = TrendRes(trend, context={"request": request})
        return Response(out.data)
