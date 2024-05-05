from flask import Flask, request
from flask_mpesa import MpesaAPI
import logging

# Initialize Flask app
app = Flask(__princedaraja__)

# Set API environment to "sandbox" remembere to change to  "production" before you commit or deploy
app.config["API_ENVIRONMENT"] = "sandbox"
app.config["APP_KEY"] = "..."
app.config["APP_SECRET"] = "..."

# Initialize Flask-Mpesa extension
mpesa_api = MpesaAPI(app)

# Callback URL from Safaricom Developer Portal
CALLBACK_URL = "https://your-domain.com/callback"

# Configure logging
logging.basicConfig(filename='mpesa.log', level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

# Route to handle STK Push requests
@app.route("/stkpush", methods=["POST"])
def stk_push():
    try:
        # Get user data from request form
        phone_number = request.form.get("phone_number")
        amount = request.form.get("amount")
        
        # Validate input
        if not phone_number or not amount:
            return "Missing phone number or amount", 400
        
        # Convert amount to float
        amount = float(amount)
        
        # Build MpesaSTKPush object using Flask-Mpesa
        stk_push = mpesa_api.STKPush(
            phone_number=phone_number,
            amount=amount,
            account_reference="here you can keep thecode for your own records",  # Optional reference for your records
            transaction_desc="Payment for whatever order it is, be specific at least",  # Optional transaction description
            callback_url=CALLBACK_URL
        )

        # Initiate the Mpesa transaction
        response = stk_push.perform()
        
        # Log transaction initiation
        logging.info(f"STK Push initiated for {phone_number} with amount {amount}")
        
        # Handle successful transaction initiation (response contains transaction details)
        return f"STK Push initiated successfully! Response: {response}"
    except Exception as e:
        # Log error
        logging.error(f"Error initiating STK Push: {str(e)}")
        # Handle errors during transaction initiation
        return f"Error initiating STK Push: {str(e)}", 500


# Route to handle Mpesa callback notifications
@app.route("/callback", methods=["POST"])
def mpesa_callback():
    try:
        # Validate and process Mpesa callback data using Flask-Mpesa
        data = mpesa_api.validate_and_parse_callback_data(request.data)
        
        # Extract relevant data from callback (e.g., transaction status, amount)
        transaction_status = data.get("ResultCode")
        
        if transaction_status == 0:
            # Log successful transaction
            logging.info("Transaction Successful")
            # Handle successful transaction (update order status, etc.)
            return "Success! Transaction completed."
        else:
            # Log failed transaction
            logging.warning(f"Transaction Failed. Result Code: {transaction_status}")
            # Handle failed transaction
            return f"Transaction Failed. Result Code: {transaction_status}", 400
    except Exception as e:
        # Log error
        logging.error(f"Error processing Mpesa callback: {str(e)}")
        # Handle errors during callback processing
        return f"Error processing Mpesa callback: {str(e)}", 500


# Run the Flask app
#  TODO: #USE THE CORRECT NAME HERE
if __name__ == "__main__": 
    app.run(debug=True)


# TODO: #REMEMBER TO CHANGE TO PRODUCTION BEFORE YOU COMMIT OR DEPLOY OR SHIP THE UPDATES
#ALSO REMOVE LOGGING BEFORE YOU COMMIT