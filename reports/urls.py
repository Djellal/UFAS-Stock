from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_index, name='reports_index'),
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('inventory/pdf/', views.inventory_report_pdf, name='inventory_report_pdf'),
    path('inventory/excel/', views.inventory_report_excel, name='inventory_report_excel'),
    path('movements/', views.movements_report, name='movements_report'),
    path('disposed/', views.disposed_report, name='disposed_report'),
    path('api/statistics/', views.statistics_api, name='statistics_api'),
    path('voucher/<str:voucher_type>/<int:pk>/pdf/', views.voucher_pdf, name='voucher_pdf'),
]
