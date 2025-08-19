import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import yfinance as yf


# Initialize session state for data if it doesn't exist yet
if "data" not in st.session_state:
    st.session_state.data = []
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()
if "tickers" not in st.session_state:
    with open("all_tickers.txt", "r") as f:
        st.session_state.tickers = set(line.strip().upper() for line in f.readlines())
        # Initialize session state for the flag
if "has_data" not in st.session_state:
    st.session_state.has_data = False
if 'summary_data' not in st.session_state:
    st.session_state.summary_data = [{}]
if 'backend_has_data' not in st.session_state:
    st.session_state.backend_has_data = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = 0


# st.write(st.session_state.tickers)

def valid(category, value):
    if category == 't': #ticker
        # st.write(value.upper())
        if not value or value.upper() not in st.session_state.tickers:
            return False
    elif category == 'q': #quantity
        # Check if value can be converted to int
        try:
            float(value)
        except (ValueError, TypeError):
            return False

    elif category == 'p': #price
        # Check if value can be converted to float
        try:
            float(value)
        except (ValueError, TypeError):
            return False
        
    elif category == 's': #sector temp
        pass
    elif category == 'a': #asset temp
        pass

    return True

def valid_percent(p):
    try:
        p = float(p)
        return p >= 0 and p <= 100
    except (ValueError, TypeError):
        return False    

def get_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")["Close"].iloc[-1]
        return float(price) if price is not None else 0.0
    except Exception:
        return 0.0  # fallback if price lookup fails

#user data
st.subheader("Input Stock Data:")
symbol, quantity, price, sector, asset = st.columns(5)

with symbol:
    box1 = st.text_input("Ticker Symbol").strip() #dropdown + typing ability (?)
with quantity:
    box2 = st.text_input("Stocks Purchased").strip()
with price:
    box3 = st.text_input("Stock Price").strip()
with sector:
    box4 = st.text_input("Sector").strip() #make dropdown at somepoint
with asset:
    box5 = st.text_input("Asset Class").strip() #make dropdown at somepoint
    

if st.button("Submit"):
    try:
        if valid('t', box1) and valid('q', box2) and valid('p', box3) and valid('s', box4) and valid('a', box5):
            pass
        else:
            raise ValueError
        box2 = float(box2)
        box3 = float(box3)
        
        # Create new row as dictionary
        new_row = {
            'symbol': box1.upper(),
            'quantity': box2,
            'avg_cost': box3,
            'sector': box4,
            'asset_class': box5,
            'current': get_price(box1.upper())
        }

        # Append to list in session state
        st.session_state.data.append(new_row)

        # Append to DataFrame in session state
        st.session_state.df = pd.concat(
            [st.session_state.df, pd.DataFrame([new_row])],
            ignore_index=True
        )

        # Set flag to True immediately
        st.session_state.has_data = True

    except ValueError:
        st.write("One or more fields contained an invalid value")

#upload file
st.subheader("Upload Stock Data")
uploaded_file = st.file_uploader("Upload a CSV file", type="csv")
added = None

if uploaded_file is not None:
    # Read the uploaded file into a DataFrame
    added = pd.read_csv(uploaded_file)
    st.write("Preview of uploaded file:")
    st.dataframe(added)

if st.button("Upload File"):
    if uploaded_file is None:
        st.write("Please upload a file first")
    else:
        added["current"] = added["symbol"].apply(get_price)
        st.session_state.df = pd.concat([st.session_state.df, added], ignore_index=True)
        st.session_state.has_data = True  # immediately mark data as present

# st.write(st.session_state.data)

