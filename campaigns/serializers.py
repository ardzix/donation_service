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

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        serialize_fields(instance, representation, {
            'qr_code': (FileLiteSerializer, False),
        })

        return representation

    class Meta:
        model = Placement
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'is_deleted']


class DonationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donation
        fields = '__all__'
        read_only_fields = ['id', 'timestamp',
                            'transaction_id', 'is_fully_allocated']


class ExpenseSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        serialize_fields(instance, representation, {
            'receipt': (FileLiteSerializer, False),
        })

        return representation
    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ['id', 'timestamp', 'is_deleted']


class FundAllocationSerializer(serializers.ModelSerializer):
    donation = serializers.StringRelatedField()
    expense = serializers.StringRelatedField()

    class Meta:
        model = FundAllocation
        fields = '__all__'
        read_only_fields = ['id']


class FundWithdrawalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundWithdrawalRequest
        fields = '__all__'
        read_only_fields = ['id', 'timestamp', 'reviewed_at', 'reviewed_by']


class CampaignListSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        serialize_fields(instance, representation, {
            'featured_image': (FileLiteSerializer, False),
        })

        return representation

    class Meta:
        model = Campaign
        fields = ['id', 'title', 'description', 'goal_amount', 'total_donated',
                  'unallocated_amount', 'is_active', 'verified', 'featured_image']


class CampaignDetailSerializer(serializers.ModelSerializer):
    placements = PlacementSerializer(many=True, read_only=True)
    donations = DonationSerializer(many=True, read_only=True)
    expenses = ExpenseSerializer(many=True, read_only=True)
    withdrawal_requests = FundWithdrawalRequestSerializer(
        many=True, read_only=True)

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        serialize_fields(instance, representation, {
            'featured_image': (FileLiteSerializer, False),
            'images': (FileLiteSerializer, True),
        })

        return representation

    class Meta:
        model = Campaign
        fields = '__all__'
        read_only_fields = ['id', 'total_donated', 'is_deleted', 'verified',
                            'unallocated_amount', 'start_date', 'organizer']
