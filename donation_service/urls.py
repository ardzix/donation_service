from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny

from campaigns.views import (
    CampaignViewSet,
    PlacementViewSet,
    DonationViewSet,
    ExpenseViewSet,
    FundAllocationViewSet,
    FundWithdrawalRequestViewSet,
    homepage
)
from common.views import FileViewSet

# Setup router
router = DefaultRouter()
router.register(r'campaigns', CampaignViewSet, basename='campaign')
router.register(r'placements', PlacementViewSet, basename='placement')
router.register(r'donations', DonationViewSet, basename='donation')
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'allocations', FundAllocationViewSet, basename='allocation')
router.register(r'withdrawals', FundWithdrawalRequestViewSet, basename='withdrawal')
router.register(r'common/file', FileViewSet, basename='file')

# Swagger schema config
schema_view = get_schema_view(
    openapi.Info(
        title="Campaign Donation API",
        default_version="v1",
        description="API documentation for campaign donation service with fund tracking and transparency.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="support@yourproject.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[AllowAny],
)

urlpatterns = [
    path('api/', include(router.urls)),
    path('', homepage, name='homepage'),
    # Swagger & Redoc UI
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]
if settings.DEBUG:
    urlpatterns.append(path('admin/', admin.site.urls))
else:
    urlpatterns.append(path('admin-kmzway87aa/', admin.site.urls))
