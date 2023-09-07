from django.core.management.base import BaseCommand
from twilio.rest import Client
import os
import requests
from bs4 import BeautifulSoup
import random

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
            summary = today_forecast['summary']

            return day_temperature, min_temperature, max_temperature, summary

        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"An error occurred while fetching data: {e}"))
            return None, None, None, None, None

    def fetch_meme_url(self):
        meme_api_url = "https://meme-api.com/gimme"

        try:
            response = requests.get(meme_api_url)
            if response.status_code == 200:
                meme_data = response.json()
                if 'url' in meme_data:
                    return meme_data['url']
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"An error occurred while fetching meme: {e}"))

        return None

    def fetch_holiday(self):
        try:
            response = requests.get("https://www.holidaycalendar.io/what-holiday-is-today")
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                holiday_title_h3 = soup.find("h3", {"class": "card-link-title---hover-secondary-1"})

                if holiday_title_h3 is not None:
                    holiday_title = holiday_title_h3.text
                    return holiday_title
                else:
                    self.stdout.write(self.style.ERROR('Could not find h3 tag with the specific class.'))
            else:
                self.stdout.write(self.style.ERROR('Failed to fetch the webpage.'))
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"An error occurred while fetching holiday: {e}"))
        return None

    def send_sms(self, phone_number, body, meme_url):
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        client = Client(account_sid, auth_token)

        if meme_url:
            message = client.messages.create(
                body=body,
                from_=os.environ.get('TWILIO_PHONE'),
                to=phone_number,
                media_url=[meme_url]
            )
        else:
            message = client.messages.create(
                body=body,
                from_=os.environ.get('TWILIO_PHONE'),
                to=phone_number
            )

    def handle(self, *args, **kwargs):
        meme_url = self.fetch_meme_url()
        holiday = self.fetch_holiday()

        lat = os.environ.get('LAT1')
        lon = os.environ.get('LON1')
        phone_number = os.environ.get('RECIPIENT_PHONE1')
        recipient_name = os.environ.get('RECIPIENT_NAME1')

        openers = [
            f"Rise and shine, {recipient_name}! The world isn't going to take over itself! 🌞",
            f"Hey {recipient_name}, the early bird gets the worm, but the second mouse gets the cheese! 🧀",
            f"Good morning, {recipient_name}! The universe called; it wants its awesome back! 🌌",
            f"Hey {recipient_name}, time to wake up and smell the possibility! Or is that coffee? ☕",
            f"Yo, {recipient_name}! Time to rise and... ugh, I can't even, but you should! 💤",
            f"Top of the morning to you, {recipient_name}! Or bottom, depending on your sleep schedule. ⏰",
            f"Morning, {recipient_name}! The bed may be your temple, but it's time to leave the sanctuary! 🛏️",
            f"Hey {recipient_name}, ready to chase those dreams? You've got to wake up first! 🌠",
            f"Hello, {recipient_name}! Your bed might miss you, but your coffee maker is jealous! ☕",
            f"Up and at 'em, {recipient_name}! Your destiny isn’t going to fulfill itself! 🚀",
            f"Hey {recipient_name}, you're one in a melon! Time to rise and be fruitful! 🍉",
            f"Good morning, {recipient_name}! Time to beast, feast, and not be the least! 🦁",
            f"Hey {recipient_name}, you snooze, you lose! But coffee can help you win again! ⏰",
            f"Morning, {recipient_name}! Time to get up and doughnut the impossible! 🍩",
            f"Good morning, {recipient_name}! Wakey, wakey, eggs and... is that bacon I smell? 🍳",
            f"Hey {recipient_name}, rise and whine... just kidding, please don't whine! 😄",
            f"Whoa, {recipient_name}, you're up? I was just about to send the search party! 🕵️‍♂️",
            f"Morning, {recipient_name}! The bed's loss is the world's gain! 🌍",
            f"Hello, {recipient_name}! You're the 'avocado' to my 'toast' of good mornings! 🥑",
            f"Hey {recipient_name}, why did the human get out of bed? To read my message, of course! 🐔",
            f"Good morning, {recipient_name}! May your day be more fruitful than a basket of puppies! 🐶",
            f"Hey {recipient_name}, up yet? Your couch said it misses you but told you to go be productive first! 🛋️",
        ]

        random_opener = random.choice(openers)

        day_temperature, min_temperature, max_temperature, summary = self.fetch_weather_and_uv(lat, lon)

        if all([day_temperature, min_temperature, max_temperature, summary]):
            body = (f"{random_opener} \n"
                    f"Here's your daily scoop:\n"
                    f"🌡️ The day's looking to be about {day_temperature}°F. Expect highs of {max_temperature}°F and lows around {min_temperature}°F.\n"
                    f"☀️ Weather's saying: {summary}.\n"
                    f"🎉 And guess what? It's {holiday} today! \n"
                    f"Make it a great one, {recipient_name}!")

            self.send_sms(phone_number, body, meme_url)
            self.stdout.write(self.style.SUCCESS('Successfully sent.'))