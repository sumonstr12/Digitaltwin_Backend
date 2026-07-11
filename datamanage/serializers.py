from rest_framework import serializers
from .models import Area, Station, Reading, Attribute, Threshold


class ThresholdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Threshold
        fields = ["max_value", "color", "label", "order"]


class AttributeSerializer(serializers.ModelSerializer):
    thresholds = ThresholdSerializer(many=True, read_only=True)

    class Meta:
        model = Attribute
        fields = ["id", "key", "label", "unit", "thresholds"]


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ["id", "name", "geometry", "properties"]


class StationSerializer(serializers.ModelSerializer):
    area_name = serializers.CharField(source="area.name", read_only=True, default=None)

    class Meta:
        model = Station
        fields = ["id", "name", "lat", "lon", "area", "area_name"]


class ReadingSerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(source="station.name", read_only=True)

    class Meta:
        model = Reading
        fields = [
            "id", "station", "station_name", "timestamp",
            "temp_c", "humidity", "pressure_mb", "windspeed_kph", "condition_text",
            "aqi_index", "pm2_5", "pm10", "co", "no2",
        ]



class StationDailyValueSerializer(serializers.Serializer):
    station_id = serializers.IntegerField()
    station_name = serializers.CharField()
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    value = serializers.FloatField(allow_null=True)
    matched_timestamp = serializers.DateTimeField(allow_null=True)