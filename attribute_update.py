
import os
import sys
import csv
from datetime import datetime


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend_DT.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import django

django.setup()

from django.db import transaction
from django.utils.timezone import make_aware
from datamanage.models import Station, Reading, Area, Attribute, Threshold


def create_all_attributes():
    attributes_data = [
        {
            'key': 'aqi_index',
            'label': 'Air Quality Index',
            'unit': '',
            'thresholds': [
                {'max_value': 50, 'color': '#00E400', 'label': 'Good', 'order': 1},
                {'max_value': 100, 'color': '#FFFF00', 'label': 'Satisfactory', 'order': 2},
                {'max_value': 200, 'color': '#FF7E00', 'label': 'Moderate', 'order': 3},
                {'max_value': 300, 'color': '#FF0000', 'label': 'Poor', 'order': 4},
                {'max_value': 400, 'color': '#99004C', 'label': 'Very Poor', 'order': 5},
                {'max_value': float('inf'), 'color': '#7E0023', 'label': 'Severe', 'order': 6},
            ]
        },
        {
            'key': 'pm2_5',
            'label': 'PM2.5',
            'unit': 'µg/m³',
            'thresholds': [
                {'max_value': 30, 'color': '#00E400', 'label': 'Good', 'order': 1},
                {'max_value': 60, 'color': '#FFFF00', 'label': 'Satisfactory', 'order': 2},
                {'max_value': 90, 'color': '#FF7E00', 'label': 'Moderate', 'order': 3},
                {'max_value': 120, 'color': '#FF0000', 'label': 'Poor', 'order': 4},
                {'max_value': 250, 'color': '#99004C', 'label': 'Very Poor', 'order': 5},
                {'max_value': float('inf'), 'color': '#7E0023', 'label': 'Severe', 'order': 6},
            ]
        },
        {
            'key': 'pm10',
            'label': 'PM10',
            'unit': 'µg/m³',
            'thresholds': [
                {'max_value': 50, 'color': '#00E400', 'label': 'Good', 'order': 1},
                {'max_value': 100, 'color': '#FFFF00', 'label': 'Satisfactory', 'order': 2},
                {'max_value': 250, 'color': '#FF7E00', 'label': 'Moderate', 'order': 3},
                {'max_value': 350, 'color': '#FF0000', 'label': 'Poor', 'order': 4},
                {'max_value': 430, 'color': '#99004C', 'label': 'Very Poor', 'order': 5},
                {'max_value': float('inf'), 'color': '#7E0023', 'label': 'Severe', 'order': 6},
            ]
        },
        {
            'key': 'co',
            'label': 'Carbon Monoxide',
            'unit': 'ppm',
            'thresholds': [
                {'max_value': 1.0, 'color': '#00E400', 'label': 'Good', 'order': 1},
                {'max_value': 2.0, 'color': '#FFFF00', 'label': 'Satisfactory', 'order': 2},
                {'max_value': 10.0, 'color': '#FF7E00', 'label': 'Moderate', 'order': 3},
                {'max_value': 17.0, 'color': '#FF0000', 'label': 'Poor', 'order': 4},
                {'max_value': 34.0, 'color': '#99004C', 'label': 'Very Poor', 'order': 5},
                {'max_value': float('inf'), 'color': '#7E0023', 'label': 'Severe', 'order': 6},
            ]
        },
        {
            'key': 'no2',
            'label': 'Nitrogen Dioxide',
            'unit': 'ppb',
            'thresholds': [
                {'max_value': 40, 'color': '#00E400', 'label': 'Good', 'order': 1},
                {'max_value': 80, 'color': '#FFFF00', 'label': 'Satisfactory', 'order': 2},
                {'max_value': 180, 'color': '#FF7E00', 'label': 'Moderate', 'order': 3},
                {'max_value': 280, 'color': '#FF0000', 'label': 'Poor', 'order': 4},
                {'max_value': 400, 'color': '#99004C', 'label': 'Very Poor', 'order': 5},
                {'max_value': float('inf'), 'color': '#7E0023', 'label': 'Severe', 'order': 6},
            ]
        },
        {
            'key': 'temp_c',
            'label': 'Temperature',
            'unit': '°C',
            'thresholds': []
        },
        {
            'key': 'humidity',
            'label': 'Humidity',
            'unit': '%',
            'thresholds': []
        },
        {
            'key': 'pressure_mb',
            'label': 'Pressure',
            'unit': 'mb',
            'thresholds': []
        },
        {
            'key': 'windspeed_kph',
            'label': 'Wind Speed',
            'unit': 'km/h',
            'thresholds': []
        },
    ]

    print("Creating Attributes from CSV dataset...")

    for attr_data in attributes_data:
        attribute, created = Attribute.objects.update_or_create(
            key=attr_data['key'],
            defaults={
                'label': attr_data['label'],
                'unit': attr_data['unit']
            }
        )

        # Delete and recreate thresholds
        Threshold.objects.filter(attribute=attribute).delete()

        for threshold_data in attr_data['thresholds']:
            Threshold.objects.create(
                attribute=attribute,
                max_value=threshold_data['max_value'],
                color=threshold_data['color'],
                label=threshold_data['label'],
                order=threshold_data['order']
            )

        status = "Created" if created else "Updated"
        print(f"   {status}: {attribute.key} - {attribute.label} ({len(attr_data['thresholds'])} thresholds)")

    print(f"✅ Total Attributes: {Attribute.objects.count()}")


