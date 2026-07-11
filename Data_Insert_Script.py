# Data_Insert_Script.py
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
from datamanage.models import Station, Reading, Area  # আপনার app নাম দিন


def parse_flexible_date(date_str, time_str):

    dt_str = f"{date_str} {time_str}"

    formats = [
        '%m/%d/%Y %H:%M',  # MM/DD/YYYY HH:MM (US format)
        '%d/%m/%Y %H:%M',  # DD/MM/YYYY HH:MM (EU format)
        '%Y-%m-%d %H:%M',  # YYYY-MM-DD HH:MM
        '%m/%d/%y %H:%M',  # MM/DD/YY HH:MM
        '%d/%m/%y %H:%M',  # DD/MM/YY HH:MM
        '%Y/%m/%d %H:%M',  # YYYY/MM/DD HH:MM
    ]

    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Unable to parse date: {dt_str}")


def is_us_format(date_str):
    try:
        parts = date_str.split('/')
        if len(parts) == 3:
            month = int(parts[0])
            day = int(parts[1])
            if month > 12:
                return False
            if day > 12:
                return True
        return True  # default US format
    except:
        return True


def import_csv_using_orm(csv_path):
    area, created = Area.objects.get_or_create(
        name='Delhi',
        defaults={
            'geometry': {"type": "Polygon", "coordinates": [[]]},
            'properties': {"source": "CSV import"}
        }
    )
    print(f"Area: {area.name} (created: {created})")

    station_cache = {}
    readings_to_create = []
    total_rows = 0
    inserted_count = 0
    skipped_count = 0
    error_rows = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        total_rows = sum(1 for _ in f) - 1

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, 1):
            try:
                dt = parse_flexible_date(row['date'], row['time'])
                timestamp = make_aware(dt)


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
                        print(f"Created station: {station_name}")

                station = station_cache[station_name]


                reading = Reading(
                    station=station,
                    timestamp=timestamp,
                    temp_c=float(row['temperature']) if row['temperature'] and row['temperature'].strip() else None,
                    humidity=float(row['humidity']) if row['humidity'] and row['humidity'].strip() else None,
                    pressure_mb=float(row['pressure']) if row['pressure'] and row['pressure'].strip() else None,
                    windspeed_kph=float(row['wind_speed']) if row['wind_speed'] and row['wind_speed'].strip() else None,
                    condition_text=row.get('condition', ''),
                    aqi_index=float(row['aqi']) if row['aqi'] and row['aqi'].strip() else None,
                    pm2_5=float(row['pm25']) if row['pm25'] and row['pm25'].strip() else None,
                    pm10=float(row['pm10']) if row['pm10'] and row['pm10'].strip() else None,
                    co=float(row['co']) if row['co'] and row['co'].strip() else None,
                    no2=float(row['no2']) if row['no2'] and row['no2'].strip() else None,
                )
                readings_to_create.append(reading)
                inserted_count += 1


                if len(readings_to_create) >= 1000:
                    with transaction.atomic():
                        Reading.objects.bulk_create(
                            readings_to_create,
                            batch_size=500,
                            ignore_conflicts=True
                        )
                    print(
                        f"Progress: {row_num}/{total_rows} rows, Inserted: {inserted_count}, Skipped: {skipped_count}")
                    readings_to_create = []

            except Exception as e:
                error_msg = f"Row {row_num}: {e} | Date: {row['date']} {row['time']}"
                print(f"Error: {error_msg}")
                error_rows.append(error_msg)
                skipped_count += 1
                continue


    if readings_to_create:
        with transaction.atomic():
            Reading.objects.bulk_create(
                readings_to_create,
                batch_size=500,
                ignore_conflicts=True
            )

    print(f"\n{'=' * 50}")
    print(f"   Import complete!")
    print(f"   Total rows processed: {total_rows}")
    print(f"   Successfully inserted: {inserted_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Total stations: {len(station_cache)}")

    if error_rows:
        print(f"\n  First 10 errors:")
        for err in error_rows[:10]:
            print(f"   - {err}")
        if len(error_rows) > 10:
            print(f"   ... and {len(error_rows) - 10} more errors")


if __name__ == "__main__":
    import_csv_using_orm('cleaned_delhi_weather_aqi.csv')