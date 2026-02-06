from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.access_control.domain.enums import RoleType
from apps.access_control.permissions import require_roles

from .serializers import (
    InvoiceApproveResponseSerializer,
    InvoiceListResponseSerializer,
    InvoiceUploadResponseSerializer,
    InvoiceUploadSerializer,
)
from .services.invoice_service import create_invoice


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
