from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # 1. Kurslar ro'yxati
    path('', views.course_list_view, name='course_list'),
    
    # 🔥 2. ADMIN PANEL (Har doim sluglardan TEPADA turishi shart!)
    path('control-panel/dashboard/', views.custom_admin_dashboard, name='custom_admin'),
    
    # 3. Kurs tafsilotlari (slug bo'yicha)
    path('<slug:slug>/', views.course_detail_view, name='course_detail'),
    
    # 4. Topshiriq sahifasi
    path('<slug:course_slug>/<slug:quest_slug>/', views.quest_detail_view, name='quest_detail'),
    
    # 5. API endpoint
    path('api/verify-command/', views.verify_command_api, name='verify_command'),
]