import uuid
from django.db import models
from django.contrib.auth.models import User
from courses.models import Quest


class ExecutionLog(models.Model):
    """Skript bajarilish tarixi"""

    STATUS_CHOICES = [
        ('success', '✅ Muvaffaqiyatli'),
        ('failed', '❌ Muvaffaqiyatsiz'),
        ('error', '⚠️ Xatolik'),
        ('timeout', '⏰ Vaqt tugadi'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='executions')
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, null=True, blank=True)
    code = models.TextField(verbose_name='Yozilgan kod')
    output = models.TextField(blank=True, default='', verbose_name='Natija')
    error_output = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='failed')
    execution_time = models.FloatField(default=0, verbose_name='Bajarilish vaqti (soniya)')
    is_correct = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Bajarilish tarixi'
        verbose_name_plural = 'Bajarilish tarixi'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_status_display()} {self.user.username} - {self.created_at}"