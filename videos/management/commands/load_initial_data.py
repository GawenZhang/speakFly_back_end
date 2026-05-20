from django.core.management.base import BaseCommand
from videos.models import Video, Lesson


DEFAULT_VIDEOS = [
    {'episode': 'EP 1', 'title': '阳光明媚、天气阴沉怎么说?', 'date': '2024年8月19日', 'tag': '天气季节',
     'thumbnail': 'https://via.placeholder.com/300x200?text=EP1', 'youtuber': 'Sydney Serena', 'topic': '天气季节',
     'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ'},
    {'episode': 'EP 2', 'title': '开幕式门票、锁定坐席怎么说?', 'date': '2024年8月20日', 'tag': '运动健身',
     'thumbnail': 'https://via.placeholder.com/300x200?text=EP2', 'youtuber': 'Sydney Serena', 'topic': '运动健身',
     'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ'},
    {'episode': 'EP 3', 'title': '奶昔稀还是稠、味道满分怎么说?', 'date': '2024年8月21日', 'tag': '美食烹饪',
     'thumbnail': 'https://via.placeholder.com/300x200?text=EP3', 'youtuber': 'Sydney Serena', 'topic': '美食烹饪',
     'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ'},
    {'episode': 'EP 4', 'title': '大脑超负荷运转、琐事怎么说?', 'date': '2024年8月22日', 'tag': '日常感想',
     'thumbnail': 'https://via.placeholder.com/300x200?text=EP4', 'youtuber': 'Sydney Serena', 'topic': '日常感想',
     'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ'},
    {'episode': 'EP 5', 'title': '眼影防水、妆面持久怎么说?', 'date': '2024年8月23日', 'tag': '化妆服装',
     'thumbnail': 'https://via.placeholder.com/300x200?text=EP5', 'youtuber': 'Sydney Serena', 'topic': '化妆服装',
     'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ'},
    {'episode': 'EP 6', 'title': '待办清单、回到正轨怎么说?', 'date': '2024年8月24日', 'tag': '学习工作',
     'thumbnail': 'https://via.placeholder.com/300x200?text=EP6', 'youtuber': 'Sydney Serena', 'topic': '学习工作',
     'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ'},
    {'episode': 'EP 7', 'title': 'Week1复习篇', 'date': '2024年8月25日', 'tag': '复习篇',
     'thumbnail': 'https://via.placeholder.com/300x200?text=EP7', 'youtuber': 'Sydney Serena', 'topic': '复习篇',
     'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ'},
    {'episode': 'EP 8', 'title': '在衣柜里翻来覆去、穿搭怎么说?', 'date': '2024年8月26日', 'tag': '日常感想',
     'thumbnail': 'https://via.placeholder.com/300x200?text=EP8', 'youtuber': 'Sydney Serena', 'topic': '日常感想',
     'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ'},
]

DEFAULT_LESSON_1 = {
    'chinese_text': '我刚洗完澡,吹干头发。今天准备化一个淡妆,主要是用防晒霜,因为外面阳光明媚,这让我很开心。我可能跟你们说过无数次,阳光很影响我的心情。我来自明尼苏达州,冬天那里特别阴暗,就是非常黑而且阴沉沉的。后来我搬到了加利福尼亚,当时我觉得这里太棒了。为什么这里从来不会阴沉呢?',
    'english_text': "I just got out of the shower, I dried my hair. And I'm just going to put on a little makeup today, mostly like SPF, just because it's actually pretty sunny out which I'm happy. The sun, I feel like I've told you guys this a million times, really affects my mood. The winters in Minnesota where I'm from are especially dark, just like very dark and dreary. Then when I moved to California, I was like, this is amazing. Why is it never dreary here?",
    'phrases': [],
    'sentences': [],
    'highlight_phrases': [],
}


class Command(BaseCommand):
    help = 'Load initial video and lesson data'

    def handle(self, *args, **options):
        if Video.objects.exists():
            self.stdout.write('Data already exists, skip.')
            return
        for v in DEFAULT_VIDEOS:
            video = Video.objects.create(**v)
            if video.id == 1:
                Lesson.objects.create(video=video, **DEFAULT_LESSON_1)
        self.stdout.write(self.style.SUCCESS('Loaded %s videos and 1 lesson.' % len(DEFAULT_VIDEOS)))
