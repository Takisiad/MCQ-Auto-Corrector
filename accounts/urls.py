from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    path('login/',    TokenObtainPairView.as_view(), name='login'),
    path('refresh/',  TokenRefreshView.as_view(),    name='refresh'),
    path('register/', views.register,                name='register'),
    path('profile/',  views.profile,                 name='profile'),
    path('users/',    views.all_users,               name='all_users'),
]