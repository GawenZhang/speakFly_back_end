from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'videos', views.VideoViewSet, basename='video')
router.register(r'lessons', views.LessonViewSet, basename='lesson')

urlpatterns = [
    # 固定路径须放在 router 之前，避免被 videos/<pk>/ 误匹配
    path('videos/next-episode/', views.NextEpisodeView.as_view()),
    path('upload/', views.UploadToOSSView.as_view()),
    path('', include(router.urls)),
]
