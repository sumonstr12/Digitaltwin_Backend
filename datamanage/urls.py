from django.urls import path
from .views import (
    AttributeListView,
    StationListView,
    AreaListView,
    AvailableTimestampsView,
    AQIMapDataView,
    ReadingListView,
)

urlpatterns = [
    path("attributes/", AttributeListView.as_view(), name="attribute-list"),
    path("stations/", StationListView.as_view(), name="station-list"),
    path("areas/", AreaListView.as_view(), name="area-list"),
    path("readings/", ReadingListView.as_view(), name="reading-list"),
    path("readings/timestamps/", AvailableTimestampsView.as_view(), name="reading-timestamps"),
    path("readings/map/", AQIMapDataView.as_view(), name="reading-map"),
]