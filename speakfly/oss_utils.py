"""
阿里云 OSS 上传工具。图片、视频、音频上传到 OSS，数据库只存 URL。
"""
import os
import uuid
from django.conf import settings


def _oss_configured():
    return bool(
        getattr(settings, 'OSS_ACCESS_KEY_ID', None)
        and getattr(settings, 'OSS_ACCESS_KEY_SECRET', None)
        and getattr(settings, 'OSS_BUCKET_NAME', None)
        and getattr(settings, 'OSS_ENDPOINT', None)
    )


def get_oss_bucket():
    """获取 OSS Bucket 实例，未配置时返回 None。"""
    if not _oss_configured():
        return None
    try:
        import oss2
        auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        return oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)
    except Exception:
        return None


def _ensure_https_url(url):
    """OSS 外链与预签名 URL 统一使用 HTTPS。"""
    if url and url.startswith('http://'):
        return 'https://' + url[7:]
    return url


def get_public_url(object_key):
    """根据 object_key 返回可访问的 URL。"""
    domain = getattr(settings, 'OSS_BUCKET_DOMAIN', '').strip()
    if domain:
        domain = domain.rstrip('/')
        return f"https://{domain}/{object_key}" if domain.startswith('http') else f"https://{domain}/{object_key}"
    bucket_name = getattr(settings, 'OSS_BUCKET_NAME', '')
    endpoint = getattr(settings, 'OSS_ENDPOINT', '').strip()
    if not endpoint:
        return ''
    if not endpoint.startswith('http'):
        endpoint = f"https://{endpoint}"
    base = endpoint.replace('https://', '').replace('http://', '')
    return _ensure_https_url(f"https://{bucket_name}.{base}/{object_key}")


def create_presigned_upload(filename, subdir='', allowed_extensions=None, content_type='', expires=3600):
    """
    生成浏览器直传 OSS 的预签名 PUT URL，绕过后端/Nginx 体积限制。
    :return: (success, upload_url, public_url, error)
    """
    bucket = get_oss_bucket()
    if not bucket:
        return False, None, None, 'OSS 未配置，请在环境变量中设置 OSS_ACCESS_KEY_ID、OSS_ACCESS_KEY_SECRET、OSS_BUCKET_NAME、OSS_ENDPOINT'

    ext = ''
    if filename:
        ext = os.path.splitext(filename)[1].lower()
    if allowed_extensions and ext and ext.lstrip('.') not in {e.lstrip('.') for e in allowed_extensions}:
        return False, None, None, f'不允许的文件类型，允许: {allowed_extensions}'

    base_dir = (getattr(settings, 'OSS_UPLOAD_DIR', 'speakfly') or 'speakfly').strip().strip('/')
    object_key = f"{base_dir}/{subdir}/{uuid.uuid4().hex}{ext}"
    ct = (content_type or 'application/octet-stream').split(';')[0].strip()
    try:
        # 预签名时绑定 Content-Type，浏览器 PUT 必须发送相同值
        upload_url = _ensure_https_url(
            bucket.sign_url('PUT', object_key, expires, headers={'Content-Type': ct})
        )
        public_url = get_public_url(object_key)
        if not public_url:
            return False, None, None, '无法生成文件访问 URL，请检查 OSS_ENDPOINT 配置'
        return True, upload_url, public_url, None
    except Exception as e:
        return False, None, None, str(e)


def upload_file_to_oss(file, subdir='', allowed_extensions=None):
    """
    将文件上传到 OSS。
    :param file: Django UploadedFile 或类文件对象，需有 name、read()
    :param subdir: 子目录，如 image / video / audio
    :param allowed_extensions: 允许的扩展名集合，如 {'jpg','png','mp4'}，None 表示不限制
    :return: (success: bool, url: str or None, error: str or None)
    """
    bucket = get_oss_bucket()
    if not bucket:
        return False, None, 'OSS 未配置，请在环境变量中设置 OSS_ACCESS_KEY_ID、OSS_ACCESS_KEY_SECRET、OSS_BUCKET_NAME、OSS_ENDPOINT'

    base_dir = (getattr(settings, 'OSS_UPLOAD_DIR', 'speakfly') or 'speakfly').strip().strip('/')
    ext = ''
    if hasattr(file, 'name') and file.name:
        ext = os.path.splitext(file.name)[1].lower()
    if allowed_extensions and ext and ext.lstrip('.') not in {e.lstrip('.') for e in allowed_extensions}:
        return False, None, f'不允许的文件类型，允许: {allowed_extensions}'

    object_key = f"{base_dir}/{subdir}/{uuid.uuid4().hex}{ext}"
    try:
        # 流式上传，避免大视频整文件读入内存
        if hasattr(file, 'seek'):
            file.seek(0)
        bucket.put_object(object_key, file)
        url = get_public_url(object_key)
        return True, url, None
    except Exception as e:
        return False, None, str(e)
