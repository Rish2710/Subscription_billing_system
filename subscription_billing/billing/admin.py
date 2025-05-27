from django.contrib import admin
from .models import Plan, Subscription, Invoice

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'description')
    search_fields = ('name',)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'plan', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'plan')
    search_fields = ('user__username', 'user__email', 'email')
    date_hierarchy = 'start_date'
    fields = ('user', 'email', 'plan', 'start_date', 'end_date', 'status')
    
    def save_model(self, request, obj, form, change):
        # Ensure email is auto-populated when saving through admin
        if not obj.email and obj.user and obj.user.email:
            obj.email = obj.user.email
        super().save_model(request, obj, form, change)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'user', 'email', 'amount', 'issue_date', 'due_date', 'status')
    list_filter = ('status',)
    search_fields = ('user__username', 'user__email', 'email', 'uuid')
    date_hierarchy = 'issue_date'
    fields = ('user', 'subscription', 'email', 'amount', 'issue_date', 'due_date', 'status')
    readonly_fields = ('uuid',)
    
    def save_model(self, request, obj, form, change):
        # Ensure email is auto-populated when saving through admin
        if not obj.email and obj.user and obj.user.email:
            obj.email = obj.user.email
        super().save_model(request, obj, form, change)
