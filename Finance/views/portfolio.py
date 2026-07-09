import pandas as pd
import requests
import streamlit as st

from services.api import clear_portfolio, save_portfolio_item
from services.prices import get_price
from services.validation import valid


def render_portfolio_page():
    st.subheader("Input Stock Data:")
    symbol, quantity, price, sector, asset = st.columns(5)

    with symbol:
        box1 = st.text_input("Ticker Symbol", key="portfolio_symbol").strip()
    with quantity:
        box2 = st.text_input("Stocks Purchased", key="portfolio_quantity").strip()
    with price:
        box3 = st.text_input("Stock Price", key="portfolio_price").strip()
    with sector:
        box4 = st.text_input("Sector", key="portfolio_sector").strip()
    with asset:
        box5 = st.text_input("Asset Class", key="portfolio_asset").strip()

    if st.button("Submit", key="portfolio_submit"):
        try:
            if not (
                valid("t", box1)
                and valid("q", box2)
                and valid("p", box3)
                and valid("s", box4)
                and valid("a", box5)
            ):
                raise ValueError

            new_row = {
                "symbol": box1.upper(),
                "quantity": float(box2),
                "avg_cost": float(box3),
                "sector": box4,
                "asset_class": box5,
                "current": get_price(box1.upper()),
            }

            st.session_state.data.append(new_row)
            st.session_state.df = pd.concat(
                [st.session_state.df, pd.DataFrame([new_row])],
                ignore_index=True,
            )
            st.session_state.has_data = True
            st.session_state.backend_has_data = False

        except ValueError:
            st.write("One or more fields contained an invalid value")

    st.subheader("Upload Stock Data")
    uploaded_file = st.file_uploader("Upload a CSV file", type="csv", key="portfolio_upload")
    added = None

    if uploaded_file is not None:
        added = pd.read_csv(uploaded_file)
        st.write("Preview of uploaded file:")
        st.dataframe(added)

    if st.button("Upload File", key="portfolio_upload_submit"):
        if uploaded_file is None:
            st.write("Please upload a file first")
        else:
            added["current"] = added["symbol"].apply(get_price)
            st.session_state.df = pd.concat([st.session_state.df, added], ignore_index=True)
            st.session_state.has_data = True
            st.session_state.backend_has_data = False

    if st.session_state.has_data:
        st.title("Current Portfolio")

        if st.button("Clear Table", key="portfolio_clear"):
            st.session_state.df = pd.DataFrame()
            st.session_state.has_data = False
            st.session_state.summary_data = [{}]
            st.session_state.summary_has_data = False
            st.session_state.backend_has_data = False
            st.session_state.logged_in = True
            st.rerun()

        st.dataframe(st.session_state.df)

        if st.button("Save Portfolio", key="portfolio_save"):
            try:
                clear_portfolio(st.session_state.user_id)
                for _, row in st.session_state.df.iterrows():
                    data_to_send = row.to_dict()
                    data_to_send["user_id"] = st.session_state.user_id
                    save_portfolio_item(data_to_send)

                st.success("Portfolio submitted to backend")
                st.session_state.backend_has_data = True
                st.session_state.summary_has_data = False

            except requests.exceptions.RequestException as e:
                st.error(f"Error saving portfolio: {e}")
