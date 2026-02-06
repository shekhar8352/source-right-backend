from rest_framework import status
from uuid import uuid4

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from shared.logging import get_logger

from apps.access_control.domain.enums import RoleType
from apps.access_control.permissions import require_roles

from .serializers import (
    CoreExampleResponseSerializer,
    InvoiceApproveResponseSerializer,
    InvoiceListResponseSerializer,
    InvoiceUploadResponseSerializer,
    InvoiceUploadSerializer,
    VendorCreateSerializer,
    VendorResponseSerializer,
)
from .services.invoice_service import create_invoice

logger = get_logger(__name__)


@extend_schema(
    summary="Example endpoint",
    description="Example API endpoint used for smoke testing.",
    responses={200: CoreExampleResponseSerializer},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def example_view(request):
    """Return a basic OK response for smoke testing."""
    logger.info("Example view hit", extra={"path": request.path})
    return Response({"status": "ok"}, status=status.HTTP_200_OK)


@extend_schema(
    summary="Create vendor",
    description="Create a vendor (internal only).",
    request=VendorCreateSerializer,
    responses={201: VendorResponseSerializer},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_vendor_view(request):
    """Create a vendor (internal only)."""
    guard = require_roles(
        request,
        [RoleType.ORG_ADMIN, RoleType.FINANCE],
        action="create vendors",
    )
    if guard:
        return guard

    serializer = VendorCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    vendor_id = f"ven_{uuid4().hex[:10]}"
    payload = {"vendor_id": vendor_id, "name": serializer.validated_data["name"]}
    return Response(payload, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="List invoices",
    description="List invoices (internal only).",
    responses={200: InvoiceListResponseSerializer},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_invoices_view(request):
    """List invoices (internal only)."""
    guard = require_roles(
        request,
        [RoleType.ORG_ADMIN, RoleType.FINANCE, RoleType.APPROVER, RoleType.VIEWER],
        action="view invoices",
    )
    if guard:
        return guard

    return Response({"invoices": []}, status=status.HTTP_200_OK)


@extend_schema(
    summary="Approve invoice",
    description="Approve an invoice (internal only).",
    responses={200: InvoiceApproveResponseSerializer},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def approve_invoice_view(request, invoice_id: str):
    """Approve an invoice (internal only)."""
    guard = require_roles(request, [RoleType.APPROVER], action="approve invoices")
    if guard:
        return guard

    return Response(
        {"invoice_id": invoice_id, "status": "approved"},
        status=status.HTTP_200_OK,
    )


@extend_schema(
    summary="Upload invoice",
    description="Upload an invoice (vendor only).",
    request=InvoiceUploadSerializer,
    responses={201: InvoiceUploadResponseSerializer},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_invoice_view(request):
    """Upload an invoice (vendor only)."""
    guard = require_roles(request, [RoleType.VENDOR], action="upload invoices")
    if guard:
        return guard

    serializer = InvoiceUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    invoice_id = serializer.validated_data["invoice_id"]
    amount = serializer.validated_data["amount"]
    create_invoice(invoice_id=invoice_id, amount=amount)

    return Response(
        {"invoice_id": invoice_id, "status": "uploaded"},
        status=status.HTTP_201_CREATED,
    )
