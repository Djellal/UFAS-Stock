"""
Transaction views - Vouchers management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction

from .models import (
    EntryVoucher, EntryVoucherItem, EntryVoucherAsset,
    ExitVoucher, ExitVoucherItem, ExitVoucherAsset,
    ReturnVoucher, ReturnVoucherItem, ReturnVoucherAsset,
    DisposalVoucher, DisposalVoucherItem, DisposalVoucherAsset,
)
from .forms import EntryVoucherForm, ExitVoucherForm, ReturnVoucherForm, DisposalVoucherForm
from inventory.models import Product, InventoryItem, StockMovement, Department, Supplier


def generate_unique_inventory_number(tenant, product_code):
    """Generate a unique inventory number that doesn't exist for the tenant"""
    import random
    import string
    while True:
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        inv_num = f"INV-{product_code}-{timezone.now().strftime('%Y%m%d')}-{random_suffix}"
        if not InventoryItem.objects.filter(inventory_number=inv_num, tenant=tenant).exists():
            return inv_num


def get_tenant_queryset(request, model):
    """Get queryset filtered by tenant"""
    if request.user.is_super_admin:
        return model.objects.all()
    return model.objects.filter(tenant=request.user.tenant)


def generate_voucher_number(prefix, tenant):
    """Generate unique voucher number"""
    year = timezone.now().year
    return f"{prefix}-{tenant.code}-{year}-{timezone.now().strftime('%m%d%H%M%S')}"


def update_product_stock(product, quantity_change):
    """Update product stock_quantity by the given amount"""
    product.stock_quantity = max(0, product.stock_quantity + quantity_change)
    product.save(update_fields=['stock_quantity'])


def get_product_total_quantity(product, items):
    """Calculate total quantity from voucher items for a product"""
    return sum(item.quantity for item in items if item.product.id == product.id)


# ============== Entry Vouchers ==============

@login_required
def entry_voucher_list(request):
    """قائمة وصلات الدخول"""
    vouchers = get_tenant_queryset(request, EntryVoucher)
    
    search = request.GET.get('search', '')
    if search:
        vouchers = vouchers.filter(
            Q(voucher_number__icontains=search) |
            Q(supplier__name__icontains=search)
        )
    
    status = request.GET.get('status')
    if status:
        vouchers = vouchers.filter(status=status)
    
    paginator = Paginator(vouchers.select_related('supplier', 'created_by'), 20)
    page = request.GET.get('page', 1)
    vouchers = paginator.get_page(page)
    
    return render(request, 'transactions/entry_voucher_list.html', {
        'vouchers': vouchers,
        'search': search,
    })


