from django.db import models
from django.conf import settings


class Video(models.Model):
    """课程视频（列表项）"""
    episode = models.CharField('期数', max_length=20)  # EP 1, EP 2
    title = models.CharField('标题', max_length=200)
    tag = models.CharField('标签', max_length=50)
    date = models.CharField('日期', max_length=30)  # 2024年8月19日
    youtuber = models.CharField('博主', max_length=100)
    topic = models.CharField('话题', max_length=100, blank=True)
    thumbnail = models.URLField('缩略图URL', max_length=500)
    video_url = models.URLField('视频URL', max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']
        verbose_name = '视频课程'
        verbose_name_plural = '视频课程'

    def __str__(self):
        return f'{self.episode} {self.title}'


class Lesson(models.Model):
    """课程详情（与视频一对一）"""
    video = models.OneToOneField(Video, on_delete=models.CASCADE, related_name='lesson')
    chinese_text = models.TextField('中文文本', blank=True)
    english_text = models.TextField('英文文本', blank=True)
    # JSON: phrases, sentences, highlight_phrases
    phrases = models.JSONField('短语列表', default=list, blank=True)
    sentences = models.JSONField('单句练习', default=list, blank=True)
    highlight_phrases = models.JSONField('高亮短语配置', default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '课程详情'
        verbose_name_plural = '课程详情'

    def __str__(self):
        return f'Lesson of {self.video.episode}'


class UserFavorite(models.Model):
    """用户收藏的课程"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_videos')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'video']
        verbose_name = '用户收藏'
        verbose_name_plural = '用户收藏'

    def __str__(self):
        return f'{self.user.username} -> {self.video.episode}'