# --- Show table & graphs ---
if st.session_state.has_data:

    st.title("Current Portfolio")
    #get current price
    st.dataframe(st.session_state.df)

    # Show Final Submit button immediately
    if st.button("Final Submit"):
        requests.delete("http://127.0.0.1:8000/portfolio/")
        url = "http://127.0.0.1:8000/portfolio/"
        for _, row in st.session_state.df.iterrows():
            data_to_send = row.to_dict()
            data_to_send["user_id"] = st.session_state.user_id  # add your integer here
            response = requests.post(url, json=data_to_send)
            if response.status_code not in (200, 201):
                st.error(f"Failed to submit {row['symbol']}")
        st.success("Portfolio submitted to backend")
        st.session_state.backend_has_data = True

    # Show graph
    
    # df_graph = st.session_state.df.copy()
    # df_graph['total'] = df_graph['quantity'] * df_graph['avg_cost']
    # df_graph_plot = df_graph.set_index('symbol')

    # fig, ax = plt.subplots()
    # df_graph_plot['total'].plot(kind='bar', ax=ax, color='skyblue')
    # ax.set_ylabel("Total Spent ($)")
    # ax.set_xlabel("Stock")
    # ax.set_title("Portfolio")
    # st.pyplot(fig)

    if 'summary_has_data' not in st.session_state:
            st.session_state.summary_has_data = False
    
    # Button to fetch summary JSON
    if st.session_state.backend_has_data:

        if st.button("Show Asset Allocation Summary"):
            try:
                API_URL_SUMMARY = "http://localhost:8000/portfolio/summary/"
                response = requests.get(API_URL_SUMMARY)
                response.raise_for_status()
                st.session_state.summary_data = response.json()
                st.session_state.summary_has_data = True


            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching summary data: {e}")

            # Render summary + inputs if data exists

    if st.session_state.summary_has_data:
        
        st.subheader("Portfolio Allocation by Asset Class")
        for item in st.session_state.summary_data:
            st.write(f"{item['asset_class']} | Spent: {item['pre_asset_allocation']:.2f}% "
                    f"(\\${item['pre_total_cost']:.2f}) | "
                    f"Current: {item['cur_asset_allocation']:.2f}% "
                    f"(\\${item['cur_total_cost']:.2f})")

        st.header('Allocate percentages')
        list_user_percents = []
        assets = st.columns(len(st.session_state.summary_data))
        for i, asset in enumerate(assets):
            with asset:
                answer = st.text_input(
                    st.session_state.summary_data[i]['asset_class'],
                    key=f"alloc_{i}"  # 🔑 unique key to persist value
                ).strip()
                list_user_percents.append(answer)

        if st.button("Submit percents"):
            try:
                for i in list_user_percents:
                    if not valid_percent(i):
                        raise ValueError
                if sum(int(x) for x in list_user_percents) != 100:
                    raise IndexError
                
                asset_amount_changes = {}
                for i in range(len(st.session_state.summary_data)):
                    st.session_state.summary_data[i]['desired_allocation'] = float(list_user_percents[i])
                
                for i in st.session_state.summary_data:
                    asset_amount_changes[i['asset_class']] = i['cur_total_cost'] * (i['desired_allocation'] / i['cur_asset_allocation']-1)
            
                try:
                    response = requests.post(
                        "http://127.0.0.1:8000/portfolio/strat1/",
                        json=asset_amount_changes
                    )
                    response.raise_for_status()
                    strategy_data = response.json()   # <--- backend’s return
                    st.success("Allocations submitted successfully")

                    st.subheader("Suggested Strategy 1")
                    st.dataframe(strategy_data)       # show as table

                    response = requests.post(
                        "http://127.0.0.1:8000/portfolio/strat2/",
                        json=asset_amount_changes
                    )
                    response.raise_for_status()
                    strategy_data = response.json()   # <--- backend’s return

                    st.subheader("Suggested Strategy 2")
                    st.dataframe(strategy_data)       # show as table

                    response = requests.post(
                        "http://127.0.0.1:8000/portfolio/strat3/",
                        json=asset_amount_changes
                    )
                    response.raise_for_status()
                    strategy_data = response.json()   # <--- backend’s return

                    st.subheader("Suggested Strategy 3")
                    st.dataframe(strategy_data)       # show as table

                except requests.exceptions.RequestException as e:
                    st.error(f"Error: {e}")
            except ValueError:
                st.error("One or more fields contained an invalid value")
            except IndexError:
                st.error("Percents must sum to 100")
            except Exception as e:
                print(f"An exception occurred: {e}")
        
