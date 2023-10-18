from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from twilio.twiml.messaging_response import MessagingResponse
import os
import openai

openai.api_key = os.environ.get('OPENAI_API_KEY')
ENGINE = "gpt-3.5-turbo"
CUSTOM_REPLY_TRIGGER = os.environ.get('CUSTOM_REPLY_TRIGGER')

@csrf_exempt
def sms_reply(request):
    user_message = request.POST.get("Body")

    if user_message.strip().lower() == CUSTOM_REPLY_TRIGGER:
        ai_reply = "Rude"
    else:
        ai_reply = generate_ai_response(user_message)

    response = MessagingResponse()
    response.message(ai_reply)

    return HttpResponse(str(response))

def generate_ai_response(prompt):
    messages = [
        {"role": "system", "content": "You are a funny helpful assistant."},
        {"role": "user", "content": prompt}
    ]

    response = openai.ChatCompletion.create(
        model=ENGINE,
        messages=messages
    )

    assistant_message = response.choices[0].message.content

    return assistant_message.strip()
