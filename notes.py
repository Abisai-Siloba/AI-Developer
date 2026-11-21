import africastalking
import os
from dotenv import load_dotenv

'''
# Sandbox credentials
username = os.getenv("SMS_USERNAME")
api_key = os.getenv("SMS_API_KEY")
africastalking.initialize(username, api_key)

sms = africastalking.SMS


# Must match the phone number connected in your open Simulator tab
recipients = ["+254733729615"]
message = "Sandbox test message\nWeekly reminder!"
sender_id = "mautumaone"  # Must match the Sender ID you created in Step 1

try:
    response = sms.send(message, recipients, sender_id)
    print(response)
except Exception as e:
    print(f"Error: {e}")
'''
    

# live api
import africastalking

# Replace with your Live App credentials
username = os.getenv("SMSLIVE_USERNAME")
api_key = os.getenv("SMSLIVE_API_KEY")

africastalking.initialize(username, api_key)
sms = africastalking.SMS

# Omit the 3rd parameter (sender_id) to use the default live Sender ID
try:
    response = sms.send("Hello from my Live Python App!", ["+254733729615"])
    print(response)
except Exception as e:
    print(f"Error: {e}")