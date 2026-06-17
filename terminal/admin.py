from django.contrib import admin
from .models import ExecutionLog


@admin.register(ExecutionLog)
class ExecutionLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'quest', 'status', 'is_correct', 'execution_time', 'created_at']
    list_filter = ['status', 'is_correct', 'created_at']
    search_fields = ['user__username', 'code']
    readonly_fields = ['id', 'user', 'quest', 'code', 'output', 'error_output',
                       'status', 'execution_time', 'is_correct', 'ip_address', 'created_at']