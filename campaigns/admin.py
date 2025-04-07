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

# Inline model for FundAllocation inside Expense admin


class FundAllocationInline(admin.TabularInline):
    model = FundAllocation
    extra = 0
    readonly_fields = ('donation', 'allocated_amount')
    can_delete = False

# Inline model for Placement in Campaign admin


class PlacementInline(admin.TabularInline):
    model = Placement
    extra = 0

# Inline model for Expense in Campaign admin


class ExpenseInline(admin.TabularInline):
    model = Expense
    extra = 0
    fields = ('description', 'amount', 'timestamp', 'created_by')
    readonly_fields = ('timestamp',)

# Inline model for Donation in Campaign admin


class DonationInline(admin.TabularInline):
    model = Donation
    extra = 0
    fields = ('donor', 'amount', 'timestamp',
              'transaction_id', 'is_fully_allocated')
    readonly_fields = ('timestamp', 'transaction_id')


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('external_id', 'title', 'goal_amount',
                    'total_donated', 'unallocated_amount', 'is_active', 'verified')
    search_fields = ('title', 'organizer__username', 'description')
    list_filter = ('is_active', 'verified', 'start_date')
    inlines = [PlacementInline, ExpenseInline, DonationInline]
    readonly_fields = ('total_donated', 'unallocated_amount', 'start_date', 'external_id')


@admin.register(Placement)
class PlacementAdmin(admin.ModelAdmin):
    list_display = ('name', 'campaign', 'created_by', 'created_at')
    search_fields = ('name', 'campaign__title', 'created_by__username')
    list_filter = ('created_at',)


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('donor', 'campaign', 'amount', 'timestamp',
                    'is_fully_allocated', 'transaction_id')
    search_fields = ('donor__username', 'campaign__title', 'transaction_id')
    list_filter = ('timestamp', 'is_fully_allocated')
    readonly_fields = ('timestamp', 'transaction_id')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'campaign',
                    'amount', 'timestamp', 'created_by')
    search_fields = ('description', 'campaign__title', 'created_by__username')
    list_filter = ('timestamp',)
    inlines = [FundAllocationInline]
    readonly_fields = ('timestamp',)


@admin.register(FundAllocation)
class FundAllocationAdmin(admin.ModelAdmin):
    list_display = ('donation', 'expense', 'allocated_amount')
    search_fields = ('donation__donor__username', 'expense__description')
    list_filter = ('donation__timestamp',)


@admin.register(FundWithdrawalRequest)
class FundWithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'amount', 'requested_by',
                    'is_approved', 'timestamp', 'reviewed_by', 'reviewed_at')
    search_fields = ('campaign__title', 'requested_by__username')
    list_filter = ('is_approved', 'timestamp')
    readonly_fields = ('timestamp', 'reviewed_at')


@admin.register(File)
class FundWithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'content_type', 'file')
    search_fields = ('name', 'description')
