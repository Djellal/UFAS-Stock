"""
Inventory views - Products, Items, Categories
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.http import JsonResponse

from .models import Product, InventoryItem, Category, Supplier, Department, StockMovement
from .forms import ProductForm, InventoryItemForm, CategoryForm, SupplierForm, DepartmentForm


def get_tenant_queryset(request, model):
    """Get queryset filtered by tenant"""
    if request.user.is_super_admin:
        return model.objects.all()
    return model.objects.filter(tenant=request.user.tenant)


# ============== Products ==============

@login_required
def product_list(request):
    """قائمة المنتجات"""
    products = get_tenant_queryset(request, Product)
    
    # Search
    search = request.GET.get('search', '')
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Filter by nature
    nature = request.GET.get('nature')
    if nature:
        products = products.filter(nature=nature)
    
    # Pagination
    paginator = Paginator(products, 20)
    page = request.GET.get('page', 1)
    products = paginator.get_page(page)
    
    categories = get_tenant_queryset(request, Category)
    
    context = {
        'products': products,
        'categories': categories,
        'search': search,
    }
    return render(request, 'inventory/product_list.html', context)


@login_required
def product_create(request):
    """إنشاء منتج جديد"""
    if request.method == 'POST':
        form = ProductForm(request.POST, tenant=request.user.tenant)
        if form.is_valid():
            product = form.save(commit=False)
            product.tenant = request.user.tenant
            product.save()
            messages.success(request, 'تم إنشاء المنتج بنجاح')
            return redirect('product_list')
    else:
        form = ProductForm(tenant=request.user.tenant)
    
    return render(request, 'inventory/product_form.html', {'form': form, 'title': 'إضافة منتج جديد'})


@login_required
def product_edit(request, pk):
    """تعديل منتج"""
    product = get_object_or_404(Product, pk=pk)
    
    if not request.user.is_super_admin and product.tenant != request.user.tenant:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذا المنتج')
        return redirect('product_list')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product, tenant=request.user.tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث المنتج بنجاح')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product, tenant=request.user.tenant)
    
    return render(request, 'inventory/product_form.html', {'form': form, 'title': 'تعديل المنتج', 'product': product})


@login_required
def product_detail(request, pk):
    """تفاصيل المنتج"""
    product = get_object_or_404(Product, pk=pk)
    
    if not request.user.is_super_admin and product.tenant != request.user.tenant:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذا المنتج')
        return redirect('product_list')
    
    items = product.items.all() if product.is_asset else None
    movements = product.stock_movements.all()[:20] if not product.is_asset else None
    
    context = {
        'product': product,
        'items': items,
        'movements': movements,
    }
    return render(request, 'inventory/product_detail.html', context)


# ============== Inventory Items (Assets) ==============

@login_required
def item_list(request):
    """قائمة عناصر المخزون (الأصول)"""
    items = get_tenant_queryset(request, InventoryItem)
    
    # Search
    search = request.GET.get('search', '')
    if search:
        items = items.filter(
            Q(inventory_number__icontains=search) |
            Q(serial_number__icontains=search) |
            Q(product__name__icontains=search)
        )
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        items = items.filter(status=status)
    
    # Filter by condition
    condition = request.GET.get('condition')
    if condition:
        items = items.filter(condition=condition)
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        items = items.filter(product__category_id=category_id)
    
    # Pagination
    paginator = Paginator(items.select_related('product', 'assigned_to'), 20)
    page = request.GET.get('page', 1)
    items = paginator.get_page(page)
    
    categories = get_tenant_queryset(request, Category)
    
    context = {
        'items': items,
        'categories': categories,
        'search': search,
        'status_choices': InventoryItem.STATUS_CHOICES,
        'condition_choices': InventoryItem.CONDITION_CHOICES,
    }
    return render(request, 'inventory/item_list.html', context)


@login_required
def item_create(request):
    """إنشاء عنصر مخزون جديد"""
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, tenant=request.user.tenant)
        if form.is_valid():
            item = form.save(commit=False)
            item.tenant = request.user.tenant
            item.save()
            messages.success(request, 'تم إنشاء عنصر المخزون بنجاح')
            return redirect('item_list')
    else:
        form = InventoryItemForm(tenant=request.user.tenant)
    
    return render(request, 'inventory/item_form.html', {'form': form, 'title': 'إضافة عنصر مخزون جديد'})


@login_required
def item_edit(request, pk):
    """تعديل عنصر مخزون"""
    item = get_object_or_404(InventoryItem, pk=pk)
    
    if not request.user.is_super_admin and item.tenant != request.user.tenant:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذا العنصر')
        return redirect('item_list')
    
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item, tenant=request.user.tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث عنصر المخزون بنجاح')
            return redirect('item_list')
    else:
        form = InventoryItemForm(instance=item, tenant=request.user.tenant)
    
    return render(request, 'inventory/item_form.html', {'form': form, 'title': 'تعديل عنصر المخزون', 'item': item})


@login_required
def item_detail(request, pk):
    """تفاصيل عنصر المخزون"""
    item = get_object_or_404(InventoryItem, pk=pk)
    
    if not request.user.is_super_admin and item.tenant != request.user.tenant:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذا العنصر')
        return redirect('item_list')
    
    return render(request, 'inventory/item_detail.html', {'item': item})


# ============== Categories ==============

@login_required
def category_list(request):
    """قائمة الأصناف"""
    categories = get_tenant_queryset(request, Category).filter(parent__isnull=True)
    return render(request, 'inventory/category_list.html', {'categories': categories})


@login_required
def category_create(request):
    """إنشاء صنف جديد"""
    if request.method == 'POST':
        form = CategoryForm(request.POST, tenant=request.user.tenant)
        if form.is_valid():
            category = form.save(commit=False)
            category.tenant = request.user.tenant
            category.save()
            messages.success(request, 'تم إنشاء الصنف بنجاح')
            return redirect('category_list')
    else:
        form = CategoryForm(tenant=request.user.tenant)
    
    return render(request, 'inventory/category_form.html', {'form': form, 'title': 'إضافة صنف جديد'})


# ============== Suppliers ==============

@login_required
def supplier_list(request):
    """قائمة الموردين"""
    suppliers = get_tenant_queryset(request, Supplier)
    
    search = request.GET.get('search', '')
    if search:
        suppliers = suppliers.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search)
        )
    
    paginator = Paginator(suppliers, 20)
    page = request.GET.get('page', 1)
    suppliers = paginator.get_page(page)
    
    return render(request, 'inventory/supplier_list.html', {'suppliers': suppliers, 'search': search})


@login_required
def supplier_create(request):
    """إنشاء مورد جديد"""
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.tenant = request.user.tenant
            supplier.save()
            messages.success(request, 'تم إنشاء المورد بنجاح')
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    
    return render(request, 'inventory/supplier_form.html', {'form': form, 'title': 'إضافة مورد جديد'})


# ============== Departments ==============

@login_required
def department_list(request):
    """قائمة المصالح"""
    departments = get_tenant_queryset(request, Department)
    
    search = request.GET.get('search', '')
    if search:
        departments = departments.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search)
        )
    
    paginator = Paginator(departments, 20)
    page = request.GET.get('page', 1)
    departments = paginator.get_page(page)
    
    return render(request, 'inventory/department_list.html', {'departments': departments, 'search': search})


@login_required
def department_create(request):
    """إنشاء مصلحة جديدة"""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save(commit=False)
            department.tenant = request.user.tenant
            department.save()
            messages.success(request, 'تم إنشاء المصلحة بنجاح')
            return redirect('department_list')
    else:
        form = DepartmentForm()
    
    return render(request, 'inventory/department_form.html', {'form': form, 'title': 'إضافة مصلحة جديدة'})


# ============== AJAX Endpoints ==============

@login_required
def search_items_ajax(request):
    """بحث ديناميكي عن عناصر المخزون"""
    query = request.GET.get('q', '')
    items = get_tenant_queryset(request, InventoryItem).filter(
        Q(inventory_number__icontains=query) |
        Q(serial_number__icontains=query) |
        Q(product__name__icontains=query),
        status='available'
    )[:10]
    
    results = [
        {
            'id': item.id,
            'text': f"{item.inventory_number} - {item.product.name}",
            'inventory_number': item.inventory_number,
            'serial_number': item.serial_number,
        }
        for item in items
    ]
    
    return JsonResponse({'results': results})


@login_required
def search_products_ajax(request):
    """بحث ديناميكي عن المنتجات"""
    query = request.GET.get('q', '')
    nature = request.GET.get('nature', '')
    
    products = get_tenant_queryset(request, Product).filter(
        Q(name__icontains=query) |
        Q(code__icontains=query)
    )
    
    if nature:
        products = products.filter(nature=nature)
    
    products = products[:10]
    
    results = [
        {
            'id': product.id,
            'text': f"{product.code} - {product.name}",
            'name': product.name,
            'code': product.code,
            'nature': product.nature,
            'unit': product.get_unit_display(),
            'unit_price': str(product.unit_price),
        }
        for product in products
    ]
    
    return JsonResponse({'results': results})
