from common.serializers import *
from main.models import *
from .models import *
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

class DomainError(Exception):
    pass


def profileLogin(username: str, password: str):
    
    user = authenticate(username=username, password=password)
    if user is None:
        raise DomainError("아이디 또는 비밀번호가 잘못되었습니다.")
    
    if not user.is_active:
        raise DomainError("비활성화된 계정입니다.")
    
    # JWT 토큰 생성
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token
    
    return {
        "user": user,
        "tokens": {
            "access": str(access_token),
            "refresh": str(refresh)
        }
    }

def profileLogout(refresh_token: str):
    
    try:
        token = RefreshToken(refresh_token)
        token.blacklist() 
        return True
    except Exception as e:
        raise DomainError(f"로그아웃 실패: {str(e)}")