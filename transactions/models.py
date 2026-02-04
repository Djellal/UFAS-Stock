"""
Transaction models - Entry, Exit, Return, Disposal vouchers
نماذج المعاملات - وصلات الدخول والخروج والإرجاع والإتلاف
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class BaseVoucher(models.Model):
    """النموذج الأساسي للوصلات"""
    
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('confirmed', 'مؤكد'),
        ('cancelled', 'ملغى'),
    ]
    
    voucher_number = models.CharField('رقم الوصل', max_length=50)
    date = models.DateField('التاريخ')
    status = models.CharField('الحالة', max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField('ملاحظات', blank=True)
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        verbose_name='الوحدة'
    )
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_created',
        verbose_name='أنشئ بواسطة'
    )
    confirmed_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_confirmed',
        verbose_name='أكد بواسطة'
    )
    created_at = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)
    updated_at = models.DateTimeField('تاريخ التحديث', auto_now=True)
    
    class Meta:
        abstract = True
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.voucher_number} - {self.date}"


class EntryVoucher(BaseVoucher):
    """وصل الدخول"""
    
    supplier = models.ForeignKey(
        'inventory.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entry_vouchers',
        verbose_name='المورد'
    )
    invoice_number = models.CharField('رقم الفاتورة', max_length=100, blank=True)
    invoice_date = models.DateField('تاريخ الفاتورة', null=True, blank=True)
    
    class Meta(BaseVoucher.Meta):
        verbose_name = 'وصل دخول'
        verbose_name_plural = 'وصلات الدخول'
        unique_together = ['voucher_number', 'tenant']
    
    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items.all())


class EntryVoucherItem(models.Model):
    """عناصر وصل الدخول"""
    
    voucher = models.ForeignKey(
        EntryVoucher,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='الوصل'
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        verbose_name='المنتج'
    )
    quantity = models.PositiveIntegerField('الكمية', default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        'سعر الوحدة',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    class Meta:
        verbose_name = 'عنصر وصل دخول'
        verbose_name_plural = 'عناصر وصل الدخول'
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price


class EntryVoucherAsset(models.Model):
    """الأصول المدخلة مع أرقام الجرد"""
    
    voucher_item = models.ForeignKey(
        EntryVoucherItem,
        on_delete=models.CASCADE,
        related_name='assets',
        verbose_name='عنصر الوصل'
    )
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.CASCADE,
        verbose_name='عنصر المخزون'
    )
    
    class Meta:
        verbose_name = 'أصل مدخل'
        verbose_name_plural = 'الأصول المدخلة'


class ExitVoucher(BaseVoucher):
    """وصل الإخراج"""
    
    department = models.ForeignKey(
        'inventory.Department',
        on_delete=models.SET_NULL,
        null=True,
        related_name='exit_vouchers',
        verbose_name='المصلحة المستفيدة'
    )
    recipient_name = models.CharField('اسم المستلم', max_length=200, blank=True)
    
    class Meta(BaseVoucher.Meta):
        verbose_name = 'وصل إخراج'
        verbose_name_plural = 'وصلات الإخراج'
        unique_together = ['voucher_number', 'tenant']


class ExitVoucherItem(models.Model):
    """عناصر وصل الإخراج"""
    
    voucher = models.ForeignKey(
        ExitVoucher,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='الوصل'
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        verbose_name='المنتج'
    )
    quantity = models.PositiveIntegerField('الكمية', default=1, validators=[MinValueValidator(1)])
    
    class Meta:
        verbose_name = 'عنصر وصل إخراج'
        verbose_name_plural = 'عناصر وصل الإخراج'
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class ExitVoucherAsset(models.Model):
    """الأصول المخرجة"""
    
    voucher_item = models.ForeignKey(
        ExitVoucherItem,
        on_delete=models.CASCADE,
        related_name='assets',
        verbose_name='عنصر الوصل'
    )
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.CASCADE,
        verbose_name='عنصر المخزون'
    )
    
    class Meta:
        verbose_name = 'أصل مخرج'
        verbose_name_plural = 'الأصول المخرجة'


class ReturnVoucher(BaseVoucher):
    """وصل الإرجاع"""
    
    department = models.ForeignKey(
        'inventory.Department',
        on_delete=models.SET_NULL,
        null=True,
        related_name='return_vouchers',
        verbose_name='المصلحة المرجعة'
    )
    original_exit_voucher = models.ForeignKey(
        ExitVoucher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='return_vouchers',
        verbose_name='وصل الإخراج الأصلي'
    )
    return_reason = models.TextField('سبب الإرجاع', blank=True)
    
    class Meta(BaseVoucher.Meta):
        verbose_name = 'وصل إرجاع'
        verbose_name_plural = 'وصلات الإرجاع'
        unique_together = ['voucher_number', 'tenant']


class ReturnVoucherItem(models.Model):
    """عناصر وصل الإرجاع"""
    
    CONDITION_CHOICES = [
        ('good', 'جيد'),
        ('fair', 'مقبول'),
        ('damaged', 'تالف'),
    ]
    
    voucher = models.ForeignKey(
        ReturnVoucher,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='الوصل'
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        verbose_name='المنتج'
    )
    quantity = models.PositiveIntegerField('الكمية', default=1, validators=[MinValueValidator(1)])
    condition = models.CharField('حالة المادة', max_length=20, choices=CONDITION_CHOICES, default='good')
    
    class Meta:
        verbose_name = 'عنصر وصل إرجاع'
        verbose_name_plural = 'عناصر وصل الإرجاع'
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class ReturnVoucherAsset(models.Model):
    """الأصول المرجعة"""
    
    voucher_item = models.ForeignKey(
        ReturnVoucherItem,
        on_delete=models.CASCADE,
        related_name='assets',
        verbose_name='عنصر الوصل'
    )
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.CASCADE,
        verbose_name='عنصر المخزون'
    )
    
    class Meta:
        verbose_name = 'أصل مرجع'
        verbose_name_plural = 'الأصول المرجعة'


class DisposalVoucher(BaseVoucher):
    """وصل الإتلاف"""
    
    DISPOSAL_REASONS = [
        ('damaged', 'تلف'),
        ('obsolete', 'تقادم'),
        ('lost', 'ضياع'),
        ('theft', 'سرقة'),
        ('other', 'أخرى'),
    ]
    
    disposal_reason = models.CharField('سبب الإتلاف', max_length=20, choices=DISPOSAL_REASONS)
    disposal_details = models.TextField('تفاصيل الإتلاف', blank=True)
    committee_members = models.TextField('أعضاء اللجنة', blank=True, help_text='أسماء أعضاء لجنة الإتلاف')
    disposal_date = models.DateField('تاريخ الإتلاف الفعلي', null=True, blank=True)
    
    class Meta(BaseVoucher.Meta):
        verbose_name = 'وصل إتلاف'
        verbose_name_plural = 'وصلات الإتلاف'
        unique_together = ['voucher_number', 'tenant']


class DisposalVoucherItem(models.Model):
    """عناصر وصل الإتلاف"""
    
    voucher = models.ForeignKey(
        DisposalVoucher,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='الوصل'
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        verbose_name='المنتج'
    )
    quantity = models.PositiveIntegerField('الكمية', default=1, validators=[MinValueValidator(1)])
    damage_description = models.TextField('وصف التلف', blank=True)
    
    class Meta:
        verbose_name = 'عنصر وصل إتلاف'
        verbose_name_plural = 'عناصر وصل الإتلاف'
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class DisposalVoucherAsset(models.Model):
    """الأصول المتلفة"""
    
    voucher_item = models.ForeignKey(
        DisposalVoucherItem,
        on_delete=models.CASCADE,
        related_name='assets',
        verbose_name='عنصر الوصل'
    )
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.CASCADE,
        verbose_name='عنصر المخزون'
    )
    
    class Meta:
        verbose_name = 'أصل متلف'
        verbose_name_plural = 'الأصول المتلفة'
