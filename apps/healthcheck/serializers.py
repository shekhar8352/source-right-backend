from rest_framework import serializers


class HealthLiveSerializer(serializers.Serializer):
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()


class HealthCheckResultSerializer(serializers.Serializer):
    name = serializers.CharField()
    ok = serializers.BooleanField()
    duration_ms = serializers.IntegerField()
    error = serializers.CharField(required=False, allow_blank=True)


class HealthReadySerializer(serializers.Serializer):
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    checks = HealthCheckResultSerializer(many=True)
