from django.db import models
from django.contrib.auth.models import User
from auditlog.registry import auditlog
from common.models import File
from auditlog.models import LogEntry
from django.contrib.contenttypes.fields import GenericRelation
from .mixins import SoftDeleteMixin
import uuid

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class Campaign(SoftDeleteMixin, models.Model):
    """
    Represents a fundraising campaign. Users can donate to a campaign,
    and campaign owners can create expenses to track fund usage.
    """
    external_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, help_text="Public UUID for external reference.")
    title = models.CharField(max_length=255, help_text="Title of the campaign.")
    description = models.TextField(help_text="Detailed description of the campaign.")
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="campaigns",
                                  help_text="User who created and manages the campaign.")
    goal_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="The target amount to be raised.")
    total_donated = models.DecimalField(max_digits=12, decimal_places=2, default=0, 
                                        help_text="Total donations received.")
    unallocated_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, 
                                             help_text="Amount not yet spent from total donations.")
    start_date = models.DateTimeField(auto_now_add=True, help_text="Campaign creation timestamp.")
    end_date = models.DateTimeField(null=True, blank=True, help_text="Optional end date for the campaign.")
    is_active = models.BooleanField(default=True, help_text="Indicates if the campaign is currently active.")
    verified = models.BooleanField(default=False, help_text="Admin verification status.")
    is_deleted = models.BooleanField(default=False, help_text="Soft delete flag.")

    featured_image = models.ForeignKey(File, on_delete=models.SET_NULL, blank=True, null=True, related_name="campaign_featured_image")
    images = models.ManyToManyField(File, blank=True, related_name="campaign_images")
    audit_logs = GenericRelation(LogEntry)

    objects = ActiveManager()  # only non-deleted by default
    all_objects = models.Manager()  # in case you still want full access somewhere

    class Meta:
        verbose_name = "Campaign"
        verbose_name_plural = "Campaigns"

    def __str__(self):
        return self.title

auditlog.register(Campaign)

class Placement(SoftDeleteMixin, models.Model):
    """
    Represents a placement (e.g., billboard, web banner) where a campaign is advertised.
    Each placement generates a unique URL or QR code for tracking donations.
    """
    external_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, help_text="Public UUID for external reference.")
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="placements",
                                 help_text="Associated campaign for this placement.")
    name = models.CharField(max_length=255, help_text="Name of the placement (e.g., 'Website Banner').")
    url = models.URLField(blank=True, null=True, help_text="URL where this placement leads to.")
    qr_code = models.ForeignKey(File, on_delete=models.SET_NULL, blank=True, null=True, related_name="qr_code",
                                help_text="QR code image for offline tracking.")
    donation_card = models.ForeignKey(File, on_delete=models.SET_NULL, blank=True, null=True, related_name="donation_card",
                                help_text="QR code image for offline tracking.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the placement was created.")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="placements",
                                   help_text="User who created this placement.")
    is_deleted = models.BooleanField(default=False, help_text="Soft delete flag.")
    audit_logs = GenericRelation(LogEntry)

    objects = ActiveManager()  # only non-deleted by default
    all_objects = models.Manager()  # in case you still want full access somewhere

    class Meta:
        verbose_name = "Placement"
        verbose_name_plural = "Placements"

    def __str__(self):
        return f"{self.name} - {self.campaign.title}"

auditlog.register(Placement)

class Donation(models.Model):
    """
    Represents a donation made to a campaign through a specific placement.
    Donations are allocated to expenses on a FIFO basis.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"


    external_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, help_text="Public UUID for external reference.")
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="donations",
                                 help_text="Campaign to which the donation was made.")
    placement = models.ForeignKey(Placement, on_delete=models.SET_NULL, null=True, blank=True, related_name="donations",
                                  help_text="Placement through which the donation was made.")
    donor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="donations",
                              help_text="User who made the donation.")
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Amount donated.")
    timestamp = models.DateTimeField(auto_now_add=True, help_text="Donation timestamp.")
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    is_fully_allocated = models.BooleanField(default=False, help_text="Flag indicating if the donation is fully used.")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, help_text="Donation payment status.")
    audit_logs = GenericRelation(LogEntry)

    class Meta:
        verbose_name = "Donation"
        verbose_name_plural = "Donations"

    def __str__(self):
        return f"Donation of {self.amount} to {self.campaign.title}"

auditlog.register(Donation)

class Expense(SoftDeleteMixin, models.Model):
    """
    Represents an expense made for a campaign. Donations are automatically allocated to cover expenses.
    """
    external_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, help_text="Public UUID for external reference.")
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="expenses",
                                 help_text="Campaign for which the expense was made.")
    description = models.CharField(max_length=255, help_text="Brief description of the expense.")
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Amount spent.")
    timestamp = models.DateTimeField(auto_now_add=True, help_text="Expense creation timestamp.")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expenses",
                                   help_text="User who created the expense record.")
    is_deleted = models.BooleanField(default=False, help_text="Soft delete flag.")
    receipt = models.ForeignKey(File, on_delete=models.SET_NULL, blank=True, null=True)
    audit_logs = GenericRelation(LogEntry)

    objects = ActiveManager()  # only non-deleted by default
    all_objects = models.Manager()  # in case you still want full access somewhere

    class Meta:
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"

    def __str__(self):
        return f"Expense: {self.description} - {self.amount}"

auditlog.register(Expense)

class FundAllocation(models.Model):
    """
    Represents the allocation of donations to expenses in a FIFO manner.
    Tracks how each donation is spent.
    """
    external_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, help_text="Public UUID for external reference.")
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, related_name="allocations",
                                 help_text="Donation being allocated to an expense.")
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="allocations",
                                help_text="Expense to which the donation is allocated.")
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Amount allocated from donation.")
    audit_logs = GenericRelation(LogEntry)

    class Meta:
        verbose_name = "Fund Allocation"
        verbose_name_plural = "Fund Allocations"

    def __str__(self):
        return f"{self.allocated_amount} from {self.donation.donor} to {self.expense.description}"

auditlog.register(FundAllocation)

class FundWithdrawalRequest(models.Model):
    """
    Represents a request to withdraw funds from a campaign.
    Requires admin approval before disbursement.
    """
    external_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, help_text="Public UUID for external reference.")
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="withdrawal_requests",
                                 help_text="Campaign from which funds are being withdrawn.")
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="withdrawal_requests",
                                     help_text="User requesting the withdrawal.")
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Requested withdrawal amount.")
    timestamp = models.DateTimeField(auto_now_add=True, help_text="Timestamp of the request.")
    is_approved = models.BooleanField(default=False, help_text="Approval status of the withdrawal request.")
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="withdrawal_reviews",
                                    help_text="Admin who reviewed the request.")
    reviewed_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when request was reviewed.")
    audit_logs = GenericRelation(LogEntry)
    
    class Meta:
        verbose_name = "Fund Withdrawal Request"
        verbose_name_plural = "Fund Withdrawal Requests"

    def __str__(self):
        return f"Withdrawal Request: {self.amount} from {self.campaign.title}"

auditlog.register(FundWithdrawalRequest)
