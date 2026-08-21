import yfinance as yf


def load_tickers(path="all_tickers.txt"):
    with open(path, "r") as f:
        return set(line.strip().upper() for line in f.readlines())


def get_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")["Close"].iloc[-1]
        return float(price) if price is not None else 0.0
    except Exception:
        return 0.0
