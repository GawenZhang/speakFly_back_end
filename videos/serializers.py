from rest_framework import serializers
from .models import Video, Lesson, UserFavorite


class VideoSerializer(serializers.ModelSerializer):
    """视频列表/详情序列化（含前端字段名）"""
    videoUrl = serializers.URLField(source='video_url', read_only=True)
    isFavorite = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            'id', 'episode', 'title', 'date', 'tag', 'thumbnail',
            'youtuber', 'topic', 'videoUrl', 'isFavorite'
        ]

    def get_isFavorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserFavorite.objects.filter(user=request.user, video=obj).exists()
        return False


class VideoCreateUpdateSerializer(serializers.ModelSerializer):
    """创建/更新视频（接受前端 camelCase）"""
    videoUrl = serializers.URLField(source='video_url', required=False, allow_blank=True)

    class Meta:
        model = Video
        fields = [
            'episode', 'title', 'tag', 'date', 'youtuber', 'topic',
            'thumbnail', 'videoUrl'
        ]


class LessonSerializer(serializers.ModelSerializer):
    """课程详情序列化（前端期望：videoId, chineseText, englishText, phrases, sentences, highlightPhrases）"""
    videoId = serializers.IntegerField(source='video_id', read_only=True)
    chineseText = serializers.CharField(source='chinese_text', required=False, allow_blank=True)
    englishText = serializers.CharField(source='english_text', required=False, allow_blank=True)
    highlightPhrases = serializers.JSONField(source='highlight_phrases', required=False, default=list)

    class Meta:
        model = Lesson
        fields = ['videoId', 'chineseText', 'englishText', 'phrases', 'sentences', 'highlightPhrases']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['videoId'] = instance.video_id
        data['chineseText'] = instance.chinese_text
        data['englishText'] = instance.english_text
        data['phrases'] = instance.phrases or []
        data['sentences'] = instance.sentences or []
        data['highlightPhrases'] = instance.highlight_phrases or []
        return data

    def to_internal_value(self, data):
        if 'chineseText' in data:
            data['chinese_text'] = data.pop('chineseText')
        if 'englishText' in data:
            data['english_text'] = data.pop('englishText')
        if 'highlightPhrases' in data:
            data['highlight_phrases'] = data.pop('highlightPhrases')
        return super().to_internal_value(data)


class LessonWriteSerializer(serializers.ModelSerializer):
    """保存课程详情（接受前端 camelCase）"""
    videoId = serializers.IntegerField(write_only=True)
    chineseText = serializers.CharField(source='chinese_text', required=False, allow_blank=True)
    englishText = serializers.CharField(source='english_text', required=False, allow_blank=True)
    highlightPhrases = serializers.JSONField(source='highlight_phrases', required=False, default=list)

    class Meta:
        model = Lesson
        fields = ['videoId', 'chineseText', 'englishText', 'phrases', 'sentences', 'highlightPhrases']

    def create(self, validated_data):
        video_id = validated_data.pop('videoId')
        from .models import Video
        video = Video.objects.get(pk=video_id)
        validated_data['video'] = video
        if 'chinese_text' not in validated_data:
            validated_data['chinese_text'] = ''
        if 'english_text' not in validated_data:
            validated_data['english_text'] = ''
        if 'highlight_phrases' not in validated_data:
            validated_data['highlight_phrases'] = []
        return Lesson.objects.create(**validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('videoId', None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance
