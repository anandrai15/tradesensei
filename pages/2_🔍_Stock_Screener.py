import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
from datetime import datetime

# Add the parent directory to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.screener import StockScreener

st.set_page_config(page_title="Stock Screener - TRADESENSEI", page_icon="🥋", layout="wide")

# Add luxury styling
st.markdown("""
<style>
    .stApp {
        background-color: #EAEOD5;
    }
    
    .main-header {
        background: linear-gradient(120deg, #000000 0%, #EAE0D5 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: #EAEOD5;
        text-align: center;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    h1, h2, h3 {
        color: #000000;
        font-weight: bold;
    }
    
    [data-testid="metric-container"] {
        background: linear-gradient(145deg, #C6AC8E, #EAEOD5);
        border: 2px solid #000000;
        padding: 1rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    .stButton > button {
        background: linear-gradient(145deg, #C6AC8E, #EAEOD5);
        color: #000000;
        border: 2px solid #000000;
        border-radius: 10px;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background: linear-gradient(145deg, #000000, #C6AC8E);
        color: #EAEOD5;
    }
</style>
""",
            unsafe_allow_html=True)


def main():
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem;">Screeners</h1>
        <p style="margin: 0.3rem 0 0 0; opacity: 0.9;"> Our Advanced screening tools for Indian markets</p>
    </div>
    """,
                unsafe_allow_html=True)

    # Initialize screener
    if 'screener' not in st.session_state:
        st.session_state.screener = StockScreener()

    screener = st.session_state.screener

    # Screening options
    screening_type = st.radio(
        "Choose Screening Method:",
        ["Pre-built Screens", "Custom Screen", "Combined Screen"],
        horizontal=True)

    if screening_type == "Pre-built Screens":
        st.header("📋 Pre-built Screening Strategies")

        strategy = st.selectbox("Select Strategy:", [
            "RSI Analysis", "Supertrend Signals", "Quarterly Earnings",
            "Momentum Stocks", "Value Stocks", "Growth Stocks",
            "Dividend Stocks", "Quality Stocks"
        ])

        col1, col2 = st.columns([3, 1])

        with col2:
            if st.button("🔍 Run Screen", use_container_width=True):
                with st.spinner(f"Screening for {strategy.lower()}..."):
                    try:
                        if strategy == "RSI Analysis":
                            # Get RSI parameters from sidebar
                            with st.sidebar:
                                st.subheader("RSI Parameters")
                                rsi_condition = st.selectbox(
                                    "RSI Condition",
                                    ["oversold", "overbought", "range"])
                                rsi_low = st.slider("RSI Low", 20, 40, 30)
                                rsi_high = st.slider("RSI High", 60, 80, 70)

                            criteria = {
                                'rsi_condition': rsi_condition,
                                'rsi_low': rsi_low,
                                'rsi_high': rsi_high
                            }
                            results = screener.rsi_screen(criteria)

                        elif strategy == "Supertrend Signals":
                            # Get Supertrend parameters
                            with st.sidebar:
                                st.subheader("Supertrend Parameters")
                                signal_type = st.selectbox(
                                    "Signal Type", ["buy", "sell"])

                            criteria = {'signal_type': signal_type}
                            results = screener.supertrend_screen(criteria)

                        elif strategy == "Quarterly Earnings":
                            # Get earnings parameters
                            with st.sidebar:
                                st.subheader("Earnings Parameters")
                                min_growth = st.slider("Min Profit Growth (%)",
                                                       0, 50, 10)
                                min_revenue_growth = st.slider(
                                    "Min Revenue Growth (%)", 0, 30, 5)
                                max_pe = st.slider("Max P/E Ratio", 10, 50, 25)

                            criteria = {
                                'min_growth': min_growth,
                                'min_revenue_growth': min_revenue_growth,
                                'max_pe': max_pe
                            }
                            results = screener.quarterly_earnings_screen(
                                criteria)

                        elif strategy == "Momentum Stocks":
                            results = screener.momentum_screen()
                        elif strategy == "Value Stocks":
                            results = screener.value_screen()
                        elif strategy == "Growth Stocks":
                            results = screener.growth_screen()
                        elif strategy == "Dividend Stocks":
                            results = screener.dividend_screen()
                        elif strategy == "Quality Stocks":
                            results = screener.quality_screen()

                        st.session_state.screen_results = results
                        st.session_state.screen_type = strategy

                    except Exception as e:
                        st.error(f"Error running screen: {str(e)}")

        # Strategy descriptions
        with col1:
            strategy_descriptions = {
                "RSI Analysis":
                "Find stocks with RSI indicating oversold or overbought conditions for potential reversal trades",
                "Supertrend Signals":
                "Identify stocks showing clear buy/sell signals based on Supertrend indicator",
                "Quarterly Earnings":
                "Screen stocks with strong quarterly earnings growth and reasonable valuations",
                "Momentum Stocks":
                "Stocks showing strong upward price movement with high volume and positive technical indicators",
                "Value Stocks":
                "Undervalued stocks with low P/E ratios, good ROE, and dividend yields",
                "Growth Stocks":
                "Companies showing strong revenue and earnings growth potential",
                "Dividend Stocks":
                "Stocks with consistent dividend payments and good yield",
                "Quality Stocks":
                "Companies with strong fundamentals, low debt, and consistent profitability"
            }

            st.info(strategy_descriptions.get(strategy, ""))

    elif screening_type == "Custom Screen":
        st.header("⚙️ Custom Screening Criteria")

        # Create tabs for different criteria types
        tab1, tab2 = st.tabs(
            ["📊 Fundamental Criteria", "📈 Technical Criteria"])

        with tab1:
            st.subheader("Fundamental Filters")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("**Valuation Metrics**")
                min_market_cap = st.number_input(
                    "Min Market Cap (Cr)", min_value=0, value=100) * 10000000
                max_market_cap = st.number_input("Max Market Cap (Cr)",
                                                 min_value=0,
                                                 value=100000) * 10000000
                min_pe = st.number_input("Min P/E Ratio",
                                         min_value=0.0,
                                         value=5.0,
                                         step=0.1)
                max_pe = st.number_input("Max P/E Ratio",
                                         min_value=0.0,
                                         value=50.0,
                                         step=0.1)

            with col2:
                st.write("**Profitability Metrics**")
                min_roe = st.number_input(
                    "Min ROE (%)", min_value=0.0, value=10.0, step=0.1) / 100
                min_profit_margin = st.number_input("Min Profit Margin (%)",
                                                    min_value=0.0,
                                                    value=5.0,
                                                    step=0.1) / 100
                max_debt_equity = st.number_input("Max Debt/Equity",
                                                  min_value=0.0,
                                                  value=2.0,
                                                  step=0.1)

            with col3:
                st.write("**Growth & Dividend**")
                min_revenue_growth = st.number_input(
                    "Min Revenue Growth (%)", value=-50.0, step=1.0) / 100
                dividend_required = st.checkbox("Must pay dividends")

                # Sector filter
                sectors = st.multiselect("Filter by Sectors:", [
                    "Technology", "Banking", "Pharmaceuticals", "Oil & Gas",
                    "Automobiles", "FMCG"
                ])

            # Build fundamental criteria
            fundamental_criteria = {
                'min_market_cap': min_market_cap,
                'max_market_cap': max_market_cap,
                'min_pe_ratio': min_pe,
                'max_pe_ratio': max_pe,
                'min_roe': min_roe,
                'min_profit_margin': min_profit_margin,
                'max_debt_to_equity': max_debt_equity,
                'min_revenue_growth': min_revenue_growth,
                'dividend_yield': dividend_required,
                'sectors': sectors if sectors else None
            }

        with tab2:
            st.subheader("Technical Filters")

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Price Action**")
                price_above_sma20 = st.checkbox("Price above SMA 20")
                price_above_sma50 = st.checkbox("Price above SMA 50")
                macd_bullish = st.checkbox("MACD Bullish Signal")
                breakout_pattern = st.checkbox("Recent Breakout")

            with col2:
                st.write("**Momentum Indicators**")
                rsi_min = st.number_input("Min RSI",
                                          min_value=0,
                                          max_value=100,
                                          value=30)
                rsi_max = st.number_input("Max RSI",
                                          min_value=0,
                                          max_value=100,
                                          value=70)
                volume_spike = st.checkbox("Volume Spike (1.5x avg)")
                min_volume = st.number_input("Min Daily Volume",
                                             min_value=0,
                                             value=100000)

            # Build technical criteria
            technical_criteria = {
                'price_above_sma20': price_above_sma20,
                'price_above_sma50': price_above_sma50,
                'macd_bullish': macd_bullish,
                'breakout_pattern': breakout_pattern,
                'rsi_min': rsi_min,
                'rsi_max': rsi_max,
                'volume_spike': volume_spike,
                'min_volume': min_volume
            }

        # Run custom screen
        if st.button("🔍 Run Custom Screen", use_container_width=True):
            with st.spinner("Running custom screen..."):
                try:
                    # Combine criteria
                    custom_criteria = {
                        **fundamental_criteria,
                        **technical_criteria
                    }
                    results = screener.custom_screen(custom_criteria)

                    st.session_state.screen_results = results
                    st.session_state.screen_type = "Custom Screen"

                except Exception as e:
                    st.error(f"Error running custom screen: {str(e)}")

    elif screening_type == "Combined Screen":
        st.header("🔄 Combined Fundamental & Technical Screen")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Fundamental Criteria")
            fund_min_roe = st.number_input("Min ROE (%)", value=12.0) / 100
            fund_max_pe = st.number_input("Max P/E Ratio", value=25.0)
            fund_min_growth = st.number_input("Min Revenue Growth (%)",
                                              value=5.0) / 100

            fundamental_criteria = {
                'min_roe': fund_min_roe,
                'max_pe_ratio': fund_max_pe,
                'min_revenue_growth': fund_min_growth
            }

        with col2:
            st.subheader("📈 Technical Criteria")
            tech_price_sma20 = st.checkbox("Price above SMA 20", value=True)
            tech_rsi_range = st.slider("RSI Range", 0, 100, (40, 70))
            tech_macd = st.checkbox("MACD Bullish")

            technical_criteria = {
                'price_above_sma20': tech_price_sma20,
                'rsi_min': tech_rsi_range[0],
                'rsi_max': tech_rsi_range[1],
                'macd_bullish': tech_macd
            }

        # Weighting
        st.subheader("⚖️ Scoring Weights")
        col1, col2 = st.columns(2)

        with col1:
            fund_weight = st.slider("Fundamental Weight", 0.0, 1.0, 0.6, 0.1)
        with col2:
            tech_weight = st.slider("Technical Weight", 0.0, 1.0, 0.4, 0.1)

        # Normalize weights
        total_weight = fund_weight + tech_weight
        if total_weight > 0:
            fund_weight = fund_weight / total_weight
            tech_weight = tech_weight / total_weight

        weights = {'fundamental': fund_weight, 'technical': tech_weight}

        if st.button("🔍 Run Combined Screen", use_container_width=True):
            with st.spinner("Running combined screen..."):
                try:
                    results = screener.combined_screen(fundamental_criteria,
                                                       technical_criteria,
                                                       weights)

                    st.session_state.screen_results = results
                    st.session_state.screen_type = "Combined Screen"

                except Exception as e:
                    st.error(f"Error running combined screen: {str(e)}")

    # Display results
    if hasattr(st.session_state,
               'screen_results') and st.session_state.screen_results:
        st.header(f"📊 {st.session_state.screen_type} Results")

        results = st.session_state.screen_results

        if results:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Stocks Found", len(results))

            with col2:
                if screening_type != "Custom Screen" and 'financial_score' in results[
                        0]:
                    avg_score = sum(
                        r.get('financial_score', 0)
                        for r in results) / len(results)
                    st.metric("Avg Financial Score", f"{avg_score:.1f}")
                elif 'combined_score' in results[0]:
                    avg_score = sum(
                        r.get('combined_score', 0)
                        for r in results) / len(results)
                    st.metric("Avg Combined Score", f"{avg_score:.1f}")
                else:
                    st.metric("Avg Tech Score", "N/A")

            with col3:
                sectors = [
                    r.get('sector', 'Unknown') for r in results
                    if r.get('sector')
                ]
                unique_sectors = len(set(sectors)) if sectors else 0
                st.metric("Sectors Covered", unique_sectors)

            with col4:
                market_caps = [
                    r.get('market_cap', 0) for r in results
                    if r.get('market_cap', 0) > 0
                ]
                avg_mcap = sum(market_caps) / len(
                    market_caps) / 10000000 if market_caps else 0
                st.metric("Avg Market Cap (Cr)", f"₹{avg_mcap:,.0f}")

            # Results table
            df_results = pd.DataFrame(results)

            # Select relevant columns for display
            display_columns = ['symbol', 'current_price']

            if 'company_name' in df_results.columns:
                display_columns.insert(1, 'company_name')
            if 'sector' in df_results.columns:
                display_columns.append('sector')
            if 'financial_score' in df_results.columns:
                display_columns.append('financial_score')
            if 'technical_score' in df_results.columns:
                display_columns.append('technical_score')
            if 'combined_score' in df_results.columns:
                display_columns.append('combined_score')
            if 'pe_ratio' in df_results.columns:
                display_columns.append('pe_ratio')
            if 'roe' in df_results.columns:
                display_columns.append('roe')
            if 'dividend_yield' in df_results.columns:
                display_columns.append('dividend_yield')

            # Filter and rename columns
            display_df = df_results[display_columns].copy()
            display_df.columns = [
                col.replace('_', ' ').title() for col in display_df.columns
            ]

            # Format numeric columns
            numeric_columns = display_df.select_dtypes(
                include=['float64', 'int64']).columns
            for col in numeric_columns:
                if 'Score' in col:
                    display_df[col] = display_df[col].round(1)
                elif 'Price' in col:
                    display_df[col] = display_df[col].round(2)
                elif 'Ratio' in col or 'Roe' in col or 'Yield' in col:
                    display_df[col] = display_df[col].round(3)

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Sector distribution chart
            if 'sector' in df_results.columns:
                sector_counts = df_results['sector'].value_counts()

                if len(sector_counts) > 1:
                    fig_sector = px.pie(
                        values=sector_counts.values,
                        names=sector_counts.index,
                        title="Sector Distribution of Screened Stocks")
                    st.plotly_chart(fig_sector, use_container_width=True)

            # Score distribution (if applicable)
            if 'financial_score' in df_results.columns:
                fig_score = px.histogram(df_results,
                                         x='financial_score',
                                         title="Financial Score Distribution",
                                         nbins=20)
                st.plotly_chart(fig_score, use_container_width=True)
            elif 'combined_score' in df_results.columns:
                fig_score = px.histogram(df_results,
                                         x='combined_score',
                                         title="Combined Score Distribution",
                                         nbins=20)
                st.plotly_chart(fig_score, use_container_width=True)

            # Export option
            if st.button("📥 Export Results to CSV"):
                csv = df_results.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=
                    f"screener_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv")
        else:
            st.warning(
                "No stocks found matching the criteria. Try adjusting your filters."
            )

    # Sector-specific screening
    st.sidebar.header("🏭 Sector Analysis")

    selected_sector = st.sidebar.selectbox("Analyze Sector Leaders:", [
        "Technology", "Banking", "Pharmaceuticals", "Oil & Gas", "Automobiles",
        "FMCG"
    ])

    if st.sidebar.button("Analyze Sector", use_container_width=True):
        with st.spinner(f"Analyzing {selected_sector} sector..."):
            try:
                sector_leaders = screener.get_sector_leaders(selected_sector)

                if sector_leaders:
                    st.session_state.screen_results = sector_leaders
                    st.session_state.screen_type = f"{selected_sector} Leaders"
                    st.rerun()
                else:
                    st.sidebar.error(
                        f"No data available for {selected_sector} sector")

            except Exception as e:
                st.sidebar.error(f"Error analyzing sector: {str(e)}")

    # Screening tips
    with st.sidebar.expander("💡 Screening Tips"):
        st.markdown("""
        **Momentum Screening:**
        - Look for stocks breaking above resistance
        - High volume confirms strong moves
        - RSI between 50-70 shows healthy momentum
        
        **Value Screening:**
        - Low P/E ratios may indicate undervaluation
        - Check debt levels for financial stability
        - Dividend yield adds income component
        
        **Growth Screening:**
        - Revenue growth shows business expansion
        - ROE indicates efficient capital use
        - Consider sector trends and competition
        """)

    # Last update info
    st.sidebar.markdown(
        f"**Last updated:** {datetime.now().strftime('%H:%M:%S')}")

    if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
        # Clear cache and rerun
        if hasattr(st.session_state, 'screener'):
            st.session_state.screener.cache.clear()
        st.rerun()


if __name__ == "__main__":
    main()