@login_required
def entry_voucher_create(request):
    """إنشاء وصل دخول جديد"""
    tenant = request.user.tenant
    
    if request.method == 'POST':
        form = EntryVoucherForm(request.POST, tenant=tenant)
        if form.is_valid():
            with transaction.atomic():
                voucher = form.save(commit=False)
                voucher.tenant = tenant
                voucher.created_by = request.user
                voucher.voucher_number = generate_voucher_number('ENT', tenant)
                voucher.save()
                
                # Process items from formset data
                items_data = request.POST.getlist('product_id')
                quantities = request.POST.getlist('quantity')
                unit_prices = request.POST.getlist('unit_price')
                
                for i, product_id in enumerate(items_data):
                    if product_id:
                        product = Product.objects.get(id=product_id)
                        quantity = int(quantities[i]) if quantities[i] else 1
                        unit_price = float(unit_prices[i]) if unit_prices[i] else 0
                        
                        item = EntryVoucherItem.objects.create(
                            voucher=voucher,
                            product=product,
                            quantity=quantity,
                            unit_price=unit_price
                        )
                        
                        # Create stock movement for consumables
                        if product.nature == 'consumable':
                            StockMovement.objects.create(
                                product=product,
                                movement_type='in',
                                quantity=quantity,
                                unit_price=unit_price,
                                reference=voucher.voucher_number,
                                tenant=tenant,
                                created_by=request.user
                            )
                        
                        # Handle assets (inventory items)
                        if product.nature == 'asset':
                            inventory_numbers = request.POST.getlist(f'inventory_number_{i}')
                            serial_numbers = request.POST.getlist(f'serial_number_{i}')
                            
                            # Track used inventory numbers in this form submission
                            used_inventory_numbers = set()
                            
                            for j in range(quantity):
                                inv_num = inventory_numbers[j] if j < len(inventory_numbers) else generate_unique_inventory_number(tenant, product.code)
                                
                                # Skip if already used in this form
                                while inv_num in used_inventory_numbers:
                                    inv_num = generate_unique_inventory_number(tenant, product.code)
                                
                                used_inventory_numbers.add(inv_num)
                                ser_num = serial_numbers[j] if j < len(serial_numbers) else ''
                                
                                inv_item = InventoryItem.objects.create(
                                    product=product,
                                    inventory_number=inv_num,
                                    serial_number=ser_num,
                                    status='available',
                                    condition='new',
                                    purchase_date=voucher.date,
                                    purchase_price=unit_price,
                                    tenant=tenant
                                )
                                
                                EntryVoucherAsset.objects.create(
                                    voucher_item=item,
                                    inventory_item=inv_item
                                )
                
                messages.success(request, f'تم إنشاء وصل الدخول رقم {voucher.voucher_number} بنجاح')
                return redirect('entry_voucher_detail', pk=voucher.pk)
    else:
        form = EntryVoucherForm(tenant=tenant, initial={'date': timezone.now().date()})
    
    products = Product.objects.filter(tenant=tenant, is_active=True)
    
    return render(request, 'transactions/entry_voucher_form.html', {
        'form': form,
        'title': 'إنشاء وصل دخول جديد',
        'products': products,
    })


@login_required
def entry_voucher_detail(request, pk):
    """تفاصيل وصل الدخول"""
    voucher = get_object_or_404(EntryVoucher, pk=pk)
    
    if not request.user.is_super_admin and voucher.tenant != request.user.tenant:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذا الوصل')
        return redirect('entry_voucher_list')
    
    items = voucher.items.select_related('product').prefetch_related('assets__inventory_item')
    
    return render(request, 'transactions/entry_voucher_detail.html', {
        'voucher': voucher,
        'items': items,
    })


@login_required
def entry_voucher_confirm(request, pk):
    """تأكيد وصل الدخول"""
    voucher = get_object_or_404(EntryVoucher, pk=pk)
    
    if voucher.status != 'draft':
        messages.error(request, 'لا يمكن تأكيد هذا الوصل')
        return redirect('entry_voucher_detail', pk=pk)
    
    with transaction.atomic():
        # Update stock quantities for all products
        for item in voucher.items.all():
            if item.product.nature == 'consumable':
                update_product_stock(item.product, item.quantity)
        
        voucher.status = 'confirmed'
        voucher.confirmed_by = request.user
        voucher.save()
    
    messages.success(request, 'تم تأكيد وصل الدخول بنجاح')
    return redirect('entry_voucher_detail', pk=pk)


# ============== Exit Vouchers ==============

@login_required
def exit_voucher_list(request):
    """قائمة وصلات الإخراج"""
    vouchers = get_tenant_queryset(request, ExitVoucher)
    
    search = request.GET.get('search', '')
    if search:
        vouchers = vouchers.filter(
            Q(voucher_number__icontains=search) |
            Q(department__name__icontains=search) |
            Q(recipient_name__icontains=search)
        )
    
    paginator = Paginator(vouchers.select_related('department', 'created_by'), 20)
    page = request.GET.get('page', 1)
    vouchers = paginator.get_page(page)
    
    return render(request, 'transactions/exit_voucher_list.html', {
        'vouchers': vouchers,
        'search': search,
    })


