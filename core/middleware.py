"""
Tenant middleware for multi-tenancy support
"""
import threading

_thread_locals = threading.local()


def get_current_tenant():
    """Get the current tenant from thread local storage"""
    return getattr(_thread_locals, 'tenant', None)


def get_current_user():
    """Get the current user from thread local storage"""
    return getattr(_thread_locals, 'user', None)


class TenantMiddleware:
    """Middleware to set the current tenant based on the logged-in user"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        _thread_locals.user = request.user if request.user.is_authenticated else None
        _thread_locals.tenant = getattr(request.user, 'tenant', None) if request.user.is_authenticated else None
        
        response = self.get_response(request)
        return response