def parse_flexible_date(date_str, time_str):
    dt_str = f"{date_str} {time_str}"

    formats = [
        '%m/%d/%Y %H:%M',
        '%d/%m/%Y %H:%M',
        '%Y-%m-%d %H:%M',
        '%m/%d/%y %H:%M',
        '%d/%m/%y %H:%M',
        '%Y/%m/%d %H:%M',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Unable to parse date: {dt_str}")


def import_csv_data(csv_path):
    print("\n" + "=" * 50)
    print("📊 Importing CSV Data")
    print("=" * 50)

    # Get or create area
    area, created = Area.objects.get_or_create(
        name='Delhi',
        defaults={
            'geometry': {"type": "Polygon", "coordinates": [[]]},
            'properties': {"source": "CSV import"}
        }
    )
    print(f"📍 Area: {area.name} (created: {created})")

    station_cache = {}
    readings_to_create = []
    total_rows = 0
    inserted_count = 0
    skipped_count = 0

    with open(csv_path, 'r', encoding='utf-8') as f:
        total_rows = sum(1 for _ in f) - 1

    print(f"📄 Total rows to process: {total_rows}")

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, 1):
            try:
                # Parse date
                dt = parse_flexible_date(row['date'], row['time'])
                timestamp = make_aware(dt)

                # Get or create station
                station_name = row['location'].strip()
                if station_name not in station_cache:
                    station, created = Station.objects.get_or_create(
                        name=station_name,
                        defaults={
                            'lat': float(row['lat']),
                            'lon': float(row['lon']),
                            'area': area
                        }
                    )
                    station_cache[station_name] = station
                    if created:
                        print(f"   🏢 Created station: {station_name}")

                station = station_cache[station_name]

                # Create reading - CSV columns to model fields mapping
                reading = Reading(
                    station=station,
                    timestamp=timestamp,

                    # Weather data (CSV column → model field)
                    temp_c=float(row['temperature']) if row['temperature'] and row['temperature'].strip() else None,
                    humidity=float(row['humidity']) if row['humidity'] and row['humidity'].strip() else None,
                    pressure_mb=float(row['pressure']) if row['pressure'] and row['pressure'].strip() else None,
                    windspeed_kph=float(row['wind_speed']) if row['wind_speed'] and row['wind_speed'].strip() else None,
                    condition_text=row.get('condition', ''),

                    # AQI & Pollutants (CSV column → model field)
                    aqi_index=float(row['aqi']) if row['aqi'] and row['aqi'].strip() else None,
                    pm2_5=float(row['pm25']) if row['pm25'] and row['pm25'].strip() else None,
                    pm10=float(row['pm10']) if row['pm10'] and row['pm10'].strip() else None,
                    co=float(row['co']) if row['co'] and row['co'].strip() else None,
                    no2=float(row['no2']) if row['no2'] and row['no2'].strip() else None,
                )
                readings_to_create.append(reading)
                inserted_count += 1

                # Bulk insert every 1000 records
                if len(readings_to_create) >= 1000:
                    with transaction.atomic():
                        Reading.objects.bulk_create(
                            readings_to_create,
                            batch_size=500,
                            ignore_conflicts=True
                        )
                    print(f"   Progress: {row_num}/{total_rows} rows (Inserted: {inserted_count})")
                    readings_to_create = []

            except Exception as e:
                print(f"   ⚠️ Error at row {row_num}: {e}")
                skipped_count += 1
                continue

    # Insert remaining
    if readings_to_create:
        with transaction.atomic():
            Reading.objects.bulk_create(
                readings_to_create,
                batch_size=500,
                ignore_conflicts=True
            )

    print("\n" + "=" * 50)
    print(f"   Import Summary:")
    print(f"   Total rows: {total_rows}")
    print(f"   Inserted: {inserted_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Stations: {len(station_cache)}")
    print(f"   Readings: {Reading.objects.count()}")


def main():
    csv_path = 'cleaned_delhi_weather_aqi.csv'

    print("Starting Complete Data Import")
    print("=" * 50)

    # Step 1: Create Attributes
    print("\nStep 1: Creating Attributes")
    print("-" * 30)
    create_all_attributes()

    # Step 2: Import CSV Data
    print("\nStep 2: Importing CSV Data")
    print("-" * 30)
    import_csv_data(csv_path)

    print("\nImport Complete!")


if __name__ == "__main__":
    main()