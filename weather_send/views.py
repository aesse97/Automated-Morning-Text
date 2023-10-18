from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from twilio.twiml.messaging_response import MessagingResponse
import os
import openai
import requests

openai.api_key = os.environ.get('OPENAI_API_KEY')
ENGINE = "gpt-3.5-turbo"
CUSTOM_REPLY_TRIGGER = os.environ.get('CUSTOM_REPLY_TRIGGER')

@csrf_exempt
def sms_reply(request):
    user_message = request.POST.get("Body")
    sender_number = request.POST.get("From")

    if user_message.strip().lower() == CUSTOM_REPLY_TRIGGER:
        ai_reply = "Rude"
    else:
        ai_reply = generate_ai_response(user_message)

    notification_message = f"New message from {sender_number}: {user_message}"
    send_pushover_notification(notification_message)

    response = MessagingResponse()
    response.message(ai_reply)

    return HttpResponse(str(response))

def generate_ai_response(prompt):
    messages = [
        {"role": "system", "content": "You are a funny helpful assistant who enjoys making comedy."},
        {"role": "user", "content": prompt}
    ]

    response = openai.ChatCompletion.create(
        model=ENGINE,
        messages=messages
    )

    assistant_message = response.choices[0].message.content

    return assistant_message.strip()

def send_pushover_notification(message):
    pushover_url = "https://api.pushover.net/1/messages.json"
    pushover_payload = {
        "token": os.environ.get('PUSHOVER_APP_TOKEN'),
        "user": os.environ.get('PUSHOVER_USER_KEY'),
        "message": message
    }
    response = requests.post(pushover_url, data=pushover_payload)
    if response.status_code != 200:
        print(f"Failed to send Pushover notification. Error: {response.text}")
