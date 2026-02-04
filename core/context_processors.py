"""
Context processors for tenant-aware templates
"""
from .middleware import get_current_tenant


def tenant_context(request):
    """Add tenant information to all templates"""
    tenant = None
    if request.user.is_authenticated:
        tenant = getattr(request.user, 'tenant', None)
    
    return {
        'current_tenant': tenant,
        'is_super_admin': getattr(request.user, 'is_super_admin', False) if request.user.is_authenticated else False,
    }
