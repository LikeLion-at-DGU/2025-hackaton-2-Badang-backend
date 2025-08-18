from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .services.llm import run_llm

class TestHaikuView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        # 예: {"topic": "ai"}
        topic = request.data.get("topic", "ai")
        system = "너는 하이쿠 시인이다. 5-7-5 느낌을 살려 한국어로 짧게."
        user = f"{topic}에 대한 하이쿠를 써줘."
        text = run_llm(system, user)
        return Response({"text": text}, status=status.HTTP_200_OK)
