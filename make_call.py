import os
from twilio.rest import Client

acc_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
client = Client(acc_sid,auth_token)

call = client.calls.create(
                        url='http://demo.twilio.com/docs/voice.xml',
                        to=os.environ.get('MY_PHONE_NUMBER'),
                        from_=os.environ.get('TWILIO_PHONE_NUMBER')
                    )

print(call.sid)
