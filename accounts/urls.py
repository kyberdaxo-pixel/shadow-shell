from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('shadow-admin/', views.shadow_admin_dashboard, name='shadow_admin_dashboard'),
    path('cyber-terminal/', views.shadow_terminal_view, name='cyber_terminal'),
]