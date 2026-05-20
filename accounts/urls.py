from django.urls import path
from . import views
from .auth import CustomTokenObtainPairView

urlpatterns = [
    path('register/', views.RegisterView.as_view()),
    path('login/', CustomTokenObtainPairView.as_view()),
    path('me/', views.UserMeView.as_view()),
    path('favorites/', views.UserFavoritesView.as_view()),
    path('users/generate/', views.AdminGenerateUsersView.as_view()),
    path('users/generate/history/', views.AdminGenerateUsersHistoryView.as_view()),
    path('users/generate/history/<uuid:batch_id>/', views.AdminGenerateUsersBatchDetailView.as_view()),
    path('users/generate/export/', views.AdminExportAccountsExcelView.as_view()),
]
