from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from accounts.views import dashboard_view
admin.site.site_header = 'ShadowShell Admin'
admin.site.site_title = 'ShadowShell'
admin.site.index_title = 'Boshqaruv Paneli'

urlpatterns = [
    path('Shadow-admin-panel/', admin.site.urls),
    path('', RedirectView.as_view(url='/accounts/dashboard/', permanent=False)),
    path('accounts/', include('accounts.urls')),
    path('terminal/', include('terminal.urls')),
    path('courses/', include('courses.urls')),
    path('billing/', include('billing.urls')),
    path('dashboard/', dashboard_view, name='dashboard'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)