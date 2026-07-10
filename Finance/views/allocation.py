import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import requests
import streamlit as st

from agents.tools import build_desired_allocation_plan
from services.api import get_ai_strategy, get_portfolio_summary, get_strategy


def render_allocation_page():
    if not st.session_state.backend_has_data:
        st.info("Save the portfolio before running allocation strategies.")
        return

    if not st.session_state.summary_has_data:
        try:
            st.session_state.summary_data = get_portfolio_summary(st.session_state.user_id)
            st.session_state.summary_has_data = True
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching summary data: {e}")
            return

    st.subheader("Portfolio Allocation by Asset Class")
    with st.expander("Exact allocations"):
        for item in st.session_state.summary_data:
            st.write(
                f"{item['asset_class']} | Spent: {item['pre_asset_allocation']:.2f}% "
                f"(\\${item['pre_total_cost']:.2f}) | "
                f"Current: {item['cur_asset_allocation']:.2f}% "
                f"(\\${item['cur_total_cost']:.2f})"
            )

    data = st.session_state.summary_data

    asset_classes = [d["asset_class"] for d in data]
    pre_allocations = [d["pre_asset_allocation"] for d in data]
    cur_allocations = [d["cur_asset_allocation"] for d in data]
    pre_costs = [d["pre_total_cost"] for d in data]
    cur_costs = [d["cur_total_cost"] for d in data]

    x = list(range(len(asset_classes)))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    pre_bars = ax.bar([i - width / 2 for i in x], pre_allocations, width, label="Original Allocation (%)")
    cur_bars = ax.bar([i + width / 2 for i in x], cur_allocations, width, label="Current Allocation (%)")

    for bar, cost in zip(pre_bars, pre_costs):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"${cost:.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    for bar, cost in zip(cur_bars, cur_costs):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"${cost:.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    ax.set_ylabel("Allocation (%)")
    ax.set_xlabel("Asset Class")
    ax.set_title("Pre vs Current Allocation by Asset Class")
    ax.set_xticks(x)
    ax.set_xticklabels(asset_classes)
    ax.legend()
    ax.set_axisbelow(True)
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(10))
    ax.yaxis.grid(True, linestyle="--", alpha=0.7, which="major")
    st.pyplot(fig)

    st.header("Allocate percentages")
    list_user_percents = []
    assets = st.columns(len(st.session_state.summary_data))
    for i, asset in enumerate(assets):
        with asset:
            answer = st.text_input(
                st.session_state.summary_data[i]["asset_class"],
                key=f"alloc_{i}",
            ).strip()
            list_user_percents.append(answer)

    if st.button("Submit percents", key="allocation_submit"):
        try:
            allocation_plan = build_desired_allocation_plan(
                st.session_state.summary_data,
                list_user_percents,
                user_id=st.session_state.user_id,
            )
            st.session_state.summary_data = allocation_plan["summary_data"]
            asset_amount_changes = allocation_plan["asset_amount_changes"]
            st.success("Allocations submitted successfully")

            with st.expander("Strategy descriptions"):
                st.write("STRATEGY 1:")
                st.write("Buy: Choose one of the stocks in the asset class and purchase all necessary shares to match desired allocation")
                st.write("Sell: Sort stocks by percent increase in descending order and continually sell shares from the top stock until satisfied")
                st.write("STRATEGY 2:")
                st.write("Buy: Purchase shares such that each stock maintains the same relative ratio within each asset class")
                st.write("Sell: Sell shares such that each stock maintains the same relative ration within each asset class")
                st.write("STRATEGY 3:")
                st.write("Buy: Same strategy as strategy 2")
                st.write("Sell: Similar to strategy 1 except it only sells half of avaliable shares for top stocks until satisfied, if this is not possible then it follows strategy 2")

            for strategy_number in (1, 2, 3):
                strategy_data = get_strategy(strategy_number, asset_amount_changes)
                st.subheader(f"Suggested Strategy {strategy_number}")
                st.dataframe(strategy_data)

            strategy_data = get_ai_strategy(asset_amount_changes)
            st.subheader("Suggested Strategy AI")
            ai_response = strategy_data["response"].replace("$", "\\$")
            st.text(ai_response.replace("\n", "\n"))

        except ValueError:
            st.error("One or more fields contained an invalid value")
        except IndexError:
            st.error("Percents must sum to 100")
        except requests.exceptions.RequestException as e:
            st.error(f"Error: {e}")
        except Exception as e:
            st.error(f"An exception occurred: {e}")
