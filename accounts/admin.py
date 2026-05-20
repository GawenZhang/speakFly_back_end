from django.contrib import admin

from .models import AccountGenerationBatch, GeneratedAccountRecord


class GeneratedAccountRecordInline(admin.TabularInline):
    model = GeneratedAccountRecord
    extra = 0
    readonly_fields = ['username', 'password', 'created_at']


@admin.register(AccountGenerationBatch)
class AccountGenerationBatchAdmin(admin.ModelAdmin):
    list_display = ['batch_id', 'count', 'prefix', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['batch_id', 'created_by__username']
    readonly_fields = ['batch_id', 'created_at']
    inlines = [GeneratedAccountRecordInline]


@admin.register(GeneratedAccountRecord)
class GeneratedAccountRecordAdmin(admin.ModelAdmin):
    list_display = ['username', 'batch', 'created_at']
    list_filter = ['batch__created_at']
    search_fields = ['username', 'batch__batch_id']