@login_required
def exit_voucher_create(request):
    """إنشاء وصل إخراج جديد"""
    tenant = request.user.tenant
    
    if request.method == 'POST':
        form = ExitVoucherForm(request.POST, tenant=tenant)
        if form.is_valid():
            with transaction.atomic():
                voucher = form.save(commit=False)
                voucher.tenant = tenant
                voucher.created_by = request.user
                voucher.voucher_number = generate_voucher_number('EXT', tenant)
                voucher.save()
                
                # Process items
                items_data = request.POST.getlist('product_id')
                quantities = request.POST.getlist('quantity')
                
                for i, product_id in enumerate(items_data):
                    if product_id:
                        product = Product.objects.get(id=product_id)
                        quantity = int(quantities[i]) if quantities[i] else 1
                        
                        item = ExitVoucherItem.objects.create(
                            voucher=voucher,
                            product=product,
                            quantity=quantity
                        )
                        
                        if product.nature == 'consumable':
                            StockMovement.objects.create(
                                product=product,
                                movement_type='out',
                                quantity=-quantity,
                                reference=voucher.voucher_number,
                                tenant=tenant,
                                created_by=request.user
                            )
                        
                        # Handle assets
                        if product.nature == 'asset':
                            asset_ids = request.POST.getlist(f'asset_id_{i}')
                            for asset_id in asset_ids:
                                if asset_id:
                                    inv_item = InventoryItem.objects.get(id=asset_id)
                                    inv_item.status = 'assigned'
                                    inv_item.assigned_to = voucher.department
                                    inv_item.save()
                                    
                                    ExitVoucherAsset.objects.create(
                                        voucher_item=item,
                                        inventory_item=inv_item
                                    )
                
                messages.success(request, f'تم إنشاء وصل الإخراج رقم {voucher.voucher_number} بنجاح')
                return redirect('exit_voucher_detail', pk=voucher.pk)
    else:
        form = ExitVoucherForm(tenant=tenant, initial={'date': timezone.now().date()})
    
    products = Product.objects.filter(tenant=tenant, is_active=True)
    departments = Department.objects.filter(tenant=tenant, is_active=True)
    
    return render(request, 'transactions/exit_voucher_form.html', {
        'form': form,
        'title': 'إنشاء وصل إخراج جديد',
        'products': products,
        'departments': departments,
    })


@login_required
def exit_voucher_detail(request, pk):
    """تفاصيل وصل الإخراج"""
    voucher = get_object_or_404(ExitVoucher, pk=pk)
    
    if not request.user.is_super_admin and voucher.tenant != request.user.tenant:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذا الوصل')
        return redirect('exit_voucher_list')
    
    items = voucher.items.select_related('product').prefetch_related('assets__inventory_item')
    
    return render(request, 'transactions/exit_voucher_detail.html', {
        'voucher': voucher,
        'items': items,
    })


@login_required
def exit_voucher_confirm(request, pk):
    """تأكيد وصل الإخراج"""
    voucher = get_object_or_404(ExitVoucher, pk=pk)
    
    if voucher.status != 'draft':
        messages.error(request, 'لا يمكن تأكيد هذا الوصل')
        return redirect('exit_voucher_detail', pk=pk)
    
    with transaction.atomic():
        # Check sufficient stock for consumables
        for item in voucher.items.all():
            if item.product.nature == 'consumable':
                if item.product.stock_quantity < item.quantity:
                    messages.error(request, f'لا يوجد مخزون كافٍ للمنتج {item.product.name}')
                    return redirect('exit_voucher_detail', pk=pk)
        
        # Update stock quantities for all products
        for item in voucher.items.all():
            if item.product.nature == 'consumable':
                update_product_stock(item.product, -item.quantity)
        
        voucher.status = 'confirmed'
        voucher.confirmed_by = request.user
        voucher.save()
    
    messages.success(request, 'تم تأكيد وصل الإخراج بنجاح')
    return redirect('exit_voucher_detail', pk=pk)


# ============== Return Vouchers ==============

@login_required
def return_voucher_list(request):
    """قائمة وصلات الإرجاع"""
    vouchers = get_tenant_queryset(request, ReturnVoucher)
    
    search = request.GET.get('search', '')
    if search:
        vouchers = vouchers.filter(
            Q(voucher_number__icontains=search) |
            Q(department__name__icontains=search)
        )
    
    paginator = Paginator(vouchers.select_related('department', 'created_by'), 20)
    page = request.GET.get('page', 1)
    vouchers = paginator.get_page(page)
    
    return render(request, 'transactions/return_voucher_list.html', {
        'vouchers': vouchers,
        'search': search,
    })


