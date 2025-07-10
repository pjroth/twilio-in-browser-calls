import os
import pprint as p

from dotenv import load_dotenv
from flask import Flask, render_template, jsonify
from flask import request
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
from twilio.twiml.voice_response import VoiceResponse, Dial

load_dotenv()

account_sid = os.environ['TWILIO_ACCOUNT_SID']
api_key = os.environ['TWILIO_API_KEY_SID']
api_key_secret = os.environ['TWILIO_API_KEY_SECRET']
twiml_app_sid = os.environ['TWIML_APP_SID']
twilio_number = os.environ['TWILIO_NUMBER']

app = Flask(__name__)


@app.route('/')
def home():
    return render_template(
        'home.html',
        title="In browser calls",
    )


@app.route('/token', methods=['GET'])
def get_token():
    # Require user_id parameter
    user_id = request.args.get('user_id')
    if not user_id:
        # Return error if user_id is not provided
        response = jsonify({'error': 'user_id parameter is required'})
        response.status_code = 400
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    identity = user_id
    outgoing_application_sid = twiml_app_sid

    access_token = AccessToken(account_sid, api_key,
                               api_key_secret, identity=identity)

    voice_grant = VoiceGrant(
        outgoing_application_sid=outgoing_application_sid,
        incoming_allow=True,
    )
    access_token.add_grant(voice_grant)

    response = jsonify(
        {'token': access_token.to_jwt(), 'identity': identity})
    response.headers.add('Access-Control-Allow-Origin', '*')

    return response


@app.route('/handle_calls', methods=['POST'])
def call():
    p.pprint(request.form)
    response = VoiceResponse()
    
    # Get identity from the request (should be the user_id)
    identity = request.form.get('From', twilio_number)
    
    dial = Dial(callerId=identity)

    if 'To' in request.form and request.form['To'] != twilio_number:
        # Get the 'To' value
        to_value = request.form['To']
        
        # For our use case, we're going to treat all values as client identifiers
        # unless they explicitly match the full phone number format with country code
        if to_value.startswith('+') and to_value[1:].isdigit() and len(to_value) >= 10:
            # This is definitely a PSTN call to a phone number with country code
            print('outbound call to phone number')
            dial.number(to_value)
        else:
            # This is a client-to-client call
            print(f'outbound client-to-client call to: {to_value}')
            dial.client(to_value)
    else:
        print('incoming call')
        caller = request.form['Caller']
        dial = Dial(callerId=caller)
        dial.client(identity)

    return str(response.append(dial))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, debug=True)
