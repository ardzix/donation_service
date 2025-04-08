from rest_framework import serializers
from .models import (
    Campaign,
    Placement,
    Donation,
    Expense,
    FundAllocation,
    FundWithdrawalRequest
)
from common.serializers import FileLiteSerializer, serialize_fields


class PlacementSerializer(serializers.ModelSerializer):
    campaign = serializers.SlugRelatedField(
        slug_field='external_id',
        queryset=Campaign.objects.all()
    )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        serialize_fields(instance, representation, {
            'qr_code': (FileLiteSerializer, False),
        })
        return representation

    class Meta:
        model = Placement
        exclude = ['id']
        read_only_fields = ['created_at', 'is_deleted', 'qr_code', 'url', 'created_by']


class DonationSerializer(serializers.ModelSerializer):
    campaign = serializers.SlugRelatedField(
        slug_field='external_id',
        queryset=Campaign.objects.all()
    )
    placement = serializers.SlugRelatedField(
        slug_field='external_id',
        queryset=Placement.objects.all(),
        allow_null=True,
        required=False
    )

    class Meta:
        model = Donation
        exclude = ['id']
        read_only_fields = ['timestamp', 'status', 'transaction_id', 'is_fully_allocated', 'donor']


class ExpenseSerializer(serializers.ModelSerializer):
    campaign = serializers.SlugRelatedField(
        slug_field='external_id',
        queryset=Campaign.objects.all()
    )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        serialize_fields(instance, representation, {
            'receipt': (FileLiteSerializer, False),
        })
        return representation

    class Meta:
        model = Expense
        exclude = ['id']
        read_only_fields = ['timestamp', 'is_deleted', 'created_by']


class FundAllocationSerializer(serializers.ModelSerializer):
    donation = serializers.SlugRelatedField(
        slug_field='external_id',
        queryset=Donation.objects.all()
    )
    expense = serializers.SlugRelatedField(
        slug_field='external_id',
        queryset=Expense.objects.all()
    )

    class Meta:
        model = FundAllocation
        exclude = ['id']


class FundWithdrawalRequestSerializer(serializers.ModelSerializer):
    campaign = serializers.SlugRelatedField(
        slug_field='external_id',
        queryset=Campaign.objects.all()
    )

    class Meta:
        model = FundWithdrawalRequest
        exclude = ['id']
        read_only_fields = ['timestamp', 'reviewed_at', 'reviewed_by', 'requested_by', 'is_approved']


class CampaignListSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        serialize_fields(instance, representation, {
            'featured_image': (FileLiteSerializer, False),
        })
        return representation

    class Meta:
        model = Campaign
        fields = ['external_id', 'title', 'description', 'goal_amount', 'total_donated',
                  'unallocated_amount', 'is_active', 'verified', 'featured_image']


class CampaignDetailSerializer(serializers.ModelSerializer):
    placements = PlacementSerializer(many=True, read_only=True)
    donations = DonationSerializer(many=True, read_only=True)
    expenses = ExpenseSerializer(many=True, read_only=True)
    withdrawal_requests = FundWithdrawalRequestSerializer(many=True, read_only=True)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        serialize_fields(instance, representation, {
            'featured_image': (FileLiteSerializer, False),
            'images': (FileLiteSerializer, True),
        })
        return representation

    def create(self, validated_data):
        placements_data = validated_data.pop('placements', [])
        expenses_data = validated_data.pop('expenses', [])
        campaign = Campaign.objects.create(**validated_data)

        for placement_data in placements_data:
            Placement.objects.create(campaign=campaign, **placement_data)

        for expense_data in expenses_data:
            Expense.objects.create(campaign=campaign, **expense_data)

        return campaign

    def update(self, instance, validated_data):
        placements_data = validated_data.pop('placements', [])
        expenses_data = validated_data.pop('expenses', [])
        instance = super().update(instance, validated_data)

        instance.placements.all().delete()
        for placement_data in placements_data:
            Placement.objects.create(campaign=instance, **placement_data)

        instance.expenses.all().delete()
        for expense_data in expenses_data:
            Expense.objects.create(campaign=instance, **expense_data)

        return instance

    class Meta:
        model = Campaign
        exclude = ['id']
        read_only_fields = ['total_donated', 'is_deleted', 'verified',
                            'unallocated_amount', 'start_date', 'organizer']
