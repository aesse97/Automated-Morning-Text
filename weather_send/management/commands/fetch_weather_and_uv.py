from django.core.management.base import BaseCommand
from twilio.rest import Client
import os
import requests


class Command(BaseCommand):
    help = 'Fetches weather and UV index and sends an SMS'

    def fetch_weather_and_uv(self, lat, lon):
        weather_api_key = os.environ.get('WEATHER_API_KEY')
        one_call_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=current,minutely,hourly&appid={weather_api_key}&units=imperial"

        try:
            one_call_data = requests.get(one_call_url).json()
            today_forecast = one_call_data.get('daily', [{}])[0]
            print(today_forecast)

            if not today_forecast:
                self.stdout.write(self.style.ERROR('Failed to fetch weather data.'))
                return None, None, None, None, None

            day_temperature = round(today_forecast['temp']['day'])
            min_temperature = round(today_forecast['temp']['min'])
            max_temperature = round(today_forecast['temp']['max'])
            uv_index = round(today_forecast['uvi'])
            summary = today_forecast['summary']

            return day_temperature, min_temperature, max_temperature, uv_index, summary

        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"An error occurred while fetching data: {e}"))
            return None, None, None, None, None

    def send_sms(self, phone_numbers, day_temperature, min_temperature, max_temperature, uv_index, summary):
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        client = Client(account_sid, auth_token)

        body = (f"Good morning! Today's temperature is {day_temperature}°F, "
                f"with a high of {max_temperature}°F and a low of {min_temperature}°F. "
                f"The UV index is {uv_index}. Summary: {summary}.")

        for number in phone_numbers:
            message = client.messages.create(
                body=body,
                from_=os.environ.get('TWILIO_PHONE'),
                to=number
            )

    def handle(self, *args, **kwargs):
        locations_and_numbers = [
            {'lat': os.environ.get('LAT1'), 'lon': os.environ.get('LON1'),
             'numbers': [os.environ.get('RECIPIENT_PHONE1'), os.environ.get('RECIPIENT_PHONE2')]},
            {'lat': os.environ.get('LAT2'), 'lon': os.environ.get('LON2'),
             'numbers': [os.environ.get('RECIPIENT_PHONE3')]}
        ]
        for loc in locations_and_numbers:
            day_temperature, min_temperature, max_temperature, uv_index, summary = self.fetch_weather_and_uv(loc['lat'], loc['lon'])

            if all([day_temperature, min_temperature, max_temperature, uv_index, summary]):
                self.send_sms(loc['numbers'], day_temperature, min_temperature, max_temperature, uv_index, summary)
                self.stdout.write(self.style.SUCCESS('Successfully sent weather and UV index information.'))