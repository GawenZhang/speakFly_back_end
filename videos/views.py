from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from django.shortcuts import get_object_or_404
import re

from .models import Video, Lesson, UserFavorite
from .serializers import (
    VideoSerializer,
    VideoCreateUpdateSerializer,
    LessonSerializer,
    LessonWriteSerializer,
)


class VideoViewSet(ModelViewSet):
    """视频 CRUD + 收藏"""
    queryset = Video.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return VideoCreateUpdateSerializer
        return VideoSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = VideoSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = VideoSerializer(instance, context={'request': request})
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        ser = VideoCreateUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        video = ser.save()
        return Response(
            VideoSerializer(video, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        if 'videoUrl' in data:
            data['video_url'] = data.pop('videoUrl')
        ser = VideoCreateUpdateSerializer(instance, data=data, partial=partial)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(VideoSerializer(instance, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='favorite')
    def favorite(self, request, pk=None):
        """切换收藏状态"""
        video = get_object_or_404(Video, pk=pk)
        fav, created = UserFavorite.objects.get_or_create(user=request.user, video=video)
        if not created:
            fav.delete()
            is_favorite = False
        else:
            is_favorite = True
        return Response({'isFavorite': is_favorite})

    @action(detail=True, methods=['get'], url_path='lesson')
    def lesson(self, request, pk=None):
        """获取该视频的课程详情；无记录时自动创建空 Lesson，避免编辑页 404。"""
        video = get_object_or_404(Video, pk=pk)
        lesson, _ = Lesson.objects.get_or_create(
            video=video,
            defaults={
                'chinese_text': '',
                'english_text': '',
                'phrases': [],
                'sentences': [],
                'highlight_phrases': [],
            },
        )
        return Response(LessonSerializer(lesson).data)


class LessonViewSet(ModelViewSet):
    """课程详情：按 video_id 获取/创建/更新"""
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return LessonWriteSerializer
        return LessonSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        video_id = request.query_params.get('video_id')
        if not video_id:
            lessons = Lesson.objects.all()[:100]
            serializer = LessonSerializer(lessons, many=True)
            return Response(serializer.data)
        lesson = Lesson.objects.filter(video_id=video_id).first()
        if not lesson:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(LessonSerializer(lesson).data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        # pk 在这里是 video_id
        lesson = get_object_or_404(Lesson, video_id=pk)
        return Response(LessonSerializer(lesson).data)

    def create(self, request, *args, **kwargs):
        video_id = request.data.get('videoId')
        if not video_id:
            return Response({'videoId': ['必填']}, status=status.HTTP_400_BAD_REQUEST)
        video = get_object_or_404(Video, pk=video_id)
        data = request.data.copy()
        chinese_text = data.get('chineseText', data.get('chinese_text', ''))
        english_text = data.get('englishText', data.get('english_text', ''))
        phrases = data.get('phrases', [])
        sentences = data.get('sentences', [])
        highlight_phrases = data.get('highlightPhrases', data.get('highlight_phrases', []))
        from .serializers import _as_json_list, _normalize_highlight_phrases, _normalize_sentences
        lesson, created = Lesson.objects.update_or_create(
            video=video,
            defaults={
                'chinese_text': chinese_text or '',
                'english_text': english_text or '',
                'phrases': _as_json_list(phrases),
                'sentences': _normalize_sentences(sentences),
                'highlight_phrases': _normalize_highlight_phrases(highlight_phrases),
            }
        )
        return Response(
            LessonSerializer(lesson).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class NextEpisodeView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        videos = Video.objects.all().values_list('episode', flat=True)
        numbers = []
        for ep in videos:
            m = re.search(r'EP\s*(\d+)', str(ep), re.I)
            if m:
                numbers.append(int(m.group(1)))
        next_num = max(numbers) + 1 if numbers else 1
        return Response({'nextEpisode': next_num})


# 允许上传的扩展名（图片/视频/音频存 OSS，数据库只存 URL）
UPLOAD_IMAGE_EXT = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
UPLOAD_VIDEO_EXT = {'mp4', 'webm', 'mov', 'avi', 'm4v', 'mkv'}
UPLOAD_AUDIO_EXT = {'mp3', 'wav', 'ogg', 'm4a'}

UPLOAD_TYPE_MAP = {
    'image': ('image', UPLOAD_IMAGE_EXT),
    'video': ('video', UPLOAD_VIDEO_EXT),
    'audio': ('audio', UPLOAD_AUDIO_EXT),
}


class SignOSSUploadView(APIView):
    """获取 OSS 直传签名 URL（视频等大文件走浏览器 → OSS，不经 Nginx 体积限制）"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        import logging
        from speakfly.oss_utils import create_presigned_upload
        logger = logging.getLogger('speakfly.upload')

        filename = (request.data.get('filename') or '').strip()
        upload_type = (request.data.get('type') or 'video').lower()
        content_type = (request.data.get('contentType') or '').strip()
        logger.info(
            'sign_start filename=%s type=%s content_type=%s user_id=%s is_staff=%s',
            filename,
            upload_type,
            content_type,
            getattr(request.user, 'id', None),
            getattr(request.user, 'is_staff', False),
        )

        if not filename:
            logger.warning('sign_failed reason=missing_filename user_id=%s', getattr(request.user, 'id', None))
            return Response({'detail': '缺少 filename'}, status=status.HTTP_400_BAD_REQUEST)

        subdir, allowed = UPLOAD_TYPE_MAP.get(upload_type, ('file', None))
        ok, upload_url, public_url, err = create_presigned_upload(
            filename,
            subdir=subdir,
            allowed_extensions=allowed,
            content_type=content_type,
        )
        if not ok:
            logger.warning('sign_failed filename=%s err=%s', filename, err)
            return Response({'detail': err or '签名失败', 'url': None}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(
            'sign_ok filename=%s public_url=%s upload_host=%s',
            filename,
            (public_url or '')[:80],
            upload_url.split('/')[2] if upload_url and '://' in upload_url else '-',
        )
        return Response({'uploadUrl': upload_url, 'url': public_url, 'detail': '签名成功'})


class UploadToOSSView(APIView):
    """上传文件到阿里云 OSS，返回 URL。仅管理员。type: image | video | audio"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        import logging
        from speakfly.oss_utils import upload_file_to_oss
        logger = logging.getLogger('speakfly.upload')
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'detail': '请选择文件', 'url': None}, status=status.HTTP_400_BAD_REQUEST)
        upload_type = (request.data.get('type') or request.POST.get('type') or 'image').lower()
        subdir, allowed = UPLOAD_TYPE_MAP.get(upload_type, ('file', None))
        logger.info(
            'upload_start type=%s size=%s name=%s user_id=%s',
            upload_type,
            getattr(file_obj, 'size', -1),
            getattr(file_obj, 'name', ''),
            getattr(request.user, 'id', None),
        )
        ok, url, err = upload_file_to_oss(file_obj, subdir=subdir, allowed_extensions=allowed)
        if not ok:
            logger.warning('upload_failed type=%s err=%s', upload_type, err)
            return Response({'detail': err or '上传失败', 'url': None}, status=status.HTTP_400_BAD_REQUEST)
        if not url:
            return Response({'detail': '上传成功但未生成 URL，请检查 OSS_ENDPOINT', 'url': None}, status=status.HTTP_400_BAD_REQUEST)
        logger.info('upload_ok type=%s url=%s', upload_type, url[:80])
        return Response({'url': url, 'detail': '上传成功'})
