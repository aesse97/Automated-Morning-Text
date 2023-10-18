from django.core.management.base import BaseCommand
from twilio.rest import Client
import os
import requests
from weather_send.views import send_pushover_notification

class Command(BaseCommand):
    help = 'Fetches weather and UV index and sends an SMS'

    def fetch_weather_and_uv(self):
        weather_api_key = os.environ.get('WEATHER_API_KEY')
        lat = os.environ.get('LAT1')
        lon = os.environ.get('LON1')
        one_call_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=current,minutely,hourly&appid={weather_api_key}&units=imperial"

        try:
            one_call_data = requests.get(one_call_url).json()
            today_forecast = one_call_data.get('daily', [{}])[0]

            if not today_forecast:
                self.stdout.write(self.style.ERROR('Failed to fetch weather data.'))
                return None, None, None, None, None

            day_temperature = round(today_forecast.get('temp', {}).get('day', "N/A"))
            min_temperature = round(today_forecast.get('temp', {}).get('min', "N/A"))
            max_temperature = round(today_forecast.get('temp', {}).get('max', "N/A"))
            summary = today_forecast.get('summary', "N/A")

            return day_temperature, min_temperature, max_temperature, summary

        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"An error occurred while fetching data: {e}"))
            return None, None, None, None, None

    def send_sms(self, day_temperature, min_temperature, max_temperature, summary):
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        client = Client(account_sid, auth_token)

        recipient_numbers = [os.environ.get('RECIPIENT_PHONE2')]

        body = (f"Good morning! Today's temperature is {day_temperature}°F, "
                f"with a high of {max_temperature}°F and a low of {min_temperature}°F. "
                f"{summary}.")

        for number in recipient_numbers:
            message = client.messages.create(
                body=body,
                from_=os.environ.get('TWILIO_PHONE'),
                to=number
            )

        send_pushover_notification(f"Daily update: {body}")

    def handle(self, *args, **kwargs):
        day_temperature, min_temperature, max_temperature, summary = self.fetch_weather_and_uv()
        if all([day_temperature, min_temperature, max_temperature, summary]):
            self.send_sms(day_temperature, min_temperature, max_temperature, summary)
            self.stdout.write(self.style.SUCCESS('Successfully sent weather and UV index information.'))
        else:
            self.stdout.write(self.style.ERROR('Failed to fetch weather and UV index data.'))