@login_required
def return_voucher_create(request):
    """إنشاء وصل إرجاع جديد"""
    tenant = request.user.tenant
    
    if request.method == 'POST':
        form = ReturnVoucherForm(request.POST, tenant=tenant)
        if form.is_valid():
            with transaction.atomic():
                voucher = form.save(commit=False)
                voucher.tenant = tenant
                voucher.created_by = request.user
                voucher.voucher_number = generate_voucher_number('RET', tenant)
                voucher.save()
                
                # Process items
                items_data = request.POST.getlist('product_id')
                quantities = request.POST.getlist('quantity')
                conditions = request.POST.getlist('condition')
                
                for i, product_id in enumerate(items_data):
                    if product_id:
                        product = Product.objects.get(id=product_id)
                        quantity = int(quantities[i]) if quantities[i] else 1
                        condition = conditions[i] if i < len(conditions) else 'good'
                        
                        item = ReturnVoucherItem.objects.create(
                            voucher=voucher,
                            product=product,
                            quantity=quantity,
                            condition=condition
                        )
                        
                        if product.nature == 'consumable':
                            StockMovement.objects.create(
                                product=product,
                                movement_type='return',
                                quantity=quantity,
                                reference=voucher.voucher_number,
                                tenant=tenant,
                                created_by=request.user
                            )
                        
                        # Handle assets
                        if product.nature == 'asset':
                            asset_ids = request.POST.getlist(f'asset_id_{i}')
                            for asset_id in asset_ids:
                                if asset_id:
                                    inv_item = InventoryItem.objects.get(id=asset_id)
                                    inv_item.status = 'available'
                                    inv_item.assigned_to = None
                                    inv_item.condition = condition
                                    inv_item.save()
                                    
                                    ReturnVoucherAsset.objects.create(
                                        voucher_item=item,
                                        inventory_item=inv_item
                                    )
                
                messages.success(request, f'تم إنشاء وصل الإرجاع رقم {voucher.voucher_number} بنجاح')
                return redirect('return_voucher_detail', pk=voucher.pk)
    else:
        form = ReturnVoucherForm(tenant=tenant, initial={'date': timezone.now().date()})
    
    products = Product.objects.filter(tenant=tenant, is_active=True)
    departments = Department.objects.filter(tenant=tenant, is_active=True)
    
    return render(request, 'transactions/return_voucher_form.html', {
        'form': form,
        'title': 'إنشاء وصل إرجاع جديد',
        'products': products,
        'departments': departments,
    })


@login_required
def return_voucher_detail(request, pk):
    """تفاصيل وصل الإرجاع"""
    voucher = get_object_or_404(ReturnVoucher, pk=pk)
    
    if not request.user.is_super_admin and voucher.tenant != request.user.tenant:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذا الوصل')
        return redirect('return_voucher_list')
    
    items = voucher.items.select_related('product').prefetch_related('assets__inventory_item')
    
    return render(request, 'transactions/return_voucher_detail.html', {
        'voucher': voucher,
        'items': items,
    })


@login_required
def return_voucher_confirm(request, pk):
    """تأكيد وصل الإرجاع"""
    voucher = get_object_or_404(ReturnVoucher, pk=pk)
    
    if voucher.status != 'draft':
        messages.error(request, 'لا يمكن تأكيد هذا الوصل')
        return redirect('return_voucher_detail', pk=pk)
    
    with transaction.atomic():
        # Update stock quantities for all products
        for item in voucher.items.all():
            if item.product.nature == 'consumable':
                update_product_stock(item.product, item.quantity)
        
        voucher.status = 'confirmed'
        voucher.confirmed_by = request.user
        voucher.save()
    
    messages.success(request, 'تم تأكيد وصل الإرجاع بنجاح')
    return redirect('return_voucher_detail', pk=pk)


# ============== Disposal Vouchers ==============

