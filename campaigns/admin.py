from django.contrib import admin
from .models import (
    Campaign,
    Placement,
    Donation,
    Expense,
    FundAllocation,
    FundWithdrawalRequest
)
from common.models import File


# Custom AdminSite to show banner count
class CustomAdminSite(admin.AdminSite):
    site_header = "Donation Admin Panel"

    def each_context(self, request):
        context = super().each_context(request)
        if request.user.is_staff:
            context['pending_withdrawals_count'] = FundWithdrawalRequest.objects.filter(is_approved=False).count()
        return context


custom_admin_site = CustomAdminSite(name='custom_admin')


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


# ========== Admins ==========
@admin.register(Campaign, site=custom_admin_site)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('external_id', 'title', 'goal_amount',
                    'total_donated', 'unallocated_amount', 'is_active', 'verified')
    search_fields = ('title', 'organizer__username', 'description')
    list_filter = ('is_active', 'verified', 'start_date')
    inlines = [PlacementInline, ExpenseInline, DonationInline]
    readonly_fields = ('total_donated', 'unallocated_amount', 'start_date', 'external_id')


@admin.register(Placement, site=custom_admin_site)
class PlacementAdmin(admin.ModelAdmin):
    list_display = ('external_id', 'name', 'campaign', 'created_by', 'created_at')
    search_fields = ('name', 'campaign__title', 'created_by__username')
    list_filter = ('created_at',)
    readonly_fields = ('external_id',)


@admin.register(Donation, site=custom_admin_site)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('external_id', 'donor', 'campaign', 'amount', 'timestamp',
                    'is_fully_allocated', 'transaction_id')
    search_fields = ('donor__username', 'campaign__title', 'transaction_id')
    list_filter = ('timestamp', 'is_fully_allocated')
    readonly_fields = ('external_id', 'timestamp', 'transaction_id')


@admin.register(Expense, site=custom_admin_site)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('external_id', 'description', 'campaign',
                    'amount', 'timestamp', 'created_by')
    search_fields = ('description', 'campaign__title', 'created_by__username')
    list_filter = ('timestamp',)
    inlines = [FundAllocationInline]
    readonly_fields = ('external_id', 'timestamp')


@admin.register(FundAllocation, site=custom_admin_site)
class FundAllocationAdmin(admin.ModelAdmin):
    list_display = ('external_id', 'donation', 'expense', 'allocated_amount')
    search_fields = ('donation__donor__username', 'expense__description')
    list_filter = ('donation__timestamp',)
    readonly_fields = ('external_id',)


@admin.register(FundWithdrawalRequest, site=custom_admin_site)
class FundWithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ('external_id', 'campaign', 'amount', 'requested_by',
                    'is_approved', 'timestamp', 'reviewed_by', 'reviewed_at')
    search_fields = ('campaign__title', 'requested_by__username')
    list_filter = ('is_approved', 'timestamp')
    readonly_fields = ('external_id', 'timestamp', 'reviewed_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_approved=False)


@admin.register(File, site=custom_admin_site)
class FileAdmin(admin.ModelAdmin):
    list_display = ('name', 'content_type', 'file')
    search_fields = ('name', 'description')

from django_q.models import Schedule, OrmQ, Failure, Success
from django_q.conf import Conf, croniter
from django_q.admin import ScheduleAdmin, TaskAdmin, FailAdmin, QueueAdmin


custom_admin_site.register(Schedule, ScheduleAdmin)
custom_admin_site.register(Success, TaskAdmin)
custom_admin_site.register(Failure, FailAdmin)

if Conf.ORM or Conf.TESTING:
    custom_admin_site.register(OrmQ, QueueAdmin)
