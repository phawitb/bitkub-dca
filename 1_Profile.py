import streamlit as st
import extra_streamlit_components as stx
from hash import hash_password, verify_password, load_users, save_users, isEmail
import datetime
from sent_email import sent_otp
import random
from streamlit_js_eval import streamlit_js_eval
import pytz

# ✅ FIX: Add rerun handler at the top
query_params = st.experimental_get_query_params()
if "rerun" in query_params:
    st.experimental_set_query_params()  # clear it
    st.experimental_rerun()

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

screen_width = streamlit_js_eval(js_expressions='screen.width', key='SCR')

if "screen_width" not in st.session_state:
    st.session_state["screen_width"] = screen_width

try:
    st.set_page_config(layout="wide", initial_sidebar_state=st.session_state.get("sidebar_state", "auto"))
except:
    pass

cookie_manager = stx.CookieManager()
person_id = cookie_manager.get(cookie='person_id')

st.write("# Welcome to Bitkub DCA! 👋")

if not person_id:
    LIST_MENUS = ["📈 Login", "🗃 Register", "Forgot Password"]
    tab1, tab2, tab3 = st.tabs(LIST_MENUS)

    # --- LOGIN ---
    users = load_users("users.json")
    login_username = tab1.text_input("Email :").lower()
    login_password = tab1.text_input("Password :", type="password")

    if not isEmail(login_username):
        tab1.text("not email format")
    elif login_username not in users:
        tab1.text("email not register")

    if tab1.button('LOGIN'):
        if login_username in users and verify_password(users[login_username], login_password):
            tab1.text("Login successful")
            cookie_manager.set(
                'person_id',
                login_username,
                expires_at=datetime.datetime.now().astimezone(pytz.timezone('Asia/Bangkok')).replace(tzinfo=None).replace(year=datetime.datetime.now().year + 2, month=2, day=2)
            )
            st.experimental_set_query_params(rerun="1")  # ✅ FIX
            st.stop()

        else:
            tab1.text("incorrect password")

    # --- REGISTER ---
    if "sentOTP" not in st.session_state:
        st.session_state["sentOTP"] = False
    if "randomotp" not in st.session_state:
        st.session_state["randomotp"] = None
    if "email" not in st.session_state:
        st.session_state["email"] = None
    if "password" not in st.session_state:
        st.session_state["password"] = None

    if not st.session_state["sentOTP"]:
        email = tab2.text_input("Email : ").lower()
        pass1 = tab2.text_input("Password : ", type="password")
        pass2 = tab2.text_input("Re-Password : ", type="password")

        if not isEmail(email):
            tab2.text('not email format')
        elif email in load_users("users.json"):
            tab2.text('email already registered')
        elif pass1 == pass2 and pass1:
            if tab2.button("send otp"):
                tab2.text('sending otp...')
                otp_sent = str(random.randint(1000, 9999))
                st.session_state["randomotp"] = otp_sent
                if sent_otp(email, otp_sent):
                    st.session_state["email"] = email
                    st.session_state["password"] = pass1
                    st.session_state["sentOTP"] = True
                    st.experimental_set_query_params(rerun="1")  # ✅ FIX
                    st.stop()
        else:
            tab2.text('password mismatch')
    else:
        otp = tab2.text_input("OTP :")
        if tab2.button("confirm OTP"):
            if st.session_state["randomotp"] == otp:
                users = load_users("users.json")
                username = st.session_state["email"]
                password = st.session_state["password"]
                hashed_password = hash_password(password)
                users[username] = hashed_password
                save_users("users.json", users)
                tab2.success(f'Done register {username}')
            else:
                tab2.text('OTP mismatch')

    # --- FORGOT PASSWORD ---
    if "stage_fg" not in st.session_state:
        st.session_state["stage_fg"] = 0
    if "email" not in st.session_state:
        st.session_state["email"] = False

    if st.session_state["stage_fg"] == 0:
        email = tab3.text_input("E-mail :").lower()
        if tab3.button('send OTP'):
            if not isEmail(email):
                tab3.text('not email format')
            elif email not in load_users("users.json"):
                tab3.text('email not registered')
            else:
                st.session_state["email"] = email
                otp_sent = str(random.randint(1000, 9999))
                st.session_state["randomotp"] = otp_sent
                if sent_otp(email, otp_sent):
                    st.session_state["stage_fg"] = 1
                    st.experimental_set_query_params(rerun="1")  # ✅ FIX
                    st.stop()
                else:
                    tab3.text('OTP not sent')

    elif st.session_state["stage_fg"] == 1:
        otp = tab3.text_input("OTP :")
        if tab3.button('confirm OTP'):
            if otp == st.session_state["randomotp"]:
                st.session_state["stage_fg"] = 2
                st.experimental_set_query_params(rerun="1")  # ✅ FIX
                st.stop()
            else:
                tab3.text('incorrect OTP')

    elif st.session_state["stage_fg"] == 2:
        new_password = tab3.text_input("New password :", type="password")
        re_new_password = tab3.text_input("Re-New password :", type="password")

        if tab3.button('confirm'):
            if new_password == re_new_password:
                users = load_users("users.json")
                username = st.session_state["email"]
                users[username] = hash_password(new_password)
                save_users("users.json", users)
                tab3.success('Password reset complete!')
            else:
                tab3.text('Passwords must match')

else:
    st.sidebar.success(person_id)
    LIST_MENUS = ["📈 My Profile", "🗃 Change Password", '🪙 Coins']
    tab1, tab2, tab3 = st.tabs(LIST_MENUS)

    # --- MY PROFILE ---
    tab1.write(person_id)
    if tab1.button('Logout'):
        try:
            cookie_manager.delete('person_id')
            st.experimental_set_query_params(rerun="1")  # ✅ FIX
            st.stop()
        except:
            pass

    # --- CHANGE PASSWORD ---
    tab2.text(person_id)
    login_password = tab2.text_input("Old Password :", type="password")
    new_password = tab2.text_input("New Password :", type="password")
    renew_password = tab2.text_input("Re-New Password :", type="password")

    users = load_users("users.json")
    if login_password and verify_password(users.get(person_id, ""), login_password):
        if new_password == renew_password and new_password:
            tab2.text("Match!")
            if tab2.button('CONFIRM'):
                users[person_id] = hash_password(new_password)
                save_users("users.json", users)
                tab2.success("Password updated successfully!")
        else:
            tab2.text("New passwords must match")
    elif login_password:
        tab2.text("Old password incorrect")
