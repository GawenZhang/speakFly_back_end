from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from videos.models import UserFavorite
from videos.serializers import VideoSerializer

from .models import AccountGenerationBatch, GeneratedAccountRecord
from .excel_export import build_accounts_excel
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    ProfileUpdateSerializer,
    GenerateUsersSerializer,
)
from .user_utils import generate_random_username, generate_random_password


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if not getattr(settings, 'ALLOW_PUBLIC_REGISTER', False):
            return Response(
                {'detail': '暂未开放自助注册，请联系管理员获取学习账号'},
                status=status.HTTP_403_FORBIDDEN
            )
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)


class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        ser = ProfileUpdateSerializer(
            data=request.data,
            context={'request': request},
            partial=True
        )
        ser.is_valid(raise_exception=True)
        user = ser.update(request.user, ser.validated_data)
        return Response({
            'user': UserSerializer(user).data,
            'message': '账号信息已更新'
        })


class UserFavoritesView(APIView):
    """当前用户收藏的课程列表"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        favs = UserFavorite.objects.filter(user=request.user).select_related('video')
        videos = [f.video for f in favs]
        data = VideoSerializer(videos, many=True, context={'request': request}).data
        for item in data:
            item['isFavorite'] = True
        return Response(data)


class AdminGenerateUsersView(APIView):
    """管理员批量生成客户账号（用户名+随机密码），并写入留档"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        ser = GenerateUsersSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        count = ser.validated_data['count']
        prefix = ser.validated_data.get('prefix') or 'sf'
        pwd_len = ser.validated_data.get('passwordLength') or 10
        note = ser.validated_data.get('note') or ''

        batch = AccountGenerationBatch.objects.create(
            created_by=request.user,
            count=0,
            prefix=prefix,
            password_length=pwd_len,
            note=note,
        )

        created = []
        records = []
        for _ in range(count):
            username = generate_random_username(prefix=prefix)
            password = generate_random_password(length=pwd_len)
            user = User.objects.create_user(username=username, email='', password=password)
            records.append(GeneratedAccountRecord(
                batch=batch,
                username=username,
                password=password,
                user=user,
            ))
            created.append({'username': username, 'password': password})

        GeneratedAccountRecord.objects.bulk_create(records)
        batch.count = len(created)
        batch.save(update_fields=['count'])

        return Response({
            'batchId': str(batch.batch_id),
            'count': len(created),
            'users': created,
            'message': f'已成功生成 {len(created)} 个账号并已留档，可导出 Excel 分发给客户',
        }, status=status.HTTP_201_CREATED)


class AdminGenerateUsersHistoryView(APIView):
    """账号生成批次历史（留档列表）"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        limit = min(int(request.query_params.get('limit', 30)), 100)
        batches = AccountGenerationBatch.objects.select_related('created_by').order_by('-created_at')[:limit]
        data = []
        for b in batches:
            data.append({
                'batchId': str(b.batch_id),
                'count': b.count,
                'prefix': b.prefix,
                'passwordLength': b.password_length,
                'note': b.note,
                'createdAt': b.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'createdBy': b.created_by.username if b.created_by else '',
            })
        return Response(data)


class AdminGenerateUsersBatchDetailView(APIView):
    """某批次下的账号明细"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, batch_id):
        try:
            batch = AccountGenerationBatch.objects.get(batch_id=batch_id)
        except AccountGenerationBatch.DoesNotExist:
            return Response({'detail': '批次不存在'}, status=status.HTTP_404_NOT_FOUND)
        accounts = batch.accounts.all()
        return Response({
            'batchId': str(batch.batch_id),
            'createdAt': batch.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'createdBy': batch.created_by.username if batch.created_by else '',
            'note': batch.note,
            'users': [{'username': a.username, 'password': a.password} for a in accounts],
        })


class AdminExportAccountsExcelView(APIView):
    """导出账号留档为 Excel。query: batchId=uuid 导出单批次；all=1 导出全部"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        batch_id = request.query_params.get('batchId')
        batch_ids_raw = request.query_params.get('batchIds', '')
        export_all = request.query_params.get('all') in ('1', 'true', 'yes')

        qs = GeneratedAccountRecord.objects.select_related('batch', 'batch__created_by').order_by(
            '-batch__created_at', 'id'
        )
        if export_all:
            filename = 'speakfly_accounts_all.xlsx'
        elif batch_ids_raw:
            batch_ids = [x.strip() for x in batch_ids_raw.split(',') if x.strip()]
            qs = qs.filter(batch__batch_id__in=batch_ids)
            if not qs.exists():
                return Response({'detail': '所选批次无记录'}, status=status.HTTP_404_NOT_FOUND)
            filename = f'speakfly_accounts_{len(batch_ids)}batches.xlsx'
        elif batch_id:
            qs = qs.filter(batch__batch_id=batch_id)
            if not qs.exists():
                return Response({'detail': '该批次无记录'}, status=status.HTTP_404_NOT_FOUND)
            filename = f'speakfly_accounts_{str(batch_id)[:8]}.xlsx'
        else:
            return Response({'detail': '请指定 batchId、batchIds 或 all=1'}, status=status.HTTP_400_BAD_REQUEST)

        buffer = build_accounts_excel(qs)
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
