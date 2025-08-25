from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJwtAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # Authorization 헤더는 보지 않음 (쿠키만 사용)
        rawToken = request.COOKIES.get('access_token')
        if not rawToken:
            return None
        validatedToken = self.get_validated_token(rawToken)
        return (self.get_user(validatedToken), validatedToken)