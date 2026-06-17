from django.contrib import admin
from .models import Plan, Payment


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_usd', 'price_uzs', 'duration_days', 'is_active', 'is_popular', 'order']
    list_filter = ['is_active', 'is_popular']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'amount', 'currency', 'provider', 'status', 'created_at']
    list_filter = ['status', 'provider', 'created_at']
    search_fields = ['user__username', 'provider_payment_id']
    readonly_fields = ['id', 'user', 'plan', 'amount', 'currency', 'provider',
                       'provider_payment_id', 'status', 'ip_address', 'metadata',
                       'created_at', 'updated_at']