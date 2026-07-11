from datetime import datetime, timedelta

from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Area, Station, Reading, Attribute
from .serializers import (
    AreaSerializer,
    StationSerializer,
    AttributeSerializer,
    ReadingSerializer,
    StationDailyValueSerializer,
)

ALLOWED_ATTRIBUTE_FIELDS = {
    "aqi_index", "pm2_5", "pm10", "co", "no2",
    "temp_c", "humidity", "windspeed_kph",
}


class AttributeListView(APIView):
    def get(self, request):
        attributes = Attribute.objects.prefetch_related("thresholds").all()
        return Response(AttributeSerializer(attributes, many=True).data)


class StationListView(APIView):
    def get(self, request):
        stations = Station.objects.select_related("area").all()
        return Response(StationSerializer(stations, many=True).data)


class AreaListView(APIView):
    def get(self, request):
        areas = Area.objects.all()
        return Response(AreaSerializer(areas, many=True).data)


class AvailableTimestampsView(APIView):
    """GET /api/readings/timestamps/ -> dataset এ প্রথম ও শেষ timestamp (slider bound এর জন্য)।"""

    def get(self, request):
        first = Reading.objects.order_by("timestamp").first()
        last = Reading.objects.order_by("-timestamp").first()

        if not first or not last:
            return Response({"min_timestamp": None, "max_timestamp": None})

        return Response({
            "min_timestamp": first.timestamp,
            "max_timestamp": last.timestamp,
        })


class AQIMapDataView(APIView):
    """
    GET /api/readings/map/?attribute=pm2_5&timestamp=2025-06-15T14:00:00&station=1,2,3

    Query params:
    - attribute (required): whitelisted field name
    - timestamp (required): ISO datetime "YYYY-MM-DDTHH:MM:SS" or "YYYY-MM-DD HH:MM:SS"
    - station (optional): comma-separated station ids, na dile সব station
    - nearest (optional): "true" হলে exact match না পেলে closest reading খুঁজবে

    Ekta timestamp e (kono nirdishto muhurte) protita station er value ferot dey,
    jeta diye heatmap render hobe.
    """

    def get(self, request):
        attribute_key = request.query_params.get("attribute")
        timestamp_str = request.query_params.get("timestamp")
        station_param = request.query_params.get("station")
        use_nearest = request.query_params.get("nearest", "true").lower() == "true"

        if not attribute_key or attribute_key not in ALLOWED_ATTRIBUTE_FIELDS:
            return Response(
                {"error": f"Provide a valid 'attribute'. Allowed: {sorted(ALLOWED_ATTRIBUTE_FIELDS)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not timestamp_str:
            return Response(
                {"error": "Provide a 'timestamp' query param, e.g. 2025-06-15T14:00:00"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_timestamp = self._parse_timestamp(timestamp_str)
        if target_timestamp is None:
            return Response(
                {"error": "Invalid timestamp format. Use YYYY-MM-DDTHH:MM:SS"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stations = Station.objects.all()
        if station_param:
            try:
                station_ids = [int(s) for s in station_param.split(",")]
                stations = stations.filter(id__in=station_ids)
            except ValueError:
                return Response({"error": "'station' must be comma-separated integer ids."},
                                 status=status.HTTP_400_BAD_REQUEST)

        results = []
        for station in stations:
            reading = self._get_reading_for_station(station, target_timestamp, use_nearest)
            results.append({
                "station_id": station.id,
                "station_name": station.name,
                "lat": station.lat,
                "lon": station.lon,
                "value": getattr(reading, attribute_key) if reading else None,
                "matched_timestamp": reading.timestamp if reading else None,
            })

        serializer = StationDailyValueSerializer(results, many=True)
        return Response(serializer.data)

    def _parse_timestamp(self, timestamp_str):
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        return None

    def _get_reading_for_station(self, station, target_timestamp, use_nearest):
        exact = Reading.objects.filter(station=station, timestamp=target_timestamp).first()
        if exact or not use_nearest:
            return exact

        # exact match nai -> ager ba porer sobcheye kache thaka reading khoja
        before = (
            Reading.objects.filter(station=station, timestamp__lte=target_timestamp)
            .order_by("-timestamp").first()
        )
        after = (
            Reading.objects.filter(station=station, timestamp__gte=target_timestamp)
            .order_by("timestamp").first()
        )

        candidates = [r for r in [before, after] if r is not None]
        if not candidates:
            return None

        return min(candidates, key=lambda r: abs((r.timestamp - target_timestamp).total_seconds()))


class ReadingListView(APIView):
    """
    GET /api/readings/?station=<id>&start=<timestamp>&end=<timestamp>
    Raw hourly readings — per-station timeline/chart এর জন্য।
    """

    def get(self, request):
        queryset = Reading.objects.select_related("station").all()

        station_id = request.query_params.get("station")
        start_str = request.query_params.get("start")
        end_str = request.query_params.get("end")

        if station_id:
            queryset = queryset.filter(station_id=station_id)

        if start_str:
            queryset = queryset.filter(timestamp__gte=start_str)
        if end_str:
            queryset = queryset.filter(timestamp__lte=end_str)

        queryset = queryset.order_by("timestamp")[:2000]
        return Response(ReadingSerializer(queryset, many=True).data)