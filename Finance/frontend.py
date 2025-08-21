import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import yfinance as yf
import matplotlib.ticker as mticker

if 'user_id' not in st.session_state:
    st.session_state.user_id = 0

with st.sidebar:
    user_input = st.text_input("Enter user id", key="sidebar_input")
    if st.button("Submit", key="sidebar_submit"):
        st.session_state.user_id = user_input
        st.session_state.pop("data", None)
        st.session_state.pop("df", None)
        st.session_state.pop("has_data", None)
        st.session_state.pop("summary_data", None)
        st.session_state.pop("backend_has_data", None)

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

if st.session_state.user_id != 0 and st.session_state.has_data == False:
    try:
        API_URL_SUMMARY = f"http://localhost:8000/portfolio/extract/?user_id={st.session_state.user_id}"
        response = requests.get(API_URL_SUMMARY)
        response.raise_for_status()
        added = pd.DataFrame(response.json())   # convert list of dicts -> DataFrame

        # Add a "current" column by applying your function
        if not added.empty:
            added["current"] = added["symbol"].apply(get_price)
            st.session_state.df = pd.concat([st.session_state.df, added], ignore_index=True)
            st.session_state.has_data = True
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching summary data: {e}")

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
        requests.delete(f"http://127.0.0.1:8000/portfolio/?user_id={st.session_state.user_id}")
        url = "http://127.0.0.1:8000/portfolio/"
        for _, row in st.session_state.df.iterrows():
            data_to_send = row.to_dict()
            data_to_send["user_id"] = st.session_state.user_id  # add your integer here
            response = requests.post(url, json=data_to_send)
            if response.status_code not in (200, 201):
                st.error(f"Failed to submit {row['symbol']}")
        st.success("Portfolio submitted to backend")
        st.session_state.backend_has_data = True

    if 'summary_has_data' not in st.session_state:
            st.session_state.summary_has_data = False
    
    # Button to fetch summary JSON
    if st.session_state.backend_has_data:

        if st.button("Show Asset Allocation Summary"):
            try:
                API_URL_SUMMARY = f"http://localhost:8000/portfolio/summary/?user_id={st.session_state.user_id}"
                response = requests.get(API_URL_SUMMARY)
                response.raise_for_status()
                st.session_state.summary_data = response.json()
                st.session_state.summary_has_data = True


            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching summary data: {e}")

            # Render summary + inputs if data exists

    if st.session_state.summary_has_data:
        
        st.subheader("Portfolio Allocation by Asset Class")
        with st.expander("Exact allocations"):
            for item in st.session_state.summary_data:
                st.write(f"{item['asset_class']} | Spent: {item['pre_asset_allocation']:.2f}% "
                        f"(\\${item['pre_total_cost']:.2f}) | "
                        f"Current: {item['cur_asset_allocation']:.2f}% "
                        f"(\\${item['cur_total_cost']:.2f})")
            
        #graph
        data = st.session_state.summary_data

        asset_classes = [d["asset_class"] for d in data]
        pre_allocations = [d["pre_asset_allocation"] for d in data]
        cur_allocations = [d["cur_asset_allocation"] for d in data]
        pre_costs = [d["pre_total_cost"] for d in data]
        cur_costs = [d["cur_total_cost"] for d in data]

        x = list(range(len(asset_classes)))  # just use range instead of numpy
        width = 0.35

        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot bars
        pre_bars = ax.bar([i - width/2 for i in x], pre_allocations, width, label="Original Allocation (%)")
        cur_bars = ax.bar([i + width/2 for i in x], cur_allocations, width, label="Current Allocation (%)")

        # Add total cost labels above bars
        for bar, cost in zip(pre_bars, pre_costs):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f"${cost:.2f}", ha="center", va="bottom", fontsize=8)

        for bar, cost in zip(cur_bars, cur_costs):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f"${cost:.2f}", ha="center", va="bottom", fontsize=8)

        # Formatting
        ax.set_ylabel("Allocation (%)")
        ax.set_xlabel("Asset Class")
        ax.set_title("Pre vs Current Allocation by Asset Class")
        ax.set_xticks(x)
        ax.set_xticklabels(asset_classes)
        ax.legend()
        ax.set_axisbelow(True)
        ax.set_ylim(0, 100)
        # Force ticks every 10%
        ax.yaxis.set_major_locator(mticker.MultipleLocator(10))
        # Gridlines every 10% (aligned with ticks)
        ax.yaxis.grid(True, linestyle="--", alpha=0.7, which="major")
        st.pyplot(fig)

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
                
                asset_amount_changes['user_id'] = st.session_state.user_id
            
                try:
                    st.success("Allocations submitted successfully")
                    with st.expander("Strategy descriptions"):
                        st.write("STRATEGY 1:" )
                        st.write("Buy: Choose one of the stocks in the asset class and purchase all necessary shares to match desired allocation" )
                        st.write("Sell: Sort stocks by percent increase in descending order and continually sell shares from the top stock until satisfied" )
                        st.write("STRATEGY 2:" )
                        st.write("Buy: Purchase shares such that each stock maintains the same relative ratio within each asset class" )
                        st.write("Sell: Sell shares such that each stock maintains the same relative ration within each asset class" )
                        st.write("STRATEGY 3:" )
                        st.write("Buy: Same strategy as strategy 2" )
                        st.write("Sell: Similar to strategy 1 except it only sells half of avaliable shares for top stocks until satisfied, if this is not possible then it follows strategy 2")
                    response = requests.post(
                        "http://127.0.0.1:8000/portfolio/strat1/",
                        json=asset_amount_changes
                    )#strategy 1
                    response.raise_for_status()
                    strategy_data = response.json()   # <--- backend’s return

                    st.subheader("Suggested Strategy 1")
                    st.dataframe(strategy_data)       # show as table
                    #strategy 2
                    response = requests.post(
                        "http://127.0.0.1:8000/portfolio/strat2/",
                        json=asset_amount_changes
                    )
                    response.raise_for_status()
                    strategy_data = response.json()   # <--- backend’s return

                    st.subheader("Suggested Strategy 2")
                    st.dataframe(strategy_data)       # show as table
                    #strategy 3
                    response = requests.post(
                        "http://127.0.0.1:8000/portfolio/strat3/",
                        json=asset_amount_changes
                    )
                    response.raise_for_status()
                    strategy_data = response.json()   # <--- backend’s return
                    #strategy AI
                    st.subheader("Suggested Strategy 3")
                    st.dataframe(strategy_data)       # show as table

                    response = requests.post(
                        "http://127.0.0.1:8000/portfolio/stratAI/",
                        json=asset_amount_changes
                    )
                    response.raise_for_status()
                    strategy_data = response.json()   # <--- backend’s return

                    st.subheader("Suggested Strategy AI")
                    AI_rambling = strategy_data['response'].replace("$", "\\$")
                    st.write(AI_rambling) 

                except requests.exceptions.RequestException as e:
                    st.error(f"Error: {e}")
            except ValueError:
                st.error("One or more fields contained an invalid value")
            except IndexError:
                st.error("Percents must sum to 100")
            except Exception as e:
                print(f"An exception occurred: {e}")
        
