from praytimes import PrayTimes
from datetime import datetime, timedelta
from typing import List, Dict


class ShalatSchedule:
    # Adjusted to jadwalsholat.org
    DEFAULT_SETTINGS = {
        'imsak': '10 min', 
        'dhuhr': '2 min', 
        'asr': 1.02, 
        'highLats': 'NightMiddle',
        'fajr': 19.5, 
        'isha': 18.7, 
        'maghrib': 1.5, 
        'midnight': 'Jafari', 
        'ashar': 51
    }

    def __init__(self, lat: float, lon: float, method: str = 'UmmAlQura'):
        """
        Initialize the prayer times calculator.

        :param lat: Latitude of the location.
        :param lon: Longitude of the location.
        :param method: Calculation method (default: UmmAlQura).
        """
        self.lat = lat
        self.lon = lon
        self.method = method
        self.pray_times = PrayTimes(self.method)  # Create a PrayTimes instance
        self.pray_times.adjust(self.DEFAULT_SETTINGS)

    def adjust(self, params: dict):
        """
        Adjust the configuration to calculate prayertimes angle.

        :param params: Parameter to adjust the configurations
        """
        self.pray_times.adjust(params)

    def get_schedule(self, months: int, timezone: int = 0) -> List[Dict[str, str]]:
        """
        Generate a prayer time schedule for a specific time range.

        :param months: Number of months from today.
        :param timezone: Timezone offset (default: 0 for UTC).
        :return: A list of dictionaries with prayer times for each day.
        """
        start_date = datetime.now()
        # Approximate 30 days per month
        end_date = start_date + timedelta(days=months * 30)
        schedule = []

        current_date = start_date
        while current_date <= end_date:
            # Convert date to tuple format required by praytimes (YYYY, MM, DD)
            date_tuple = (current_date.year,
                          current_date.month, current_date.day)

            # Get prayer times
            times = self.pray_times.getTimes(
                date_tuple, (self.lat, self.lon), timezone)

            # Append to schedule
            schedule.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'imsak': times['imsak'],
                'fajr': times['fajr'],
                'sunrise': times['sunrise'],
                'dhuhr': times['dhuhr'],
                'asr': times['asr'],
                'sunset': times['sunset'],
                'maghrib': times['maghrib'],
                'isha': times['isha'],
                'midnight': times['midnight']
            })

            # Move to the next day
            current_date += timedelta(days=1)

        return schedule


def bulk_create_prayer_times(mosque_id, shalat_times):
    """
    Bulk create PrayerTime records from the shalat_times list.

    :param mosque_id: The ID of the mosque.
    :param shalat_times: A list of dictionaries containing prayer times.
    """
    from api.models import Mosque, PrayerTime
    from datetime import datetime
    mosque = Mosque.objects.get(id=mosque_id)  # Fetch the mosque instance

    prayer_times_objects = [
        PrayerTime(
            mosque=mosque,
            date=datetime.strptime(day["date"], "%Y-%m-%d").date(),
            imsak=datetime.strptime(day["imsak"], "%H:%M").time(),
            fajr=datetime.strptime(day["fajr"], "%H:%M").time(),
            sunrise=datetime.strptime(day["sunrise"], "%H:%M").time(),
            dhuhr=datetime.strptime(day["dhuhr"], "%H:%M").time(),
            asr=datetime.strptime(day["asr"], "%H:%M").time(),
            sunset=datetime.strptime(day["sunset"], "%H:%M").time(),
            maghrib=datetime.strptime(day["maghrib"], "%H:%M").time(),
            isha=datetime.strptime(day["isha"], "%H:%M").time(),
            midnight=datetime.strptime(day["midnight"], "%H:%M").time()
        )
        for day in shalat_times
    ]

    # Bulk create prayer times
    PrayerTime.objects.bulk_create(prayer_times_objects)

    print(
        f"✅ Successfully inserted {len(prayer_times_objects)} prayer times for mosque {mosque.name}")


def run(mosque_id, months=1):
    from api.models import Mosque, PrayerTime
    mosque = Mosque.objects.get(pk=mosque_id)
    schedule = ShalatSchedule(mosque.latitude, mosque.longitude)
    schedule_data = schedule.get_schedule(months, 7)
    bulk_create_prayer_times(mosque_id, schedule_data)
