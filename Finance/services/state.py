import pandas as pd
import streamlit as st

from services.prices import load_tickers


def initialize_state():
    defaults = {
        "user_id": 0,
        "logged_in": False,
        "data": [],
        "df": pd.DataFrame(),
        "has_data": False,
        "summary_data": [{}],
        "backend_has_data": False,
        "summary_has_data": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "tickers" not in st.session_state:
        st.session_state.tickers = load_tickers()


def reset_portfolio_state():
    st.session_state.user_id = st.session_state.get("user_id", 0)
    st.session_state.logged_in = False
    st.session_state.pop("data", None)
    st.session_state.pop("df", None)
    st.session_state.pop("has_data", None)
    st.session_state.pop("summary_data", None)
    st.session_state.pop("backend_has_data", None)
    st.session_state.pop("summary_has_data", None)
    initialize_state()


def portfolio_exists():
    return st.session_state.has_data and not st.session_state.df.empty
