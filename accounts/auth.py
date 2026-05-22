import logging

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

logger = logging.getLogger('speakfly.auth')


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        try:
            data = super().validate(attrs)
        except Exception:
            username = attrs.get('username', '')
            logger.warning('login_failed username=%s', username)
            raise
        logger.info('login_ok user_id=%s', self.user.id)
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email or '',
            'isAdmin': self.user.is_staff,
        }
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
