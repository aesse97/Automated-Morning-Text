from django.core.management.base import BaseCommand
from twilio.rest import Client
import os
import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime
from weather_send.views import send_pushover_notification

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

    def fetch_random_fun_fact_from_api(self):
        limit = 1
        api_url = 'https://api.api-ninjas.com/v1/facts?limit={}'.format(limit)
        ninja_api_key = os.environ.get('NINJA_API_KEY')

        if not ninja_api_key:
            self.stdout.write(self.style.ERROR("NINJA_API_KEY not set in environment variables"))
            return None

        try:
            response = requests.get(api_url, headers={'X-Api-Key': ninja_api_key})
            if response.status_code == requests.codes.ok:
                facts = response.json()
                random_fact = random.choice(facts)
                return random_fact.get('fact', 'No fact available.')
            else:
                self.stdout.write(self.style.ERROR(f"Error fetching fun facts: {response.status_code} {response.text}"))
                return None
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"An error occurred while fetching fun facts: {e}"))
            return None

    def fetch_meme_url(self, tried_urls=set()):
        MEMEDROID_URL = "https://www.memedroid.com/memes/top/day"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            response = requests.get(MEMEDROID_URL, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                meme_articles = soup.find_all("article", class_="gallery-item")
                if not meme_articles:
                    self.stdout.write(self.style.ERROR('No memes found.'))
                    return None
                random.shuffle(meme_articles)
                for article in meme_articles:
                    meme_img = article.find("img", class_="img-responsive")
                    if meme_img and meme_img['src'] not in tried_urls:
                        print(f"Extracted meme URL: {meme_img['src']}")
                        tried_urls.add(meme_img['src'])
                        return meme_img["src"]
            else:
                self.stdout.write(
                    self.style.ERROR(f"Failed to fetch Memedroid page. Status code: {response.status_code}"))
                return None
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"An error occurred while fetching meme: {e}"))
            return None

    def fetch_meme_size(self, meme_url):
        try:
            response = requests.head(meme_url)
            meme_size = int(response.headers.get('Content-Length', 0))  # Size in bytes
            return meme_size
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"An error occurred while fetching meme size: {e}"))
            return 0

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

    def fetch_joke(self):
        joke_api_url = "https://v2.jokeapi.dev/joke/Any"
        joke_string = None

        try:
            response = requests.get(joke_api_url)
            if response.status_code == 200:
                joke_data = response.json()
                if joke_data['type'] == 'twopart':
                    joke_string = f"{joke_data['setup']} ... {joke_data['delivery']}"
                elif joke_data['type'] == 'single':
                    joke_string = joke_data['joke']
                return joke_string
            else:
                self.stdout.write(self.style.ERROR('Failed to fetch the joke.'))
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"An error occurred while fetching joke: {e}"))

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
        fun_fact = self.fetch_random_fun_fact_from_api()

        lat = os.environ.get('LAT2')
        lon = os.environ.get('LON2')
        phone_number = os.environ.get('RECIPIENT_PHONE4')
        recipient_name = os.environ.get('RECIPIENT_NAME4')

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
            f"Hey {recipient_name}, why did the chicken join a band? Because it had the drumsticks! Now, get up and rock your day! 🐔🥁",
            f"Morning, {recipient_name}! The aliens just called, they’re missing their leader. Beam up and take charge! 👽",
            f"Good morning, {recipient_name}! Ever tried to catch fog? Don't bother, I heard it's mist-ifying! 😂",
            f"Hey {recipient_name}, heard you've been knighted! Arise, Sir Laze-a-lot! ⚔️",
            f"Yo, {recipient_name}! Ever read a book on anti-gravity? It's impossible to put down, just like you! 📚",
            f"Morning, {recipient_name}! Wanna hear a construction joke? Oh, never mind, I'm still building it. Get up and build your day! 🏗️",
            f"Hey {recipient_name}, what did one wall say to the other? 'I'll meet you at the corner!' Time to turn your day around! 🏠",
            f"Good morning, {recipient_name}! How does Moses make his coffee? Hebrews it! Time to part your Red Sea of blankets! 🌊",
            f"Hey {recipient_name}, did you hear about the kidnapping at the playground? He woke up! Just like you need to! 😴",
            f"Morning, {recipient_name}! Why did the scarecrow win an award? Because he was outstanding in his field, just like you'll be today! 🌾",
            f"Hey {recipient_name}, what did one ocean say to the other? Nothing, they just waved. Time to make waves today! 🌊",
            f"Morning, {recipient_name}! What did the janitor say when he jumped out of the closet? 'Supplies!' Time to supply your awesomeness to the world! 🎉",
            f"Yo, {recipient_name}! What do you call fake spaghetti? An 'Impasta'! No faking today, rise and shine! 🍝",
            f"Hey {recipient_name}, what did one plate say to another plate? 'Lunch is on me!' Your day's on you, make it great! 🍽️",
            f"Good morning, {recipient_name}! Why did the golfer bring two pairs of pants? In case he got a hole in one. You got this one! ⛳"
        ]

        random_opener = random.choice(openers)

        day_temperature, min_temperature, max_temperature, summary = self.fetch_weather_and_uv(lat, lon)
        joke_string = self.fetch_joke()
        today_date_readable = datetime.now().strftime('%B %d, %Y')

        if all([day_temperature, min_temperature, max_temperature, summary]):
            body = (f"📆 Today is {today_date_readable}. \n"
                    f"{random_opener} \n"
                    f"Here's your daily scoop:\n"
                    f"🌡️ The day's looking to be about {day_temperature}°F. Expect highs of {max_temperature}°F and lows around {min_temperature}°F.\n"
                    f"☀️ Weather's saying: {summary}.\n"
                    f"🎉 And guess what? It's {holiday} today! \n"
                    f"🤓 Fun Fact of the Day: {fun_fact}.\n"
                    f"😂 Joke of the Day: {joke_string}.\n"
                    f"Make it a great one, {recipient_name}!")

            send_pushover_notification(f"Daily Update for {recipient_name}: {body}")

            meme_fits = False
            while not meme_fits:
                meme_url = self.fetch_meme_url()
                if meme_url:
                    meme_size = self.fetch_meme_size(meme_url)
                    text_size = len(body.encode('utf-8'))
                    total_size_mb = (meme_size + text_size) / (1024 * 1024)
                    print(f"Combined size (in MB) for URL {meme_url}: {total_size_mb}")
                    if total_size_mb < 5:
                        meme_fits = True
                        self.send_sms(phone_number, body, meme_url)
                        self.stdout.write(self.style.SUCCESS('Successfully sent.'))
                        return
                else:
                    break

            self.stdout.write(self.style.ERROR('Unable to find a suitable meme that fits within the size limit.'))