@login_required
def disposal_voucher_list(request):
    """قائمة وصلات الإتلاف"""
    vouchers = get_tenant_queryset(request, DisposalVoucher)
    
    search = request.GET.get('search', '')
    if search:
        vouchers = vouchers.filter(voucher_number__icontains=search)
    
    paginator = Paginator(vouchers.select_related('created_by'), 20)
    page = request.GET.get('page', 1)
    vouchers = paginator.get_page(page)
    
    return render(request, 'transactions/disposal_voucher_list.html', {
        'vouchers': vouchers,
        'search': search,
    })


@login_required
def disposal_voucher_create(request):
    """إنشاء وصل إتلاف جديد"""
    tenant = request.user.tenant
    
    if request.method == 'POST':
        form = DisposalVoucherForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                voucher = form.save(commit=False)
                voucher.tenant = tenant
                voucher.created_by = request.user
                voucher.voucher_number = generate_voucher_number('DIS', tenant)
                voucher.save()
                
                # Process items
                items_data = request.POST.getlist('product_id')
                quantities = request.POST.getlist('quantity')
                damage_descriptions = request.POST.getlist('damage_description')
                
                for i, product_id in enumerate(items_data):
                    if product_id:
                        product = Product.objects.get(id=product_id)
                        quantity = int(quantities[i]) if quantities[i] else 1
                        damage_desc = damage_descriptions[i] if i < len(damage_descriptions) else ''
                        
                        item = DisposalVoucherItem.objects.create(
                            voucher=voucher,
                            product=product,
                            quantity=quantity,
                            damage_description=damage_desc
                        )
                        
                        # Handle assets
                        if product.nature == 'asset':
                            asset_ids = request.POST.getlist(f'asset_id_{i}')
                            for asset_id in asset_ids:
                                if asset_id:
                                    inv_item = InventoryItem.objects.get(id=asset_id)
                                    inv_item.status = 'disposed'
                                    inv_item.condition = 'damaged'
                                    inv_item.save()
                                    
                                    DisposalVoucherAsset.objects.create(
                                        voucher_item=item,
                                        inventory_item=inv_item
                                    )
                
                messages.success(request, f'تم إنشاء وصل الإتلاف رقم {voucher.voucher_number} بنجاح')
                return redirect('disposal_voucher_detail', pk=voucher.pk)
    else:
        form = DisposalVoucherForm(initial={'date': timezone.now().date()})
    
    products = Product.objects.filter(tenant=tenant, is_active=True)
    
    return render(request, 'transactions/disposal_voucher_form.html', {
        'form': form,
        'title': 'إنشاء وصل إتلاف جديد',
        'products': products,
    })


@login_required
def disposal_voucher_detail(request, pk):
    """تفاصيل وصل الإتلاف"""
    voucher = get_object_or_404(DisposalVoucher, pk=pk)
    
    if not request.user.is_super_admin and voucher.tenant != request.user.tenant:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذا الوصل')
        return redirect('disposal_voucher_list')
    
    items = voucher.items.select_related('product').prefetch_related('assets__inventory_item')
    
    return render(request, 'transactions/disposal_voucher_detail.html', {
        'voucher': voucher,
        'items': items,
    })


@login_required
def disposal_voucher_confirm(request, pk):
    """تأكيد وصل الإتلاف"""
    voucher = get_object_or_404(DisposalVoucher, pk=pk)
    
    if voucher.status != 'draft':
        messages.error(request, 'لا يمكن تأكيد هذا الوصل')
        return redirect('disposal_voucher_detail', pk=pk)
    
    with transaction.atomic():
        # Check sufficient stock for consumables
        for item in voucher.items.all():
            if item.product.nature == 'consumable':
                if item.product.stock_quantity < item.quantity:
                    messages.error(request, f'لا يوجد مخزون كافٍ للمنتج {item.product.name}')
                    return redirect('disposal_voucher_detail', pk=pk)
        
        # Update stock quantities for all products
        for item in voucher.items.all():
            if item.product.nature == 'consumable':
                update_product_stock(item.product, -item.quantity)
        
        voucher.status = 'confirmed'
        voucher.confirmed_by = request.user
        voucher.save()
    
    messages.success(request, 'تم تأكيد وصل الإتلاف بنجاح')
    return redirect('disposal_voucher_detail', pk=pk)
