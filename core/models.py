"""
Core models - Users and Tenants (Multi-tenancy)
نماذج المستخدمين والمستأجرين
"""
from django.db import models
from django.contrib.auth.models import AbstractUser


class Tenant(models.Model):
    """المستأجر - يمثل وحدة مستقلة (كلية، معهد، مخزن مركزي)"""
    
    TENANT_TYPES = [
        ('central', 'المخزن المركزي'),
        ('faculty', 'كلية'),
        ('institute', 'معهد'),
        ('department', 'قسم'),
    ]
    
    name = models.CharField('اسم الوحدة', max_length=200)
    code = models.CharField('رمز الوحدة', max_length=50, unique=True)
    tenant_type = models.CharField('نوع الوحدة', max_length=20, choices=TENANT_TYPES, default='faculty')
    address = models.TextField('العنوان', blank=True)
    phone = models.CharField('الهاتف', max_length=20, blank=True)
    email = models.EmailField('البريد الإلكتروني', blank=True)
    is_active = models.BooleanField('نشط', default=True)
    created_at = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)
    updated_at = models.DateTimeField('تاريخ التحديث', auto_now=True)
    
    class Meta:
        verbose_name = 'وحدة/مستأجر'
        verbose_name_plural = 'الوحدات/المستأجرين'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class User(AbstractUser):
    """المستخدم المخصص مع دعم تعدد المستأجرين"""
    
    ROLE_CHOICES = [
        ('super_admin', 'مسؤول مركزي'),
        ('admin', 'مسؤول وحدة'),
        ('manager', 'مدير مخزن'),
        ('staff', 'موظف'),
        ('viewer', 'مشاهد فقط'),
    ]
    
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='users',
        verbose_name='الوحدة'
    )
    role = models.CharField('الدور', max_length=20, choices=ROLE_CHOICES, default='staff')
    phone = models.CharField('الهاتف', max_length=20, blank=True)
    
    class Meta:
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'
    
    def __str__(self):
        return f"{self.get_full_name() or self.username}"
    
    @property
    def is_super_admin(self):
        return self.role == 'super_admin'
    
    @property
    def can_manage(self):
        return self.role in ['super_admin', 'admin', 'manager']
    
    @property
    def can_edit(self):
        return self.role in ['super_admin', 'admin', 'manager', 'staff']


class AuditLog(models.Model):
    """سجل التدقيق لتتبع جميع العمليات"""
    
    ACTION_TYPES = [
        ('create', 'إنشاء'),
        ('update', 'تحديث'),
        ('delete', 'حذف'),
        ('entry', 'إدخال'),
        ('exit', 'إخراج'),
        ('return', 'إرجاع'),
        ('disposal', 'إتلاف'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='المستخدم')
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, verbose_name='الوحدة')
    action = models.CharField('العملية', max_length=20, choices=ACTION_TYPES)
    model_name = models.CharField('النموذج', max_length=100)
    object_id = models.PositiveIntegerField('معرف الكائن', null=True)
    object_repr = models.CharField('وصف الكائن', max_length=255)
    changes = models.JSONField('التغييرات', default=dict, blank=True)
    ip_address = models.GenericIPAddressField('عنوان IP', null=True, blank=True)
    timestamp = models.DateTimeField('التاريخ والوقت', auto_now_add=True)
    
    class Meta:
        verbose_name = 'سجل تدقيق'
        verbose_name_plural = 'سجلات التدقيق'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.object_repr}"
