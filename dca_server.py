import time
import hmac
import hashlib
import requests
import configures
import pandas as pd
import pytz
from datetime import datetime

# Replace with your Bitkub API credentials

def order_thb_to_btc(API_KEY,API_SECRET,AMOUNT):
    def generate_signature(timestamp, method, path, payload=None):
        message = f"{timestamp}{method}{path}"
        if payload:
            message += payload
        signature = hmac.new(
            API_SECRET.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def get_current_price(symbol):
        endpoint = "/api/v3/market/ticker"
        url = BASE_URL + endpoint

        params = {
            "sym": symbol
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return data[0]
        else:
            return {
                "error": response.status_code,
                "message": response.text
            }

    def place_market_buy_order(type,thb_amount):
        price_info = get_current_price(type)
        if isinstance(price_info, dict) and price_info.get("last"):
            btc_price = float(price_info["last"])
            btc_amount = thb_amount / btc_price

            endpoint = "/api/v3/market/place-bid"
            url = BASE_URL + endpoint

            payload = {
                "sym": "btc_thb",
                "amt": thb_amount,
                "rat": 0,  # Market price
                "typ": "market",
                "client_id" : "dca"
            }

            payload_json = str(payload).replace("'", '\"')  # Ensure JSON format

            timestamp = int(time.time() * 1000)
            signature = generate_signature(timestamp, "POST", endpoint, payload_json)

            headers = {
                "X-BTK-APIKEY": API_KEY,
                "X-BTK-TIMESTAMP": str(timestamp),
                "X-BTK-SIGN": signature,
                "Content-Type": "application/json",
            }

            response = requests.post(url, headers=headers, json=payload)
            return response.json()
        else:
            return "Error: Unable to fetch BTC price."

    BASE_URL = "https://api.bitkub.com"
    # API_KEY = configures.api_key
    # API_SECRET = configures.api_secret

    # THB to BTC :: Place market buy order with 100 THB
    market_buy_result = place_market_buy_order("btc_thb",AMOUNT)
    return market_buy_result


DCA_COMPLETE = False

print('Bitkub DCA Start!!!....')

while True:
    # check time is 0700
    thailand_timezone = pytz.timezone('Asia/Bangkok')
    current_time_thailand = datetime.now(thailand_timezone)
    if current_time_thailand.strftime('%H%M') == '0700' and not DCA_COMPLETE:
        print("Start DCA",'-'*100)


        # Fence data from Google Sheet
        url = "https://script.google.com/macros/s/AKfycbyFzLMucsNlowRBoFAtQ8l1E8_qZK06xU8-sduGuWQQFFdEXB10km0TuThopDx03ZHoNw/exec"
        params = {
            "function": "doGetAll",  # Ensure the correct function name matches your script
            "sheetName": "Sheet1"    # Replace with the actual sheet name
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise an error for bad status codes
            data = response.json()
            if data["status"] == "success":
                df = pd.DataFrame(data["data"])
                print("DataFrame created successfully:")
            else:
                print(f"Error: {data['message']}")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching the data: {e}")

        # print(df)
        for index, row in df.iterrows():
            print('\nDCA::::::::',row['EMAIL'],row['API_KEY'],row['API_SECRET'],row['DCA_AMOUNT'])

            API_KEY = row['API_KEY']
            API_SECRET = row['API_SECRET']
            r = order_thb_to_btc(API_KEY,API_SECRET,row['DCA_AMOUNT'])
            print(r)
        
        DCA_COMPLETE = True

    if current_time_thailand.strftime('%H%M') == '0730':
        DCA_COMPLETE = False

    # else:
    #     print(f"The current time in Thailand is {current_time_thailand.strftime('%H:%M')}. It's not 07:10 yet.")


        

        
