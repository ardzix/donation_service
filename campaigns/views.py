from rest_framework import viewsets, permissions, filters
from rest_framework.exceptions import PermissionDenied
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Campaign,
    Placement,
    Donation,
    Expense,
    FundAllocation,
    FundWithdrawalRequest
)

from .serializers import (
    CampaignListSerializer,
    CampaignDetailSerializer,
    PlacementSerializer,
    DonationSerializer,
    ExpenseSerializer,
    FundAllocationSerializer,
    FundWithdrawalRequestSerializer
)


class CampaignViewSet(ModelViewSet):
    """
    Campaigns are UGC. Users can only list/create/update their own campaigns.
    Public can view campaign detail by external_id.
    """
    queryset = Campaign.objects.filter(is_deleted=False)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'verified']
    search_fields = ['title', 'description']
    ordering_fields = ['start_date', 'total_donated', 'unallocated_amount']
    lookup_field = "external_id"

    def get_queryset(self):
        user = self.request.user
        if self.action == 'retrieve':
            return Campaign.objects.filter(is_deleted=False)
        return Campaign.objects.filter(is_deleted=False, organizer=user)

    def get_object(self):
        """
        Get object using external_id instead of PK.
        """
        return Campaign.objects.get(external_id=self.kwargs["external_id"])

    def get_serializer_class(self):
        if self.action == 'list':
            return CampaignListSerializer
        return CampaignDetailSerializer

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)


# ============================
# Base Class for Related Models
# ============================

class BaseCampaignRelatedViewSet(ModelViewSet):
    """
    Base viewset for all models related to Campaign via ForeignKey.
    Requires `?campaign=<uuid>` in query param.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['campaign']
    lookup_field = "external_id"

    campaign_param = openapi.Parameter(
        name='campaign',
        in_=openapi.IN_QUERY,
        description='Filter by Campaign external_id (Required)',
        type=openapi.TYPE_STRING,
        required=True,
    )

    @swagger_auto_schema(manual_parameters=[campaign_param])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        campaign_uuid = self.request.query_params.get('campaign')
        if not campaign_uuid:
            raise PermissionDenied("The 'campaign' query parameter is required.")

        return super().get_queryset().filter(
            campaign__external_id=campaign_uuid,
            campaign__organizer=self.request.user
        )

    def perform_create(self, serializer):
        campaign = serializer.validated_data.get('campaign')
        if campaign.organizer != self.request.user:
            raise PermissionDenied("You do not have permission to modify this campaign.")
        serializer.save()


# ============================
# ViewSets for Related Models
# ============================

class PlacementViewSet(BaseCampaignRelatedViewSet):
    queryset = Placement.objects.filter(is_deleted=False)
    serializer_class = PlacementSerializer
    search_fields = ['name', 'campaign__title']
    ordering_fields = ['created_at']


class DonationViewSet(BaseCampaignRelatedViewSet):
    queryset = Donation.objects.all()
    serializer_class = DonationSerializer
    search_fields = ['donor__username', 'transaction_id']
    ordering_fields = ['timestamp', 'amount']


class ExpenseViewSet(BaseCampaignRelatedViewSet):
    queryset = Expense.objects.filter(is_deleted=False)
    serializer_class = ExpenseSerializer
    search_fields = ['description', 'campaign__title']
    ordering_fields = ['timestamp', 'amount']


class FundWithdrawalRequestViewSet(BaseCampaignRelatedViewSet):
    queryset = FundWithdrawalRequest.objects.all()
    serializer_class = FundWithdrawalRequestSerializer
    search_fields = ['campaign__title', 'requested_by__username']
    ordering_fields = ['timestamp', 'amount']


class FundAllocationViewSet(ReadOnlyModelViewSet):
    """
    Read-only view for Fund Allocations. Requires ?campaign=<uuid>
    """
    queryset = FundAllocation.objects.select_related('donation', 'expense')
    serializer_class = FundAllocationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['donation', 'expense']
    search_fields = ['donation__donor__username', 'expense__description']
    ordering_fields = ['allocated_amount']

    campaign_param = openapi.Parameter(
        name='campaign',
        in_=openapi.IN_QUERY,
        description='Filter by Campaign external_id (Required)',
        type=openapi.TYPE_STRING,
        required=True,
    )

    @swagger_auto_schema(manual_parameters=[campaign_param])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        campaign_uuid = self.request.query_params.get('campaign')
        if not campaign_uuid:
            raise PermissionDenied("The 'campaign' query parameter is required.")
        return super().get_queryset().filter(expense__campaign__external_id=campaign_uuid,
                                             expense__campaign__organizer=self.request.user)


from django.shortcuts import render

def homepage(request):
    return render(request, "homepage.html")
