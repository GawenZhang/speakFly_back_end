from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'videos', views.VideoViewSet, basename='video')
router.register(r'lessons', views.LessonViewSet, basename='lesson')

urlpatterns = [
    path('', include(router.urls)),
    path('videos/next-episode/', views.NextEpisodeView.as_view()),
    path('upload/', views.UploadToOSSView.as_view()),
]
