import pandas as pd
import requests
import streamlit as st

from services.api import extract_portfolio
from services.prices import get_price
from services.state import initialize_state, portfolio_exists, reset_portfolio_state
from views.advice import render_advice_page
from views.allocation import render_allocation_page
from views.portfolio import render_portfolio_page


initialize_state()

if st.session_state.user_id != 0 and not st.session_state.has_data and not st.session_state.logged_in:
    try:
        added = pd.DataFrame(extract_portfolio(st.session_state.user_id))

        if not added.empty:
            added["current"] = added["symbol"].apply(get_price)
            st.session_state.df = pd.concat([st.session_state.df, added], ignore_index=True)
            st.session_state.has_data = True
            st.session_state.backend_has_data = True

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching summary data: {e}")


with st.sidebar:
    user_input = st.text_input("Enter user id", key="sidebar_input")
    if st.button("Submit", key="sidebar_submit"):
        st.session_state.user_id = user_input
        reset_portfolio_state()
        st.rerun()

    pages = ["Portfolio"]
    if portfolio_exists():
        pages.append("Rebalancing calculator")
        pages.append("Portfolio advice")

    selected_page = st.radio("Navigation", pages, key="selected_page")


if selected_page == "Portfolio":
    render_portfolio_page()
elif selected_page == "Rebalancing calculator":
    render_allocation_page()
elif selected_page == "Portfolio advice":
    render_advice_page()
