from rest_framework import serializers


class CoreExampleResponseSerializer(serializers.Serializer):
    status = serializers.CharField()


class VendorCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)


class VendorResponseSerializer(serializers.Serializer):
    vendor_id = serializers.CharField()
    name = serializers.CharField()


class InvoiceSummarySerializer(serializers.Serializer):
    invoice_id = serializers.CharField()
    amount = serializers.IntegerField()
    status = serializers.CharField()


class InvoiceListResponseSerializer(serializers.Serializer):
    invoices = InvoiceSummarySerializer(many=True)


class InvoiceApproveResponseSerializer(serializers.Serializer):
    invoice_id = serializers.CharField()
    status = serializers.CharField()


class InvoiceUploadSerializer(serializers.Serializer):
    invoice_id = serializers.CharField()
    amount = serializers.IntegerField(min_value=0)


class InvoiceUploadResponseSerializer(serializers.Serializer):
    invoice_id = serializers.CharField()
    status = serializers.CharField()
