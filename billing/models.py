import uuid
from django.db import models
from django.contrib.auth.models import User


class Plan(models.Model):
    """Obuna rejasi"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name='Reja nomi')
    slug = models.SlugField(unique=True)
    description = models.TextField(verbose_name='Tavsif')
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Narx (USD)')
    price_uzs = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Narx (UZS)')
    duration_days = models.IntegerField(default=30, verbose_name='Muddat (kun)')
    features = models.JSONField(default=list, verbose_name='Imkoniyatlar')
    stripe_price_id = models.CharField(max_length=100, blank=True, default='')
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Obuna rejasi'
        verbose_name_plural = 'Obuna rejalari'
        ordering = ['order']

    def __str__(self):
        return f"{self.name} - ${self.price_usd}"


class Payment(models.Model):
    """To'lov tarixi"""

    PROVIDER_CHOICES = [
        ('stripe', 'Stripe'),
        ('payme', 'Payme'),
        ('click', 'Click'),
        ('sandbox', 'Sandbox (Test)'),
    ]

    STATUS_CHOICES = [
        ('pending', '⏳ Kutilmoqda'),
        ('completed', '✅ Bajarildi'),
        ('failed', '❌ Muvaffaqiyatsiz'),
        ('refunded', '↩️ Qaytarildi'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    provider_payment_id = models.CharField(max_length=200, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'To\'lov'
        verbose_name_plural = 'To\'lovlar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()} - {self.amount} {self.currency}"