# UFAS-Stock - Context Engineering Guide

## Project Overview

**نظام إدارة المخزون والممتلكات الشامل - جامعة فرحات عباس سطيف 1**

A comprehensive inventory and asset management system for Ferhat Abbas Setif 1 University. Built with Django 6.x, featuring multi-tenant architecture, Arabic RTL interface, and full voucher-based transaction tracking.

## Tech Stack

- **Backend:** Django 6.0.2 (Python)
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **Frontend:** Django Templates + Bootstrap 5 RTL + Chart.js
- **PDF Generation:** WeasyPrint
- **Excel Export:** openpyxl
- **Forms:** django-crispy-forms + crispy-bootstrap5

## Project Structure

```
UFAS-Stock/
├── config/                 # Django project settings
│   ├── settings.py        # Main configuration
│   ├── urls.py            # Root URL routing
│   └── wsgi.py
├── core/                   # Core app - Users, Tenants, Auth
│   ├── models.py          # Tenant, User, AuditLog
│   ├── views.py           # Dashboard, Login, Profile
│   ├── middleware.py      # TenantMiddleware
│   ├── context_processors.py
│   └── management/commands/
│       ├── setup_initial_data.py
│       └── seed_samples.py
├── inventory/              # Inventory management
│   ├── models.py          # Category, Product, InventoryItem, Supplier, Department, StockMovement
│   ├── views.py           # CRUD for all inventory entities
│   ├── forms.py
│   └── urls.py
├── transactions/           # Voucher management
│   ├── models.py          # EntryVoucher, ExitVoucher, ReturnVoucher, DisposalVoucher + Items
│   ├── views.py           # Voucher CRUD and processing
│   ├── forms.py
│   └── urls.py
├── reports/                # Reporting and exports
│   ├── views.py           # PDF/Excel generation, statistics API
│   └── urls.py
├── templates/              # Django templates (RTL Arabic)
│   ├── base.html          # Main layout with sidebar
│   ├── core/              # Auth and dashboard templates
│   ├── inventory/         # Product, Item, Category templates
│   ├── transactions/      # Voucher templates
│   └── reports/           # Report and PDF templates
├── static/                 # Static files (CSS, JS, images)
├── manage.py
├── requirements.txt
└── db.sqlite3
```

## Commands

### Development
```bash
# Activate virtual environment
source venv/bin/activate

# Run development server
python manage.py runserver

# Run on specific port
python manage.py runserver 0.0.0.0:8000
```

### Database
```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Setup initial data (tenants, categories, admin user)
python manage.py setup_initial_data

# Seed sample data for testing
python manage.py seed_samples
```

### Admin
```bash
# Create superuser manually
python manage.py createsuperuser

# Collect static files (production)
python manage.py collectstatic
```

### Checks
```bash
# Run system checks
python manage.py check

# Run tests
python manage.py test
```

## Key Models

### Core App
- **Tenant:** Multi-tenant units (central warehouse, faculties, institutes)
- **User:** Custom user with tenant association and roles (super_admin, admin, manager, staff, viewer)
- **AuditLog:** Activity tracking

### Inventory App
- **Category:** Hierarchical product categories (global or tenant-specific)
- **Product:** Base product definition (nature: asset or consumable)
- **InventoryItem:** Individual tracked assets with inventory_number and serial_number
- **StockMovement:** Quantity tracking for consumables
- **Supplier:** Vendor information
- **Department:** Internal departments receiving items

### Transactions App
- **EntryVoucher:** Incoming goods (وصل دخول)
- **ExitVoucher:** Outgoing goods to departments (وصل إخراج)
- **ReturnVoucher:** Returned items (وصل إرجاع)
- **DisposalVoucher:** Damaged/disposed items (وصل إتلاف)

Each voucher has associated Item and Asset models for line items.

## Multi-Tenancy Pattern

Data isolation is achieved via foreign key to Tenant:
```python
# Filter by current user's tenant
def get_tenant_queryset(request, model):
    if request.user.is_super_admin:
        return model.objects.all()
    return model.objects.filter(tenant=request.user.tenant)
```

The `TenantMiddleware` sets the current tenant in thread-local storage.

## URL Patterns

| Path | App | Description |
|------|-----|-------------|
| `/` | core | Dashboard |
| `/login/`, `/logout/` | core | Authentication |
| `/inventory/products/` | inventory | Products CRUD |
| `/inventory/items/` | inventory | Inventory items (assets) |
| `/inventory/categories/` | inventory | Categories |
| `/inventory/suppliers/` | inventory | Suppliers |
| `/inventory/departments/` | inventory | Departments |
| `/transactions/entry/` | transactions | Entry vouchers |
| `/transactions/exit/` | transactions | Exit vouchers |
| `/transactions/return/` | transactions | Return vouchers |
| `/transactions/disposal/` | transactions | Disposal vouchers |
| `/reports/` | reports | Reports index |
| `/reports/inventory/` | reports | Inventory report |
| `/admin/` | django.admin | Django admin panel |

## Code Conventions

### Models
- All models use Arabic verbose_name for admin/forms
- Timestamps: `created_at` (auto_now_add), `updated_at` (auto_now)
- Tenant FK on all tenant-scoped models
- Use `related_name` for reverse relations

### Views
- Use `@login_required` decorator
- Call `get_tenant_queryset()` for filtered data
- Use Django messages for user feedback
- Paginate lists with 20 items per page

### Templates
- Extend `base.html` for consistent layout
- Use `{% block title %}`, `{% block page_title %}`, `{% block content %}`
- RTL direction with Bootstrap 5 RTL
- Icons from Bootstrap Icons

### Forms
- Use crispy-forms with bootstrap5 pack
- Pass `tenant` parameter to filter related querysets
- Widget classes: `form-control`, `form-select`

## Default Credentials

- **Username:** admin
- **Password:** admin123
- **Role:** Super Admin (can see all tenants)

## Arabic/RTL Notes

- Language code: `ar`
- Timezone: `Africa/Algiers`
- Templates use `dir="rtl"` and Bootstrap RTL CSS
- Font: Tajawal (Google Fonts)

## Common Tasks

### Add a new product field
1. Add field to `inventory/models.py` Product model
2. Run `python manage.py makemigrations && python manage.py migrate`
3. Add field to `inventory/forms.py` ProductForm
4. Update templates if needed

### Add a new voucher type
1. Create model in `transactions/models.py` (extend BaseVoucher)
2. Create Item model for line items
3. Add form in `transactions/forms.py`
4. Add views in `transactions/views.py`
5. Add URL patterns in `transactions/urls.py`
6. Create templates in `templates/transactions/`
7. Add PDF template in `templates/reports/`

### Add a new report
1. Add view in `reports/views.py`
2. Add URL in `reports/urls.py`
3. Create template in `templates/reports/`
4. For PDF: create `*_pdf.html` template and use WeasyPrint

## Dependencies

Key packages in requirements.txt:
- `Django==6.0.2` - Web framework
- `django-crispy-forms==2.4` - Form rendering
- `crispy-bootstrap5==2025.4` - Bootstrap 5 template pack
- `django-filter==25.1` - Queryset filtering
- `WeasyPrint==65.1` - PDF generation
- `openpyxl==3.1.5` - Excel file handling
- `Pillow>=11.0.0` - Image processing
