"""
URL configuration for UFAS-Stock project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('inventory/', include('inventory.urls')),
    path('transactions/', include('transactions.urls')),
    path('reports/', include('reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

# Customize admin site
admin.site.site_header = 'نظام إدارة المخزون - جامعة فرحات عباس سطيف 1'
admin.site.site_title = 'UFAS-Stock'
admin.site.index_title = 'لوحة الإدارة'
