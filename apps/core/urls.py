from django.urls import path

from . import api

urlpatterns = [
    path("example", api.example_view, name="core-example"),
    path("internal/vendors", api.create_vendor_view, name="create-vendor"),
    path("internal/invoices", api.list_invoices_view, name="list-invoices"),
    path(
        "internal/invoices/<str:invoice_id>/approve",
        api.approve_invoice_view,
        name="approve-invoice",
    ),
    path("vendor/invoices/upload", api.upload_invoice_view, name="upload-invoice"),
]
