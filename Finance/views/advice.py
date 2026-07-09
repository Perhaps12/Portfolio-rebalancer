import streamlit as st


def render_advice_page():
    st.title("Portfolio Advice")

    st.caption("Prototype: supervisor agent + risk specialist agent.")

    model = st.text_input("Model", value="ollama:llama3.1", key="advice_model")
    user_query = st.text_area("Ask a portfolio question", key="advice_query")

    if st.button("Ask", key="advice_ask"):
        if not user_query.strip():
            st.error("Enter a question first.")
            return

        if not st.session_state.has_data or st.session_state.df.empty:
            st.error("Create or load a portfolio before asking for portfolio advice.")
            return

        try:
            from agents.supervisor import SupervisorAgent

            with st.spinner("The supervisor is consulting the risk specialist..."):
                supervisor = SupervisorAgent(model=model)
                result = supervisor.run(user_query, st.session_state.df)

            st.subheader("Answer")
            st.write(result["final_answer"])

            with st.expander("Specialist output"):
                for specialist_result in result["specialist_results"]:
                    st.markdown(f"**{specialist_result['agent']}**")
                    st.write(specialist_result["answer"])
                    st.json(specialist_result["portfolio_summary"])

        except ModuleNotFoundError:
            st.error("The aisuite package is not installed yet. Install it before using Portfolio Advice.")
        except Exception as e:
            st.error(f"Portfolio advice failed: {e}")
