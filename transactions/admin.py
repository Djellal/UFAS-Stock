from django.contrib import admin
from .models import (
    EntryVoucher, EntryVoucherItem, EntryVoucherAsset,
    ExitVoucher, ExitVoucherItem, ExitVoucherAsset,
    ReturnVoucher, ReturnVoucherItem, ReturnVoucherAsset,
    DisposalVoucher, DisposalVoucherItem, DisposalVoucherAsset,
)


class EntryVoucherItemInline(admin.TabularInline):
    model = EntryVoucherItem
    extra = 1
    raw_id_fields = ['product']


@admin.register(EntryVoucher)
class EntryVoucherAdmin(admin.ModelAdmin):
    list_display = ['voucher_number', 'date', 'supplier', 'status', 'tenant', 'created_by']
    list_filter = ['status', 'tenant', 'date']
    search_fields = ['voucher_number', 'supplier__name']
    ordering = ['-date']
    inlines = [EntryVoucherItemInline]
    raw_id_fields = ['supplier']


class ExitVoucherItemInline(admin.TabularInline):
    model = ExitVoucherItem
    extra = 1
    raw_id_fields = ['product']


@admin.register(ExitVoucher)
class ExitVoucherAdmin(admin.ModelAdmin):
    list_display = ['voucher_number', 'date', 'department', 'recipient_name', 'status', 'tenant']
    list_filter = ['status', 'tenant', 'date']
    search_fields = ['voucher_number', 'department__name', 'recipient_name']
    ordering = ['-date']
    inlines = [ExitVoucherItemInline]
    raw_id_fields = ['department']


class ReturnVoucherItemInline(admin.TabularInline):
    model = ReturnVoucherItem
    extra = 1
    raw_id_fields = ['product']


@admin.register(ReturnVoucher)
class ReturnVoucherAdmin(admin.ModelAdmin):
    list_display = ['voucher_number', 'date', 'department', 'status', 'tenant']
    list_filter = ['status', 'tenant', 'date']
    search_fields = ['voucher_number', 'department__name']
    ordering = ['-date']
    inlines = [ReturnVoucherItemInline]
    raw_id_fields = ['department', 'original_exit_voucher']


class DisposalVoucherItemInline(admin.TabularInline):
    model = DisposalVoucherItem
    extra = 1
    raw_id_fields = ['product']


@admin.register(DisposalVoucher)
class DisposalVoucherAdmin(admin.ModelAdmin):
    list_display = ['voucher_number', 'date', 'disposal_reason', 'status', 'tenant']
    list_filter = ['status', 'disposal_reason', 'tenant', 'date']
    search_fields = ['voucher_number']
    ordering = ['-date']
    inlines = [DisposalVoucherItemInline]
