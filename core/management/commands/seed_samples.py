"""
Management command to seed sample data for UFAS-Stock
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import random

from core.models import Tenant, User
from inventory.models import Category, Department, Supplier, Product, InventoryItem, StockMovement
from transactions.models import (
    EntryVoucher, EntryVoucherItem, EntryVoucherAsset,
    ExitVoucher, ExitVoucherItem, ExitVoucherAsset,
)


class Command(BaseCommand):
    help = 'Seeds sample data for testing UFAS-Stock'

    def handle(self, *args, **options):
        self.stdout.write('Seeding sample data...\n')
        
        central = Tenant.objects.get(code='CENTRAL')
        admin = User.objects.get(username='admin')
        
        # Get categories
        cat_it = Category.objects.get(code='IT')
        cat_furn = Category.objects.get(code='FURN')
        cat_paper = Category.objects.get(code='PAPER')
        cat_elec = Category.objects.get(code='ELEC')
        cat_lab = Category.objects.get(code='LAB')
        
        # Get suppliers and departments
        suppliers = list(Supplier.objects.filter(tenant=central))
        departments = list(Department.objects.filter(tenant=central))
        
        # ========== CREATE PRODUCTS ==========
        products_data = [
            # IT Equipment (Assets)
            ('PC-001', 'حاسوب مكتبي Dell OptiPlex', cat_it, 'asset', 'piece', 85000),
            ('PC-002', 'حاسوب محمول HP ProBook', cat_it, 'asset', 'piece', 120000),
            ('PC-003', 'حاسوب محمول Lenovo ThinkPad', cat_it, 'asset', 'piece', 95000),
            ('PRN-001', 'طابعة HP LaserJet Pro', cat_it, 'asset', 'piece', 45000),
            ('PRN-002', 'طابعة متعددة الوظائف Canon', cat_it, 'asset', 'piece', 65000),
            ('MON-001', 'شاشة كمبيوتر 24 بوصة Dell', cat_it, 'asset', 'piece', 28000),
            ('MON-002', 'شاشة كمبيوتر 27 بوصة LG', cat_it, 'asset', 'piece', 35000),
            ('PRJ-001', 'جهاز عرض Epson', cat_it, 'asset', 'piece', 75000),
            ('SRV-001', 'خادم Dell PowerEdge', cat_it, 'asset', 'piece', 450000),
            ('NET-001', 'موزع شبكة Cisco 24 منفذ', cat_it, 'asset', 'piece', 55000),
            
            # Furniture (Assets)
            ('DSK-001', 'مكتب خشبي 160×80', cat_furn, 'asset', 'piece', 25000),
            ('DSK-002', 'مكتب مدير فاخر', cat_furn, 'asset', 'piece', 45000),
            ('CHR-001', 'كرسي مكتب دوار', cat_furn, 'asset', 'piece', 12000),
            ('CHR-002', 'كرسي مدير جلد', cat_furn, 'asset', 'piece', 28000),
            ('CAB-001', 'خزانة ملفات معدنية', cat_furn, 'asset', 'piece', 18000),
            ('TBL-001', 'طاولة اجتماعات 8 أشخاص', cat_furn, 'asset', 'piece', 55000),
            
            # Electrical (Assets)
            ('AC-001', 'مكيف هواء LG 12000 BTU', cat_elec, 'asset', 'piece', 85000),
            ('AC-002', 'مكيف هواء Samsung 18000 BTU', cat_elec, 'asset', 'piece', 110000),
            
            # Lab Equipment (Assets)
            ('MIC-001', 'مجهر ضوئي Olympus', cat_lab, 'asset', 'piece', 180000),
            ('OSC-001', 'راسم إشارة رقمي', cat_lab, 'asset', 'piece', 250000),
            
            # Consumables
            ('PAP-001', 'ورق طباعة A4 (رزمة 500)', cat_paper, 'consumable', 'ream', 650),
            ('PAP-002', 'ورق طباعة A3 (رزمة 500)', cat_paper, 'consumable', 'ream', 1200),
            ('INK-001', 'حبر طابعة HP أسود', cat_paper, 'consumable', 'piece', 3500),
            ('INK-002', 'حبر طابعة HP ملون', cat_paper, 'consumable', 'piece', 5500),
            ('PEN-001', 'أقلام حبر جاف (علبة 50)', cat_paper, 'consumable', 'box', 800),
            ('STK-001', 'دباسة معدنية', cat_paper, 'consumable', 'piece', 350),
            ('FLD-001', 'ملفات بلاستيكية (حزمة 10)', cat_paper, 'consumable', 'pack', 450),
        ]
        
        products = {}
        for code, name, category, nature, unit, price in products_data:
            product, created = Product.objects.get_or_create(
                code=code,
                tenant=central,
                defaults={
                    'name': name,
                    'category': category,
                    'nature': nature,
                    'unit': unit,
                    'unit_price': Decimal(str(price)),
                    'min_stock': 5 if nature == 'consumable' else 0,
                }
            )
            products[code] = product
            if created:
                self.stdout.write(f'  Created product: {name}')
        
        # ========== CREATE INVENTORY ITEMS (Assets) ==========
        self.stdout.write('\nCreating inventory items...')
        
        asset_products = [p for p in products.values() if p.nature == 'asset']
        item_count = 0
        
        for product in asset_products:
            # Create 2-5 items per asset product
            num_items = random.randint(2, 5)
            for i in range(num_items):
                inv_num = f"INV-{product.code}-{str(i+1).zfill(3)}"
                serial = f"SN-{random.randint(100000, 999999)}"
                
                # Random status distribution
                status_choices = ['available'] * 6 + ['assigned'] * 3 + ['disposed'] * 1
                status = random.choice(status_choices)
                
                condition_choices = ['new'] * 4 + ['good'] * 4 + ['fair'] * 2
                condition = random.choice(condition_choices)
                
                assigned_to = None
                if status == 'assigned':
                    assigned_to = random.choice(departments)
                    condition = random.choice(['good', 'fair'])
                elif status == 'disposed':
                    condition = 'damaged'
                
                item, created = InventoryItem.objects.get_or_create(
                    inventory_number=inv_num,
                    tenant=central,
                    defaults={
                        'product': product,
                        'serial_number': serial,
                        'status': status,
                        'condition': condition,
                        'purchase_date': timezone.now().date() - timedelta(days=random.randint(30, 730)),
                        'purchase_price': product.unit_price,
                        'assigned_to': assigned_to,
                        'location': random.choice(['المبنى A', 'المبنى B', 'المبنى C', 'المخزن الرئيسي']),
                    }
                )
                if created:
                    item_count += 1
        
        self.stdout.write(f'  Created {item_count} inventory items')
        
        # ========== CREATE STOCK MOVEMENTS FOR CONSUMABLES ==========
        self.stdout.write('\nCreating stock movements...')
        
        consumable_products = [p for p in products.values() if p.nature == 'consumable']
        
        for product in consumable_products:
            # Initial stock entry
            StockMovement.objects.get_or_create(
                product=product,
                tenant=central,
                reference=f'INIT-{product.code}',
                defaults={
                    'movement_type': 'in',
                    'quantity': random.randint(50, 200),
                    'unit_price': product.unit_price,
                    'created_by': admin,
                }
            )
            
            # Some outgoing movements
            for _ in range(random.randint(2, 5)):
                StockMovement.objects.create(
                    product=product,
                    tenant=central,
                    movement_type='out',
                    quantity=-random.randint(5, 20),
                    reference=f'OUT-{random.randint(1000, 9999)}',
                    created_by=admin,
                )
        
        self.stdout.write('  Created stock movements')
        
        # ========== CREATE ENTRY VOUCHERS ==========
        self.stdout.write('\nCreating entry vouchers...')
        
        for i in range(5):
            voucher_date = timezone.now().date() - timedelta(days=random.randint(1, 60))
            voucher = EntryVoucher.objects.create(
                voucher_number=f'ENT-CENTRAL-2024-{str(i+1).zfill(4)}',
                date=voucher_date,
                supplier=random.choice(suppliers),
                invoice_number=f'FAC-{random.randint(10000, 99999)}',
                invoice_date=voucher_date - timedelta(days=random.randint(1, 5)),
                status='confirmed',
                tenant=central,
                created_by=admin,
                confirmed_by=admin,
            )
            
            # Add 2-4 items to each voucher
            selected_products = random.sample(list(products.values()), random.randint(2, 4))
            for product in selected_products:
                qty = random.randint(1, 3) if product.nature == 'asset' else random.randint(10, 50)
                EntryVoucherItem.objects.create(
                    voucher=voucher,
                    product=product,
                    quantity=qty,
                    unit_price=product.unit_price,
                )
            
            self.stdout.write(f'  Created entry voucher: {voucher.voucher_number}')
        
        # ========== CREATE EXIT VOUCHERS ==========
        self.stdout.write('\nCreating exit vouchers...')
        
        for i in range(4):
            voucher_date = timezone.now().date() - timedelta(days=random.randint(1, 45))
            voucher = ExitVoucher.objects.create(
                voucher_number=f'EXT-CENTRAL-2024-{str(i+1).zfill(4)}',
                date=voucher_date,
                department=random.choice(departments),
                recipient_name=random.choice(['أحمد محمد', 'فاطمة علي', 'محمد كريم', 'سارة أمين']),
                status='confirmed',
                tenant=central,
                created_by=admin,
                confirmed_by=admin,
            )
            
            # Add 1-3 consumable items
            consumables = random.sample(consumable_products, min(random.randint(1, 3), len(consumable_products)))
            for product in consumables:
                ExitVoucherItem.objects.create(
                    voucher=voucher,
                    product=product,
                    quantity=random.randint(2, 10),
                )
            
            self.stdout.write(f'  Created exit voucher: {voucher.voucher_number}')
        
        # ========== SUMMARY ==========
        self.stdout.write(self.style.SUCCESS('\n✅ Sample data seeded successfully!'))
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'  - Products: {Product.objects.filter(tenant=central).count()}')
        self.stdout.write(f'  - Inventory Items: {InventoryItem.objects.filter(tenant=central).count()}')
        self.stdout.write(f'  - Entry Vouchers: {EntryVoucher.objects.filter(tenant=central).count()}')
        self.stdout.write(f'  - Exit Vouchers: {ExitVoucher.objects.filter(tenant=central).count()}')
        self.stdout.write(f'\nRun: python manage.py runserver')
