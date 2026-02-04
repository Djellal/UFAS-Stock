"""
Transaction forms
"""
from django import forms
from .models import EntryVoucher, ExitVoucher, ReturnVoucher, DisposalVoucher
from inventory.models import Supplier, Department


class EntryVoucherForm(forms.ModelForm):
    class Meta:
        model = EntryVoucher
        fields = ['date', 'supplier', 'invoice_number', 'invoice_date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['supplier'].queryset = Supplier.objects.filter(tenant=tenant, is_active=True)


class ExitVoucherForm(forms.ModelForm):
    class Meta:
        model = ExitVoucher
        fields = ['date', 'department', 'recipient_name', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'recipient_name': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['department'].queryset = Department.objects.filter(tenant=tenant, is_active=True)


class ReturnVoucherForm(forms.ModelForm):
    class Meta:
        model = ReturnVoucher
        fields = ['date', 'department', 'original_exit_voucher', 'return_reason', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'original_exit_voucher': forms.Select(attrs={'class': 'form-select'}),
            'return_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['department'].queryset = Department.objects.filter(tenant=tenant, is_active=True)
            self.fields['original_exit_voucher'].queryset = ExitVoucher.objects.filter(tenant=tenant)


class DisposalVoucherForm(forms.ModelForm):
    class Meta:
        model = DisposalVoucher
        fields = ['date', 'disposal_reason', 'disposal_details', 'committee_members', 'disposal_date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'disposal_reason': forms.Select(attrs={'class': 'form-select'}),
            'disposal_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'committee_members': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'disposal_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
