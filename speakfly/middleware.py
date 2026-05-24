import logging
import time
import uuid

from speakfly.log_handlers import sanitize_message

logger = logging.getLogger('speakfly.request')

# 不记录请求体的路径（含登录等）
_SKIP_BODY_PATHS = ('/api/auth/login/', '/api/auth/register/')


class RequestLoggingMiddleware:
    """记录 API 请求（不含密码、Token 等敏感信息）"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/api/'):
            return self.get_response(request)

        start = time.perf_counter()
        request_id = uuid.uuid4().hex[:12]
        user = getattr(request, 'user', None)
        user_id = user.id if user and getattr(user, 'is_authenticated', False) else None

        if request.path.startswith('/api/upload'):
            content_length = request.META.get('CONTENT_LENGTH', '-')
            content_type = request.META.get('CONTENT_TYPE', '-')
            auth_present = 'yes' if request.META.get('HTTP_AUTHORIZATION') else 'no'
            logger.info(
                'rid=%s upload_request method=%s path=%s content_length=%s content_type=%s auth=%s',
                request_id,
                request.method,
                sanitize_message(request.path),
                content_length,
                sanitize_message(content_type[:80] if content_type else '-'),
                auth_present,
            )

        response = self.get_response(request)
        duration_ms = int((time.perf_counter() - start) * 1000)
        status = getattr(response, 'status_code', 0)

        logger.info(
            'rid=%s method=%s path=%s status=%s duration_ms=%s user_id=%s ip=%s',
            request_id,
            request.method,
            sanitize_message(request.path),
            status,
            duration_ms,
            user_id or '-',
            _mask_ip(_client_ip(request)),
        )
        if status >= 400:
            logger.warning(
                'rid=%s request_failed status=%s path=%s',
                request_id,
                status,
                sanitize_message(request.path),
            )
        return response


def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '-')


def _mask_ip(ip):
    """GDPR：IP 仅保留前两段"""
    if not ip or ip == '-':
        return '-'
    parts = ip.split('.')
    if len(parts) == 4:
        return f'{parts[0]}.{parts[1]}.*.*'
    return ip[:8] + '***' if len(ip) > 8 else ip
