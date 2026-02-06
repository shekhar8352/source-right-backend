from rest_framework import serializers


class CoreExampleResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
