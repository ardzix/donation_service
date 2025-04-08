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
    queryset = Campaign.objects.filter(is_deleted=False)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'verified']
    search_fields = ['title', 'description']
    ordering_fields = ['start_date', 'total_donated', 'unallocated_amount']
    lookup_field = "external_id"

    def get_queryset(self):
        if self.action == 'retrieve':
            return Campaign.objects.filter(is_deleted=False)
        elif not self.request.user.is_authenticated:
            return Campaign.objects.none()
        user = self.request.user
        return Campaign.objects.filter(is_deleted=False, organizer=user)

    def get_object(self):
        return Campaign.objects.get(external_id=self.kwargs["external_id"])

    def get_serializer_class(self):
        if self.action == 'list':
            return CampaignListSerializer
        return CampaignDetailSerializer

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)


class BaseCampaignRelatedViewSet(ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['campaign__external_id']
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


class PlacementViewSet(BaseCampaignRelatedViewSet):
    queryset = Placement.objects.filter(is_deleted=False)
    serializer_class = PlacementSerializer
    search_fields = ['name', 'campaign__title']
    ordering_fields = ['created_at']

    def perform_create(self, serializer):
        campaign = serializer.validated_data.get('campaign')
        if campaign.organizer != self.request.user:
            raise PermissionDenied("You do not have permission to modify this campaign.")
        serializer.save(created_by=self.request.user)


class DonationViewSet(BaseCampaignRelatedViewSet):
    queryset = Donation.objects.all()
    serializer_class = DonationSerializer
    search_fields = ['donor__username', 'transaction_id']
    ordering_fields = ['timestamp', 'amount']

    def perform_create(self, serializer):
        donor = self.request.user if self.request.user.is_authenticated else None
        serializer.save(donor=donor)



class ExpenseViewSet(BaseCampaignRelatedViewSet):
    queryset = Expense.objects.filter(is_deleted=False)
    serializer_class = ExpenseSerializer
    search_fields = ['description', 'campaign__title']
    ordering_fields = ['timestamp', 'amount']

    def perform_create(self, serializer):
        campaign = serializer.validated_data.get('campaign')
        if campaign.organizer != self.request.user:
            raise PermissionDenied("You do not have permission to modify this campaign.")
        serializer.save(created_by=self.request.user)


class FundWithdrawalRequestViewSet(BaseCampaignRelatedViewSet):
    queryset = FundWithdrawalRequest.objects.all()
    serializer_class = FundWithdrawalRequestSerializer
    search_fields = ['campaign__title', 'requested_by__username']
    ordering_fields = ['timestamp', 'amount']

    def perform_create(self, serializer):
        campaign = serializer.validated_data.get('campaign')
        if campaign.organizer != self.request.user:
            raise PermissionDenied("You do not have permission to request withdrawals for this campaign.")
        serializer.save(requested_by=self.request.user)


class FundAllocationViewSet(ReadOnlyModelViewSet):
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
