"""
Inventory models - Categories, Products, Items
نماذج المخزون - الأصناف والمنتجات والمواد
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    """صنف/عائلة المواد"""
    
    name = models.CharField('اسم الصنف', max_length=200)
    code = models.CharField('رمز الصنف', max_length=50)
    description = models.TextField('الوصف', blank=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='children',
        verbose_name='الصنف الأب'
    )
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name='الوحدة',
        null=True,
        blank=True
    )
    is_global = models.BooleanField('صنف عام', default=False, help_text='متاح لجميع الوحدات')
    created_at = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)
    
    class Meta:
        verbose_name = 'صنف'
        verbose_name_plural = 'الأصناف'
        ordering = ['name']
        unique_together = ['code', 'tenant']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Supplier(models.Model):
    """المورد"""
    
    name = models.CharField('اسم المورد', max_length=200)
    code = models.CharField('رمز المورد', max_length=50, blank=True)
    address = models.TextField('العنوان', blank=True)
    phone = models.CharField('الهاتف', max_length=20, blank=True)
    email = models.EmailField('البريد الإلكتروني', blank=True)
    tax_id = models.CharField('الرقم الجبائي', max_length=50, blank=True)
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='suppliers',
        verbose_name='الوحدة',
        null=True,
        blank=True
    )
    is_active = models.BooleanField('نشط', default=True)
    created_at = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)
    
    class Meta:
        verbose_name = 'مورد'
        verbose_name_plural = 'الموردون'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Department(models.Model):
    """المصلحة/القسم المستفيد"""
    
    name = models.CharField('اسم المصلحة', max_length=200)
    code = models.CharField('رمز المصلحة', max_length=50, blank=True)
    responsible_name = models.CharField('اسم المسؤول', max_length=200, blank=True)
    phone = models.CharField('الهاتف', max_length=20, blank=True)
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='departments',
        verbose_name='الوحدة'
    )
    is_active = models.BooleanField('نشطة', default=True)
    created_at = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)
    
    class Meta:
        verbose_name = 'مصلحة'
        verbose_name_plural = 'المصالح'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.tenant.name}"


class Product(models.Model):
    """المنتج/المادة الأساسية"""
    
    NATURE_CHOICES = [
        ('asset', 'مادة مجرودة (أصل)'),
        ('consumable', 'مادة غير مجرودة (مستهلكة)'),
    ]
    
    UNIT_CHOICES = [
        ('piece', 'قطعة'),
        ('box', 'علبة'),
        ('pack', 'رزمة'),
        ('kg', 'كيلوغرام'),
        ('liter', 'لتر'),
        ('meter', 'متر'),
        ('ream', 'رزمة ورق'),
    ]
    
    name = models.CharField('اسم المادة', max_length=300)
    code = models.CharField('رمز المادة', max_length=100)
    description = models.TextField('الوصف', blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products',
        verbose_name='الصنف'
    )
    nature = models.CharField('طبيعة المادة', max_length=20, choices=NATURE_CHOICES, default='consumable')
    unit = models.CharField('وحدة القياس', max_length=20, choices=UNIT_CHOICES, default='piece')
    unit_price = models.DecimalField(
        'سعر الوحدة',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    min_stock = models.PositiveIntegerField('الحد الأدنى للمخزون', default=0)
    initial_quantity = models.PositiveIntegerField('الكمية الأولية', default=0)
    stock_quantity = models.PositiveIntegerField('الكمية المتوفرة', default=0)
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='الوحدة'
    )
    is_active = models.BooleanField('نشط', default=True)
    created_at = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)
    updated_at = models.DateTimeField('تاريخ التحديث', auto_now=True)
    
    class Meta:
        verbose_name = 'منتج/مادة'
        verbose_name_plural = 'المنتجات/المواد'
        ordering = ['name']
        unique_together = ['code', 'tenant']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def is_asset(self):
        return self.nature == 'asset'
    
    @property
    def current_stock(self):
        """حساب المخزون الحالي للمواد غير المجرودة"""
        if self.is_asset:
            return self.items.filter(status='available').count()
        return self.stock_movements.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0


class InventoryItem(models.Model):
    """عنصر المخزون - للمواد المجرودة (الأصول)"""
    
    STATUS_CHOICES = [
        ('available', 'متوفر'),
        ('assigned', 'مخرج/مسلم'),
        ('maintenance', 'في الصيانة'),
        ('disposed', 'متلف/محذوف'),
    ]
    
    CONDITION_CHOICES = [
        ('new', 'جديد'),
        ('good', 'جيد'),
        ('fair', 'مقبول'),
        ('poor', 'سيء'),
        ('damaged', 'تالف'),
    ]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='المنتج'
    )
    inventory_number = models.CharField('رقم الجرد', max_length=100)
    serial_number = models.CharField('الرقم التسلسلي', max_length=100, blank=True)
    barcode = models.CharField('الباركود', max_length=100, blank=True)
    status = models.CharField('الحالة', max_length=20, choices=STATUS_CHOICES, default='available')
    condition = models.CharField('حالة المادة', max_length=20, choices=CONDITION_CHOICES, default='new')
    purchase_date = models.DateField('تاريخ الشراء', null=True, blank=True)
    purchase_price = models.DecimalField(
        'سعر الشراء',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    warranty_end = models.DateField('نهاية الضمان', null=True, blank=True)
    location = models.CharField('الموقع', max_length=200, blank=True)
    assigned_to = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_items',
        verbose_name='المصلحة المستفيدة'
    )
    notes = models.TextField('ملاحظات', blank=True)
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='inventory_items',
        verbose_name='الوحدة'
    )
    created_at = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)
    updated_at = models.DateTimeField('تاريخ التحديث', auto_now=True)
    
    class Meta:
        verbose_name = 'عنصر مخزون'
        verbose_name_plural = 'عناصر المخزون'
        ordering = ['-created_at']
        unique_together = ['inventory_number', 'tenant']
    
    def __str__(self):
        return f"{self.product.name} - {self.inventory_number}"


class StockMovement(models.Model):
    """حركة المخزون للمواد غير المجرودة (المستهلكات)"""
    
    MOVEMENT_TYPES = [
        ('in', 'دخول'),
        ('out', 'خروج'),
        ('return', 'إرجاع'),
        ('adjust', 'تعديل'),
    ]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_movements',
        verbose_name='المنتج'
    )
    movement_type = models.CharField('نوع الحركة', max_length=10, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField('الكمية', help_text='موجب للدخول، سالب للخروج')
    unit_price = models.DecimalField('سعر الوحدة', max_digits=12, decimal_places=2, default=Decimal('0.00'))
    reference = models.CharField('المرجع', max_length=100, blank=True)
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='stock_movements',
        verbose_name='الوحدة'
    )
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='أنشئ بواسطة'
    )
    created_at = models.DateTimeField('التاريخ', auto_now_add=True)
    
    class Meta:
        verbose_name = 'حركة مخزون'
        verbose_name_plural = 'حركات المخزون'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.get_movement_type_display()} - {self.quantity}"
