from django.core.management.base import BaseCommand
from twilio.rest import Client
import os
import requests

class Command(BaseCommand):
    help = 'Fetches weather and UV index and sends an SMS'

    def fetch_weather_and_uv(self):
        weather_api_key = os.environ.get('WEATHER_API_KEY')
        lat = os.environ.get('LATITUDE')
        lon = os.environ.get('LONGITUDE')
        weather_url = f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={weather_api_key}&units=imperial'
        uv_url = f'http://api.openweathermap.org/data/2.5/uvi?lat={lat}&lon={lon}&appid={weather_api_key}'

        try:
            weather_data = requests.get(weather_url).json()
            uv_data = requests.get(uv_url).json()
            print(weather_data)
            print("UV API Raw Response:", uv_data)

            if weather_data.get('cod') != 200:
                self.stdout.write(
                    self.style.ERROR(f"Weather API Error: {weather_data.get('message', 'Unknown error')}"))
                return None, None, None, f"Weather API Error: {weather_data.get('message', 'Unknown error')}"
            if 'value' not in uv_data:
                self.stdout.write(self.style.ERROR(f"UV API Error: {uv_data.get('message', 'Unknown error')}"))
                return None, None, None, f"UV API Error: {uv_data.get('message', 'Unknown error')}"

            temperature = weather_data['main']['temp']
            high = weather_data['main']['temp_max']
            low = weather_data['main']['temp_min']
            uv_index = uv_data['value']

            return temperature, high, low, uv_index

        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"An error occurred while fetching data: {e}"))
            return None, None, None, f"An error occurred while fetching data: {e}"

    def send_sms(self, temperature, high, low, uv_index):
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        client = Client(account_sid, auth_token)

        body = f"Good morning! Today's temperature is {temperature}°F, with a high of {high}°F and a low of {low}°F. The UV index is {uv_index}."

        message = client.messages.create(
            body=body,
            from_=os.environ.get('TWILIO_PHONE'),
            to=os.environ.get('RECIPIENT_PHONE')
        )

    def handle(self, *args, **kwargs):
        temperature, high, low, uv_index = self.fetch_weather_and_uv()
        if temperature is not None and high is not None and low is not None and uv_index is not None:
            self.send_sms(temperature, high, low, uv_index)
            self.stdout.write(self.style.SUCCESS('Successfully sent weather and UV index information.'))
        else:
            self.stdout.write(self.style.ERROR('Failed to fetch weather and UV index data.'))