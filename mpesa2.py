from flask import Flask, request
import requests
from requests.auth import HTTPBasicAuth
import base64
from datetime import datetime

app = Flask(__name__)
my_endpoint = "https://4019-197-237-11-90.ngrok-free.app/"

@app.route("/prince")
def home():
    return "Hello it's Prince"

@app.route("/stkpush")
def MpesaExpress():
    amount = request.args.get('amount')
    phone = request.args.get('phone')

    endpoint = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    access_token = getAccessToken()
    headers = {"Authorization": "Bearer %s" % access_token}
    time = datetime.now()
    timestamp = time.strftime("%Y%m%d%H%M%S")
    password = "174379" + "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919" + timestamp
    password = base64.b64encode(password.encode('utf-8'))

    data = {
        "BusinessShortCode": "174379",
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": "174379",
        "PhoneNumber": phone,
        "CallBackURL": "https://fbec-197-237-11-90.ngrok-free.app/callback",
        "AccountReference": "VitapharmPayment",
        "TransactionDesc": "Test"
    }
    response = requests.post(endpoint, json=data, headers=headers)
    return response.json()

# mpesa-callback
@app.route("/callback", methods=["POST"])
def incoming():
    data = request.get_json()
    print(data)
    

# getAccessToken
def getAccessToken():
    consumer_key = "xyyfojxRcUqE57AMT1qAlc6WLKSXZGGzwUReLA2uCQAbmqaN"
    consumer_secret = "cl8uGswLYcvNAEQZDQxLBfadKxJXp8oMANWy4P8OTqdcT7V8vpDjckWyDxzAYwgZ"
    api_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r = requests.get(api_URL, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    my_access_token = r.json()['access_token']
    return my_access_token



if __name__ == "__main__": 
    app.run(debug=True)