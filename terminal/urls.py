from django.urls import path
from . import views

app_name = 'terminal'

urlpatterns = [
    path('lab/<slug:course_slug>/<slug:quest_slug>/', views.lab_view, name='lab'),
    path('execute/', views.execute_code_view, name='execute'),
]