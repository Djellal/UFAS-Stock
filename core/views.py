"""
Core views - Dashboard and Authentication
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta

from django.db import models
from inventory.models import Product, InventoryItem, Category, StockMovement
from transactions.models import EntryVoucher, ExitVoucher, ReturnVoucher, DisposalVoucher


def login_view(request):
    """تسجيل الدخول"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'مرحباً {user.get_full_name() or user.username}')
            return redirect('dashboard')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
    
    return render(request, 'core/login.html')


def logout_view(request):
    """تسجيل الخروج"""
    logout(request)
    messages.info(request, 'تم تسجيل الخروج بنجاح')
    return redirect('login')


@login_required
def dashboard(request):
    """لوحة التحكم الرئيسية"""
    user = request.user
    tenant = user.tenant
    
    # Base querysets based on user role
    if user.is_super_admin:
        products = Product.objects.all()
        items = InventoryItem.objects.all()
        entry_vouchers = EntryVoucher.objects.all()
        exit_vouchers = ExitVoucher.objects.all()
        return_vouchers = ReturnVoucher.objects.all()
        disposal_vouchers = DisposalVoucher.objects.all()
    else:
        products = Product.objects.filter(tenant=tenant)
        items = InventoryItem.objects.filter(tenant=tenant)
        entry_vouchers = EntryVoucher.objects.filter(tenant=tenant)
        exit_vouchers = ExitVoucher.objects.filter(tenant=tenant)
        return_vouchers = ReturnVoucher.objects.filter(tenant=tenant)
        disposal_vouchers = DisposalVoucher.objects.filter(tenant=tenant)
    
    # Statistics
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    stats = {
        'total_products': products.count(),
        'total_assets': items.count(),
        'available_assets': items.filter(status='available').count(),
        'assigned_assets': items.filter(status='assigned').count(),
        'disposed_assets': items.filter(status='disposed').count(),
        'total_asset_value': items.aggregate(total=Sum('purchase_price'))['total'] or 0,
        
        # Voucher counts
        'entry_vouchers_count': entry_vouchers.filter(date__gte=last_30_days).count(),
        'exit_vouchers_count': exit_vouchers.filter(date__gte=last_30_days).count(),
        'return_vouchers_count': return_vouchers.filter(date__gte=last_30_days).count(),
        'disposal_vouchers_count': disposal_vouchers.filter(date__gte=last_30_days).count(),
    }
    
    # Assets by status for pie chart
    assets_by_status = items.values('status').annotate(count=Count('id'))
    
    # Assets by category for bar chart
    assets_by_category = items.values('product__category__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Recent activities
    recent_entries = entry_vouchers.order_by('-created_at')[:5]
    recent_exits = exit_vouchers.order_by('-created_at')[:5]
    
    # Low stock products (consumables)
    low_stock = products.filter(
        nature='consumable'
    ).annotate(
        current_stock=Sum('stock_movements__quantity')
    ).filter(
        current_stock__lte=models.F('min_stock')
    )[:5]
    
    context = {
        'stats': stats,
        'assets_by_status': list(assets_by_status),
        'assets_by_category': list(assets_by_category),
        'recent_entries': recent_entries,
        'recent_exits': recent_exits,
        'low_stock': low_stock,
    }
    
    return render(request, 'core/dashboard.html', context)


@login_required
def profile(request):
    """صفحة الملف الشخصي"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.phone = request.POST.get('phone', '')
        user.save()
        messages.success(request, 'تم تحديث الملف الشخصي بنجاح')
        return redirect('profile')
    
    return render(request, 'core/profile.html')


@login_required
def change_password(request):
    """تغيير كلمة المرور"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(old_password):
            messages.error(request, 'كلمة المرور الحالية غير صحيحة')
        elif new_password != confirm_password:
            messages.error(request, 'كلمة المرور الجديدة غير متطابقة')
        elif len(new_password) < 8:
            messages.error(request, 'كلمة المرور يجب أن تكون 8 أحرف على الأقل')
        else:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, 'تم تغيير كلمة المرور بنجاح')
            return redirect('login')
    
    return render(request, 'core/change_password.html')
