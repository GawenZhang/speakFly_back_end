import secrets
import string

from django.contrib.auth.models import User


def generate_random_username(prefix='sf'):
    """生成唯一用户名，如 sf_a1b2c3d4"""
    for _ in range(20):
        suffix = secrets.token_hex(4)
        username = f'{prefix}_{suffix}'
        if not User.objects.filter(username=username).exists():
            return username
    raise ValueError('无法生成唯一用户名，请重试')


def generate_random_password(length=10):
    """生成随机密码（字母+数字）"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))
