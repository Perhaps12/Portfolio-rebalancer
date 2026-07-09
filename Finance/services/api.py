import requests


BASE_URL = "http://127.0.0.1:8000"


def extract_portfolio(user_id):
    response = requests.get(f"{BASE_URL}/portfolio/extract/?user_id={user_id}")
    response.raise_for_status()
    return response.json()


def clear_portfolio(user_id):
    response = requests.delete(f"{BASE_URL}/portfolio/?user_id={user_id}")
    response.raise_for_status()
    return response


def save_portfolio_item(item):
    response = requests.post(f"{BASE_URL}/portfolio/", json=item)
    response.raise_for_status()
    return response


def get_portfolio_summary(user_id):
    response = requests.get(f"{BASE_URL}/portfolio/summary/?user_id={user_id}")
    response.raise_for_status()
    return response.json()


def get_strategy(strategy_number, changes):
    response = requests.post(f"{BASE_URL}/portfolio/strat{strategy_number}/", json=changes)
    response.raise_for_status()
    return response.json()


def get_ai_strategy(changes):
    response = requests.post(f"{BASE_URL}/portfolio/stratAI/", json=changes)
    response.raise_for_status()
    return response.json()
