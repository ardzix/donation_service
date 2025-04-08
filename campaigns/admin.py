from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from campaigns.models import (
    Campaign, Placement, Donation, Expense,
    FundAllocation, FundWithdrawalRequest
)
from common.models import File
from auditlog.models import LogEntry
from django_q.models import Schedule, OrmQ, Failure, Success
from django_q.admin import ScheduleAdmin, TaskAdmin, FailAdmin, QueueAdmin
from django_q.conf import Conf


# ========== Custom Admin Site ==========
class CustomAdminSite(admin.AdminSite):
    site_header = "Donation Admin Panel"

    def each_context(self, request):
        context = super().each_context(request)
        if request.user.is_staff:
            context['pending_withdrawals_count'] = FundWithdrawalRequest.objects.filter(is_approved=False).count()
        return context


custom_admin_site = CustomAdminSite(name='custom_admin')


# ========== Base AuditLog Admin Mixin ==========
class AuditLogAdminMixin:
    def view_logs_link(self, obj):
        model_name = self.model._meta.model_name
        url = reverse('admin:auditlog_logentry_changelist') + f'?object_id={obj.pk}&content_type__model={model_name}'
        return format_html('<a class="button" href="{}">View Logs</a>', url)

    view_logs_link.short_description = 'Audit Logs'


# ========== Inlines ==========
class FundAllocationInline(admin.TabularInline):
    model = FundAllocation
    extra = 0
    readonly_fields = ('donation', 'allocated_amount')
    can_delete = False


class PlacementInline(admin.TabularInline):
    model = Placement
    extra = 0


class ExpenseInline(admin.TabularInline):
    model = Expense
    extra = 0
    fields = ('description', 'amount', 'timestamp', 'created_by')
    readonly_fields = ('timestamp',)


class DonationInline(admin.TabularInline):
    model = Donation
    extra = 0
    fields = ('donor', 'amount', 'timestamp', 'transaction_id', 'is_fully_allocated')
    readonly_fields = ('timestamp', 'transaction_id')


# ========== Model Admins ==========
@admin.register(Campaign, site=custom_admin_site)
class CampaignAdmin(AuditLogAdminMixin, admin.ModelAdmin):
    list_display = ('external_id', 'title', 'goal_amount', 'total_donated',
                    'unallocated_amount', 'is_active', 'verified', 'view_logs_link')
    search_fields = ('title', 'organizer__username', 'description')
    list_filter = ('is_active', 'verified', 'start_date')
    inlines = [PlacementInline, ExpenseInline, DonationInline]
    readonly_fields = ('total_donated', 'unallocated_amount', 'start_date', 'external_id')


@admin.register(Placement, site=custom_admin_site)
class PlacementAdmin(AuditLogAdminMixin, admin.ModelAdmin):
    list_display = ('external_id', 'name', 'campaign', 'created_by', 'created_at', 'view_logs_link')
    search_fields = ('name', 'campaign__title', 'created_by__username')
    list_filter = ('created_at',)
    readonly_fields = ('external_id',)


@admin.register(Donation, site=custom_admin_site)
class DonationAdmin(AuditLogAdminMixin, admin.ModelAdmin):
    list_display = ('external_id', 'donor', 'campaign', 'amount', 'timestamp',
                    'is_fully_allocated', 'transaction_id', 'view_logs_link')
    search_fields = ('donor__username', 'campaign__title', 'transaction_id')
    list_filter = ('timestamp', 'is_fully_allocated')
    readonly_fields = ('external_id', 'timestamp', 'transaction_id')


@admin.register(Expense, site=custom_admin_site)
class ExpenseAdmin(AuditLogAdminMixin, admin.ModelAdmin):
    list_display = ('external_id', 'description', 'campaign', 'amount',
                    'timestamp', 'created_by', 'view_logs_link')
    search_fields = ('description', 'campaign__title', 'created_by__username')
    list_filter = ('timestamp',)
    inlines = [FundAllocationInline]
    readonly_fields = ('external_id', 'timestamp')


@admin.register(FundAllocation, site=custom_admin_site)
class FundAllocationAdmin(AuditLogAdminMixin, admin.ModelAdmin):
    list_display = ('external_id', 'donation', 'expense', 'allocated_amount', 'view_logs_link')
    search_fields = ('donation__donor__username', 'expense__description')
    list_filter = ('donation__timestamp',)
    readonly_fields = ('external_id',)


@admin.register(FundWithdrawalRequest, site=custom_admin_site)
class FundWithdrawalRequestAdmin(AuditLogAdminMixin, admin.ModelAdmin):
    list_display = ('external_id', 'campaign', 'amount', 'requested_by',
                    'is_approved', 'timestamp', 'reviewed_by', 'reviewed_at', 'view_logs_link')
    search_fields = ('campaign__title', 'requested_by__username')
    list_filter = ('is_approved', 'timestamp')
    readonly_fields = ('external_id', 'timestamp', 'reviewed_at')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_approved=False)


@admin.register(File, site=custom_admin_site)
class FileAdmin(admin.ModelAdmin):
    list_display = ('name', 'content_type', 'file')
    search_fields = ('name', 'description')


# ========== Q Cluster Admins ==========
custom_admin_site.register(Schedule, ScheduleAdmin)
custom_admin_site.register(Success, TaskAdmin)
custom_admin_site.register(Failure, FailAdmin)

if Conf.ORM or Conf.TESTING:
    custom_admin_site.register(OrmQ, QueueAdmin)


# ========== LogEntry Admin ==========
@admin.register(LogEntry, site=custom_admin_site)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('object_repr', 'actor', 'action', 'timestamp')
    list_filter = ('content_type__model', 'action')
    search_fields = ('object_repr', 'changes', 'actor__username')
    readonly_fields = [f.name for f in LogEntry._meta.fields]
