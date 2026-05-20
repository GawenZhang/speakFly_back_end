from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6, validators=[validate_password])
    confirmPassword = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirmPassword']

    def validate_username(self, value):
        if len(value) < 3:
            raise serializers.ValidationError('用户名长度不能少于3位')
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('用户名已存在')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('confirmPassword'):
            raise serializers.ValidationError({'confirmPassword': '两次输入的密码不一致'})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    isAdmin = serializers.BooleanField(source='is_staff', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'isAdmin']


class ProfileUpdateSerializer(serializers.Serializer):
    """用户修改账号与密码"""
    username = serializers.CharField(required=False, min_length=3, max_length=150)
    oldPassword = serializers.CharField(required=False, write_only=True)
    newPassword = serializers.CharField(required=False, write_only=True, min_length=6)
    confirmPassword = serializers.CharField(required=False, write_only=True)

    def validate_username(self, value):
        user = self.context['request'].user
        if User.objects.filter(username=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError('该用户名已被占用')
        return value

    def validate(self, attrs):
        new_password = attrs.get('newPassword')
        old_password = attrs.get('oldPassword')
        confirm = attrs.pop('confirmPassword', None)

        user = self.context['request'].user
        if new_password:
            if not old_password:
                raise serializers.ValidationError({'oldPassword': '修改密码请先填写当前密码'})
            if not user.check_password(old_password):
                raise serializers.ValidationError({'oldPassword': '当前密码不正确'})
            if confirm is not None and new_password != confirm:
                raise serializers.ValidationError({'confirmPassword': '两次输入的新密码不一致'})
            validate_password(new_password, user)
        elif old_password:
            raise serializers.ValidationError({'newPassword': '请填写新密码'})

        if not attrs.get('username') and not new_password:
            raise serializers.ValidationError('请至少修改用户名或密码中的一项')

        return attrs

    def update(self, user, validated_data):
        username = validated_data.get('username')
        if username and username != user.username:
            user.username = username

        new_password = validated_data.get('newPassword')
        if new_password:
            user.set_password(new_password)

        user.save()
        return user


class GenerateUsersSerializer(serializers.Serializer):
    count = serializers.IntegerField(min_value=1, max_value=50, default=1)
    prefix = serializers.CharField(max_length=20, default='sf', required=False)
    passwordLength = serializers.IntegerField(min_value=6, max_value=32, default=10, required=False)
    note = serializers.CharField(max_length=200, required=False, allow_blank=True)
