from django.urls import path
from . import views

urlpatterns = [
    # Entry Vouchers
    path('entry/', views.entry_voucher_list, name='entry_voucher_list'),
    path('entry/create/', views.entry_voucher_create, name='entry_voucher_create'),
    path('entry/<int:pk>/', views.entry_voucher_detail, name='entry_voucher_detail'),
    path('entry/<int:pk>/confirm/', views.entry_voucher_confirm, name='entry_voucher_confirm'),
    
    # Exit Vouchers
    path('exit/', views.exit_voucher_list, name='exit_voucher_list'),
    path('exit/create/', views.exit_voucher_create, name='exit_voucher_create'),
    path('exit/<int:pk>/', views.exit_voucher_detail, name='exit_voucher_detail'),
    
    # Return Vouchers
    path('return/', views.return_voucher_list, name='return_voucher_list'),
    path('return/create/', views.return_voucher_create, name='return_voucher_create'),
    path('return/<int:pk>/', views.return_voucher_detail, name='return_voucher_detail'),
    
    # Disposal Vouchers
    path('disposal/', views.disposal_voucher_list, name='disposal_voucher_list'),
    path('disposal/create/', views.disposal_voucher_create, name='disposal_voucher_create'),
    path('disposal/<int:pk>/', views.disposal_voucher_detail, name='disposal_voucher_detail'),
]
