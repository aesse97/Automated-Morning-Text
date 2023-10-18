from django.core.management.base import BaseCommand
from twilio.rest import Client
import os

class Command(BaseCommand):
    help = 'Send a text to multiple phone numbers at once'

    def add_arguments(self, parser):
        parser.add_argument('message', type=str, help='The message to send')

    def handle(self, *args, **kwargs):
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        twilio_phone_number = os.environ.get('TWILIO_PHONE')

        phone_numbers = [
            os.environ.get('RECIPIENT_PHONE1'),
            os.environ.get('RECIPIENT_PHONE3'),
            os.environ.get('RECIPIENT_PHONE4'),
        ]

        client = Client(account_sid, auth_token)
        message_text = kwargs['message']

        for number in phone_numbers:
            if number:
                client.messages.create(
                    body=message_text,
                    from_=twilio_phone_number,
                    to=number
                )
                self.stdout.write(self.style.SUCCESS(f"Message sent to {number}"))