from django.db import models

class Area(models.Model):
    name = models.CharField(max_length=100)
    geometry = models.JSONField(help_text="GeoJSON geometry (Polygon/MultiPolygon)")
    properties = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name


class Station(models.Model):
    name = models.CharField(max_length=100, unique=True)
    lat = models.FloatField()
    lon = models.FloatField()
    area = models.ForeignKey(Area, null=True, blank=True, on_delete=models.SET_NULL, related_name="stations")

    def __str__(self):
        return self.name


class Reading(models.Model):
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="readings")
    timestamp = models.DateTimeField(db_index=True)

    # weather
    temp_c = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    pressure_mb = models.FloatField(null=True, blank=True)
    windspeed_kph = models.FloatField(null=True, blank=True)
    condition_text = models.CharField(max_length=100, blank=True)

    # aqi / pollutants
    aqi_index = models.FloatField(null=True, blank=True)
    pm2_5 = models.FloatField(null=True, blank=True)
    pm10 = models.FloatField(null=True, blank=True)
    co = models.FloatField(null=True, blank=True)
    no2 = models.FloatField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["station", "timestamp"])]
        unique_together = ("station", "timestamp")
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.station.name} @ {self.timestamp}"


class Attribute(models.Model):
    key = models.SlugField(unique=True)       # e.g. "pm2_5"
    label = models.CharField(max_length=50)   # e.g. "PM2.5"
    unit = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.label


class Threshold(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="thresholds")
    max_value = models.FloatField(null=True, blank=True, help_text="upper bound; leave empty for the last (open-ended) band")
    color = models.CharField(max_length=7)
    label = models.CharField(max_length=30)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["attribute", "order"]



