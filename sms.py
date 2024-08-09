import os
from flask import Flask, request, jsonify
from twilio.rest import Client
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import random
from podio_utilis import authenticate_podio

app = Flask(__name__)

print("Starting script...")

csv_file = os.environ.get('CSV_FILE_PATH', '/Project_Files/CSV/Sms.csv')

# This will raise an error if the file can't be read, which will help diagnose the issue
try:
    data = pd.read_csv(csv_file)
    print("CSV loaded successfully")
except Exception as e:
    print(f"Error loading CSV: {e}")

print("Script finished")

account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

twilio_phone_numbers = [os.environ.get('TWILIO_PHONE_NUMBER')]

PODIO_CLIENT_ID = os.environ.get('PODIO_CLIENT_ID')
PODIO_CLIENT_SECRET = os.environ.get('PODIO_CLIENT_SECRET')
PODIO_USERNAME = os.environ.get('PODIO_USERNAME')
PODIO_PASSWORD = os.environ.get('PODIO_PASSWORD')

podio_client = authenticate_podio(PODIO_CLIENT_ID, PODIO_CLIENT_SECRET, PODIO_USERNAME, PODIO_PASSWORD)

initial_messages = [
    "Hey, is this {owner_name}? This is Derrick.",
    "Hi {owner_name}, Derrick here. Is this a good time to chat?",
    "Hello {owner_name}, it's Derrick. Are you available to talk?",
    "Hey {owner_name}, this is Derrick. Do you have a moment?",
    "Hi {owner_name}, Derrick speaking. Can we talk?",
    "Hello {owner_name}, Derrick here. Is now a good time?",
    "Hey {owner_name}, it's Derrick. Can we chat for a bit?",
    "Hi {owner_name}, Derrick. Got a minute to talk?",
    "Hello {owner_name}, this is Derrick. Are you free to chat?"
]

response_messages = [
    "great! did you have some time for a phone call? wanted to have a quick chat about your property.",
    "did you have some time for a phone call? wanted to discuss your property.",
    "can we have a quick chat about your property?",
    "can we talk about your property?",
    "do you have a few minutes for a call? would love to chat about your property.",
    "can we schedule a quick call to discuss your property?",
    "can we have a quick chat about your property?",
    "can we talk about your property for a few minutes?",
    "did you have some time for a phone call?"
]

follow_up_messages = [
    "just wanted to follow up, {owner_name}. did you have some time to discuss your property? if you'd rather not hear from me, just let me know.",
    "hi {owner_name}, checking in to see if you're available for a quick chat about your property. if you're not interested, just say so.",
    "hello {owner_name}, following up to see if we can discuss your property. if this isn't a good time, just let me know.",
    "hey {owner_name}, still interested in having a quick chat about your property. if you'd like to opt out, just reply with 'stop'.",
    "hi {owner_name}, do you have some time to talk about your property? if you'd rather not continue, just let me know.",
    "hello {owner_name}, checking if you're available for a brief call about your property. if you want to opt out, just let me know.",
    "hey {owner_name}, wanted to see if you have some time to chat about your property. if you're not interested, just reply 'stop'.",
    "hi {owner_name}, following up to see if we can discuss your property. if you'd like to opt out, please let me know.",
    "hello {owner_name}, did you have some time to chat about your property? if not, feel free to let me know."
]

phone_number = os.environ.get('TWILIO_PHONE_NUMBER')

scheduler = BackgroundScheduler()

def send_follow_up(to_number, owner_name, address):
    follow_up_message = random.choice(follow_up_messages).format(owner_name=owner_name, address=address)
    client.messages.create(body=follow_up_message, from_=phone_number, to=to_number)

@app.route('/send_sms', methods=['POST'])
def send_sms():
    now = datetime.now()
    start_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=19, minute=0, second=0, microsecond=0)
    if start_time <= now <= end_time:
        for i, row in data.iterrows():
            owner_name = row['Owner 1 First Name']
            address = row['Address']
            to_number = row['Owner 1 Phone Number']
            message_body = random.choice(initial_messages).format(owner_name=owner_name)
            client.messages.create(body=message_body, from_=phone_number, to=to_number)

            scheduler.add_job(send_follow_up, 'date', run_date=now + timedelta(days=7), args=[to_number, owner_name, address])

        time.sleep(720)
        return "Messages Sent!"

@app.route('/response_handler', methods=['POST'])
def response_handler():
    from_number = request.form['From']
    body = request.form['Body']
    if "yes" in body.lower() or "sure" in body.lower() or "yeah" in body.lower() or "okay" in body.lower():
        for i, row in data.iterrows():
            if row['Phone_Number'] == from_number:
                address = row['Address']
                response_message = random.choice(response_messages).format(address=address)
                client.messages.create(body=response_message, from_=phone_number, to=from_number)
                break
    elif "stop" in body.lower() or "unsubscribe" in body.lower():
        client.messages.create(body="Okay! You have been unsubscribed.")

def push_to_podio(podio_client, owner_name, from_number, address):
    item_data = {
        "fields": {
            "title": f"Lead for {address}",
            "name": owner_name,
            "phone_number": from_number,
            "address": address
        }
    }
    # Assuming you have a method to push data to Podio
    # podio_client.create_item(item_data)
