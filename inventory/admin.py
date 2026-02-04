from django.contrib import admin
from .models import Category, Supplier, Department, Product, InventoryItem, StockMovement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent', 'tenant', 'is_global']
    list_filter = ['is_global', 'tenant']
    search_fields = ['name', 'code']
    ordering = ['name']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'phone', 'email', 'tenant', 'is_active']
    list_filter = ['is_active', 'tenant']
    search_fields = ['name', 'code', 'email']
    ordering = ['name']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'responsible_name', 'tenant', 'is_active']
    list_filter = ['is_active', 'tenant']
    search_fields = ['name', 'code', 'responsible_name']
    ordering = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'category', 'nature', 'unit', 'unit_price', 'tenant', 'is_active']
    list_filter = ['nature', 'category', 'tenant', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering = ['name']


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['inventory_number', 'product', 'serial_number', 'status', 'condition', 'assigned_to', 'tenant']
    list_filter = ['status', 'condition', 'tenant', 'product__category']
    search_fields = ['inventory_number', 'serial_number', 'product__name']
    ordering = ['-created_at']
    raw_id_fields = ['product', 'assigned_to']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'reference', 'created_by', 'created_at']
    list_filter = ['movement_type', 'tenant', 'created_at']
    search_fields = ['product__name', 'reference']
    ordering = ['-created_at']
    raw_id_fields = ['product']
