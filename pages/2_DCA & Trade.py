import streamlit as st
import time
import hmac
import hashlib
import requests
import extra_streamlit_components as stx
import configures
import ast
import json
import pandas as pd
from datetime import datetime
from datetime import timedelta

st.set_page_config(
    page_title="BitkubDca",
    page_icon="👋",
)
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

if 'person_data' not in st.session_state:
    st.session_state.person_data = None

cookie_manager = stx.CookieManager()
person_id = cookie_manager.get(cookie='person_id')
st.sidebar.success(person_id)

def get_server_time():
    """
    Fetch the current server time from the Bitkub API.
    """
    BASE_URL = "https://api.bitkub.com"
    endpoint = "/api/v3/servertime"
    url = BASE_URL + endpoint

    response = requests.get(url)
    if response.status_code == 200:
        return int(response.text)  # Assuming the server time is returned as a Unix timestamp
    else:
        st.error("Error fetching server time!")
        return None


def get_all_trade_history(API_KEY,API_SECRET,symbol, start=None, end=None, limit=100):

    BASE_URL = "https://api.bitkub.com"

    endpoint = "/api/v3/market/my-order-history"
    url = BASE_URL + endpoint

    timestamp = int(time.time() * 1000)
    params = {
        "sym": symbol,
        "p": 1,
        "lmt": limit
    }
    if start:
        params["start"] = start
    if end:
        params["end"] = end

    # Generate signature
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    signature_string = f"{timestamp}GET{endpoint}?{query_string}"
    signature = hmac.new(API_SECRET.encode(), signature_string.encode(), hashlib.sha256).hexdigest()

    headers = {
        "X-BTK-APIKEY": API_KEY,
        "X-BTK-TIMESTAMP": str(timestamp),
        "X-BTK-SIGN": signature,
        "Content-Type": "application/json",
    }

    all_trades = []
    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print("Error fetching trade history:", response.text)
            break

        data = response.json()
        if data.get("error") != 0:
            print("API Error:", data)
            break

        trades = data.get("result", [])
        if not trades:
            break

        all_trades.extend(trades)

        # Pagination logic
        pagination = data.get("pagination", {})
        if "next" not in pagination or not pagination["next"]:
            break

        params["p"] = pagination["next"]

        time.sleep(0.2)  # Respect rate limits

    return all_trades

st.write("# DCA & Trade! 👋")
if person_id:
    API_URL = configures.api_url 
    params = {
        "EMAIL": person_id
    }

    if not st.session_state.person_data:
        with st.spinner('Waiting'):
            response = requests.get(API_URL, params=params)
            if response.status_code == 200:
                st.session_state.person_data = response.json()
            else:
                st.session_state.person_data = None

    if st.session_state.person_data['status'] == 'error':
        API_KEY = ""
        API_SECRET = ""
        DCA_AMOUNT = 0
        TRADES = [[0,0,0],[0,0,0],[0,0,0]]
    else:
        API_KEY = st.session_state.person_data['data']['API_KEY']
        API_SECRET = st.session_state.person_data['data']['API_SECRET']
        API_SECRET = st.session_state.person_data['data']['API_SECRET']
        DCA_AMOUNT = st.session_state.person_data['data']['DCA_AMOUNT']
        TRADE1 = st.session_state.person_data['data']['TRADE1']
        TRADE2 = st.session_state.person_data['data']['TRADE2']
        TRADE3 = st.session_state.person_data['data']['TRADE3']

        TRADES = [TRADE1,TRADE2,TRADE3]

        for i in range(len(TRADES)):
            if TRADES[i]:
                TRADES[i] = ast.literal_eval(TRADES[i])
            else:
                TRADES[i] = [0,0,0]

    LIST_MENUS  = ['Setup','DCA','Trade']
    tab1,tab2,tab3 = st.tabs(LIST_MENUS)
        
    api_key = tab1.text_input("API_KEY :",API_KEY)
    api_secret = tab1.text_input("API_SECRET :", API_SECRET,type="password")

    if tab1.button("Update"):
        with st.spinner('Waiting'):
            payload = {
                "EMAIL": person_id,
                "API_KEY": api_key,
                "API_SECRET": api_secret,
            }
            response = requests.post(API_URL, json=payload)

            tab1.write('update complete!')

    dca_amount = tab2.number_input("DCA_AMOUNT :",value=DCA_AMOUNT,min_value=0,max_value=None,key=f"dca")

    if tab2.button("Update!"):
        with st.spinner('Waiting'):
            payload = {
                "EMAIL": person_id,
                "DCA_AMOUNT": dca_amount
            }
            response = requests.post(API_URL, json=payload)
            tab2.write('update complete!')

    tab2.write("## Historys")
    all_trades = get_all_trade_history(API_KEY,API_SECRET,"btc_thb")
    if all_trades:
        # st.write(all_trades)
        df_historys = pd.DataFrame(all_trades)

        # Adjust `ts` with server time
        if 'ts' in df_historys.columns:
            server_time = get_server_time()
            df_historys['adjusted_ts'] = df_historys['ts'] - (server_time - int(time.time() * 1000))
            df_historys['datetime'] = pd.to_datetime(df_historys['adjusted_ts'], unit='ms')
            df_historys['datetime'] = df_historys['datetime'] + timedelta(hours=7)

        df_history_dca = df_historys[df_historys['client_id'] == 'dca']
        df_history_dca.set_index('datetime', inplace=True)
        df_history_dca = df_history_dca[['side', 'type', 'rate', 'fee', 'amount']]
        df_history_dca['rate'] = df_history_dca['rate'].astype(float)
        df_history_dca['rate'] = df_history_dca['rate'].apply(lambda x: f"{x:,.2f}")
        tab2.write(df_history_dca)
    else:
        tab2.write("No trade history available.")


    #tab3 Trade
    cols = tab3.tabs(['Bot1','Bot2','Bot3'])
    for i in range(len(cols)):
        trade_profit = cols[i].number_input ("trade1_profit :",value=TRADES[i][0],min_value=0,max_value=100,key=f"u{i}")
        trade_cutloss = cols[i].number_input("trade1_cutloss :",value=TRADES[i][1],min_value=0,max_value=100,key=f"l{i}")
        trade_amount = cols[i].number_input("trade1_amount :",value=TRADES[i][2],min_value=0,max_value=None,key=f"a{i}")

        if cols[i].button(f"Update", key=f"bot{i}"):
            with st.spinner('Waiting'):
                TRADES[i] = [trade_profit,trade_cutloss,trade_amount]
                payload = {
                    "EMAIL": person_id,
                    f"TRADE{i+1}": str(TRADES[i])
                }
        
                response = requests.post(API_URL, json=payload)

                cols[i].write('update complete!')
else:
    st.write('### Please login!!!')
