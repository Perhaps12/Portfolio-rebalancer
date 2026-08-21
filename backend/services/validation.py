import streamlit as st


def valid(category, value):
    if category == "t":
        if not value or value.upper() not in st.session_state.tickers:
            return False
    elif category == "q":
        try:
            float(value)
        except (ValueError, TypeError):
            return False
    elif category == "p":
        try:
            float(value)
        except (ValueError, TypeError):
            return False
    elif category == "s":
        pass
    elif category == "a":
        pass

    return True


def valid_percent(p):
    try:
        p = float(p)
        return 0 <= p <= 100
    except (ValueError, TypeError):
        return False
