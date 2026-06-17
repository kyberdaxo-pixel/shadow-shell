from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def premium_required(view_func):
    """Premium foydalanuvchi uchun dekorator"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'cyber_profile'):
            messages.error(request, 'Profil topilmadi.')
            return redirect('accounts:login')
        if not request.user.cyber_profile.is_premium_active:
            messages.warning(request, '🔒 Bu bo\'lim faqat Premium foydalanuvchilar uchun!')
            return redirect('billing:pricing')
        return view_func(request, *args, **kwargs)
    return wrapper