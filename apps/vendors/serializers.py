from rest_framework import serializers


class VendorCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)


class VendorResponseSerializer(serializers.Serializer):
    vendor_id = serializers.CharField()
    name = serializers.CharField()
