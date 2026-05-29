from django.http import JsonResponse
from django.utils import timezone


def health_check(request):
    return JsonResponse({
        'status': 'ok',
        'service': 'speakfly-api',
        'uploadMode': 'direct-oss-v2',
        'uploadSignPath': '/api/upload/sign/',
        'timestamp': timezone.now().isoformat(),
    })
