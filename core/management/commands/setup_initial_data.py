"""
Management command to set up initial data for UFAS-Stock
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Tenant
from inventory.models import Category, Department, Supplier

User = get_user_model()


class Command(BaseCommand):
    help = 'Sets up initial data for the UFAS-Stock system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial data...\n')
        
        # Create central warehouse tenant
        central, created = Tenant.objects.get_or_create(
            code='CENTRAL',
            defaults={
                'name': 'المخزن المركزي',
                'tenant_type': 'central',
                'address': 'جامعة فرحات عباس سطيف 1',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created tenant: {central.name}'))
        
        # Create sample faculties
        faculties = [
            ('SCI', 'كلية العلوم', 'faculty'),
            ('TECH', 'كلية التكنولوجيا', 'faculty'),
            ('INFO', 'معهد الإعلام الآلي', 'institute'),
            ('MED', 'كلية الطب', 'faculty'),
        ]
        
        for code, name, tenant_type in faculties:
            tenant, created = Tenant.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'tenant_type': tenant_type,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created tenant: {name}'))
        
        # Create global categories
        categories = [
            ('IT', 'المعلومات الآلية'),
            ('FURN', 'الأثاث'),
            ('PAPER', 'الورق والمستلزمات المكتبية'),
            ('CHEM', 'المواد الكيميائية'),
            ('ELEC', 'الأجهزة الكهربائية'),
            ('LAB', 'المعدات المخبرية'),
        ]
        
        for code, name in categories:
            cat, created = Category.objects.get_or_create(
                code=code,
                tenant=None,
                defaults={
                    'name': name,
                    'is_global': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {name}'))
        
        # Create super admin user
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@ufas.dz',
                password='admin123',
                first_name='مدير',
                last_name='النظام',
                role='super_admin',
                tenant=central,
            )
            self.stdout.write(self.style.SUCCESS(f'Created super admin user: admin / admin123'))
        
        # Create sample departments for central
        departments = [
            ('ADM', 'الإدارة العامة'),
            ('IT-DEPT', 'مصلحة الإعلام الآلي'),
            ('LIB', 'المكتبة المركزية'),
            ('MAINT', 'مصلحة الصيانة'),
        ]
        
        for code, name in departments:
            dept, created = Department.objects.get_or_create(
                code=code,
                tenant=central,
                defaults={
                    'name': name,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created department: {name}'))
        
        # Create sample suppliers
        suppliers = [
            ('SUP001', 'شركة الحاسوب الجزائري'),
            ('SUP002', 'مؤسسة الأثاث المكتبي'),
            ('SUP003', 'شركة المستلزمات المخبرية'),
        ]
        
        for code, name in suppliers:
            sup, created = Supplier.objects.get_or_create(
                code=code,
                tenant=central,
                defaults={
                    'name': name,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created supplier: {name}'))
        
        self.stdout.write(self.style.SUCCESS('\nInitial data setup complete!'))
        self.stdout.write(self.style.WARNING('\nLogin credentials:'))
        self.stdout.write('  Username: admin')
        self.stdout.write('  Password: admin123')
        self.stdout.write('\nRun the server with: python manage.py runserver')
