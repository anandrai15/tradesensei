import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import yfinance as yf
import numpy as np
import sys
import os

# Add the parent directory to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.market_data import (get_nifty_data, get_top_gainers_losers,
                               get_market_status, get_real_time_price,
                               calculate_technical_indicators,
                               detect_breakouts)
from utils.fundamentals import get_fundamental_data

st.set_page_config(page_title="Market Dashboard - TRADESENSEI", page_icon="🥋", layout="wide")


def create_candlestick_chart(data, title):
    """Create a candlestick chart"""
    fig = go.Figure(data=go.Candlestick(x=data.index,
                                        open=data['Open'],
                                        high=data['High'],
                                        low=data['Low'],
                                        close=data['Close'],
                                        name=title))

    fig.update_layout(title=title,
                      xaxis_title="Date",
                      yaxis_title="Price (₹)",
                      height=400,
                      showlegend=False)

    return fig


def create_volume_chart(data):
    """Create volume chart"""
    fig = go.Figure()

    fig.add_trace(
        go.Bar(x=data.index,
               y=data['Volume'],
               name='Volume',
               marker_color='rgba(255, 107, 107, 0.7)'))

    fig.update_layout(title="Trading Volume",
                      xaxis_title="Date",
                      yaxis_title="Volume",
                      height=200)

    return fig


# Add luxury styling
st.markdown("""
<style>
    /* Luxury color palette: Black, #C6AC8E (warm beige), #EAEOD5 (light cream) */
    .stApp {
        background-color: #EAEOD5;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #000000 0%, #C6AC8E 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: #EAEOD5;
        text-align: center;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    /* Text styling */
    h1, h2, h3 {
        color: #000000;
        font-weight: bold;
    }
    
    /* Metric styling */
    [data-testid="metric-container"] {
        background: linear-gradient(145deg, #C6AC8E, #EAEOD5);
        border: 2px solid #000000;
        padding: 1rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    /* Button styling */
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
    # DRAVYUM header for Market Dashboard
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem;">Market Dashboard</h1>
        <p style="margin: 0.3rem 0 0 0; opacity: 0.9;">Real-time market intelligence and analysis</p>
    </div>
    """,
                unsafe_allow_html=True)

    # Market status indicator
    market_status = get_market_status()

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if market_status.get('is_open', False):
            st.success("🟢 Market OPEN")
        else:
            st.error("🔴 Market CLOSED")

    with col2:
        st.info(f"🕒 {market_status.get('current_time', 'N/A')}")

    with col3:
        st.info(f"📅 Next Session: {market_status.get('next_open', 'N/A')}")

    # Main indices overview
    st.header("📊 Major Indices")

    indices = {
        "NIFTY 50": "^NSEI",
        "SENSEX": "^BSESN",
        "BANK NIFTY": "^NSEBANK",
        "NIFTY IT": "^CNXIT"
    }

    index_cols = st.columns(len(indices))

    for i, (name, symbol) in enumerate(indices.items()):
        with index_cols[i]:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")

                if not hist.empty and len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2]
                    change = current - previous
                    change_pct = (change / previous) * 100

                    st.metric(label=name,
                              value=f"₹{current:,.2f}",
                              delta=f"{change:+.2f} ({change_pct:+.2f}%)")
                else:
                    st.metric(label=name, value="Data unavailable")

            except Exception as e:
                st.metric(label=name, value="Error loading data")

    # AI Market Summary Section
    st.header("🤖 AI Market Summary")

    try:
        from utils.ai_analysis import generate_daily_market_summary

        with st.spinner("Generating AI market analysis..."):
            ai_summary = generate_daily_market_summary()

            if ai_summary:
                # Display summary in an attractive format
                st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 20px; 
                        border-radius: 10px; 
                        color: white;
                        margin: 10px 0;
                    ">
                        <h3 style="color: white; margin: 0 0 15px 0;">📊 Market Intelligence Report</h3>
                        <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 5px;">
                            {ai_summary.replace(chr(10), '<br>')}
                        </div>
                    </div>
                    """,
                            unsafe_allow_html=True)
            else:
                st.info(
                    "AI market summary is currently being generated. Please refresh the page in a moment."
                )

    except Exception as e:
        st.error(f"Error generating AI market summary: {str(e)}")

    # Detailed NIFTY analysis
    st.header("🎯 NIFTY 50 Detailed Analysis")

    try:
        nifty_data = get_nifty_data(period="3mo")

        if not nifty_data.empty:
            # Add technical indicators
            nifty_with_indicators = calculate_technical_indicators(nifty_data)

            col1, col2 = st.columns([2, 1])

            with col1:
                # Candlestick chart
                candlestick_fig = create_candlestick_chart(
                    nifty_data.tail(60), "NIFTY 50 - Last 60 Days")

                # Add moving averages
                if 'SMA_20' in nifty_with_indicators.columns:
                    candlestick_fig.add_trace(
                        go.Scatter(x=nifty_with_indicators.index.tail(60),
                                   y=nifty_with_indicators['SMA_20'].tail(60),
                                   mode='lines',
                                   name='SMA 20',
                                   line=dict(color='orange', width=1)))

                if 'SMA_50' in nifty_with_indicators.columns:
                    candlestick_fig.add_trace(
                        go.Scatter(x=nifty_with_indicators.index.tail(60),
                                   y=nifty_with_indicators['SMA_50'].tail(60),
                                   mode='lines',
                                   name='SMA 50',
                                   line=dict(color='blue', width=1)))

                candlestick_fig.update_layout(showlegend=True)
                st.plotly_chart(candlestick_fig, use_container_width=True)

            with col2:
                # Key technical levels
                current_price = nifty_data['Close'].iloc[-1]
                high_52w = nifty_data['High'].max()
                low_52w = nifty_data['Low'].min()

                st.subheader("📈 Technical Levels")
                st.metric("52W High", f"₹{high_52w:,.2f}")
                st.metric("52W Low", f"₹{low_52w:,.2f}")

                if 'RSI' in nifty_with_indicators.columns:
                    rsi = nifty_with_indicators['RSI'].iloc[-1]
                    st.metric("RSI (14)", f"{rsi:.1f}")

                # Support/Resistance levels
                st.subheader("🎯 Key Levels")
                recent_data = nifty_data.tail(20)
                support = recent_data['Low'].min()
                resistance = recent_data['High'].max()

                st.metric("Support", f"₹{support:,.2f}")
                st.metric("Resistance", f"₹{resistance:,.2f}")

            # Volume analysis
            volume_fig = create_volume_chart(nifty_data.tail(60))
            st.plotly_chart(volume_fig, use_container_width=True)

        else:
            st.error("Unable to fetch NIFTY data")

    except Exception as e:
        st.error(f"Error in NIFTY analysis: {str(e)}")

    # Top movers section
    st.header("🔥 Market Movers")

    try:
        gainers, losers = get_top_gainers_losers()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🟢 Top Gainers")
            if not gainers.empty:
                # Color code the dataframe
                def color_positive(val):
                    return 'color: green' if val > 0 else ''

                styled_gainers = gainers.head(10).style.applymap(
                    color_positive, subset=['Change', '% Change'])
                st.dataframe(styled_gainers, use_container_width=True)
            else:
                st.info("No gainers data available")

        with col2:
            st.subheader("🔴 Top Losers")
            if not losers.empty:

                def color_negative(val):
                    return 'color: red' if val < 0 else ''

                styled_losers = losers.head(10).style.applymap(
                    color_negative, subset=['Change', '% Change'])
                st.dataframe(styled_losers, use_container_width=True)
            else:
                st.info("No losers data available")

    except Exception as e:
        st.error(f"Error loading top movers: {str(e)}")

    # Sectoral performance
    st.header("🏭 Sector Performance")

    try:
        # Sample sector indices (in production, this would fetch real sector data)
        sector_data = {
            'Bank Nifty': '^NSEBANK',
            'IT': '^CNXIT',
            'Auto': '^CNXAUTO',
            'Pharma': '^CNXPHARMA',
            'FMCG': '^CNXFMCG'
        }

        sector_performance = []

        for sector, symbol in sector_data.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")

                if not hist.empty and len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2]
                    change_pct = ((current - previous) / previous) * 100

                    sector_performance.append({
                        'Sector': sector,
                        'Change %': change_pct,
                        'Current': current
                    })
            except:
                continue

        if sector_performance:
            sector_df = pd.DataFrame(sector_performance)
            sector_df = sector_df.sort_values('Change %', ascending=False)

            # Create sector performance chart
            fig = px.bar(sector_df,
                         x='Sector',
                         y='Change %',
                         title="Sectoral Performance Today",
                         color='Change %',
                         color_continuous_scale=['red', 'white', 'green'])
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

            # Show sector table
            st.dataframe(sector_df, use_container_width=True, hide_index=True)
        else:
            st.info("Sector data temporarily unavailable")

    except Exception as e:
        st.error(f"Error loading sector performance: {str(e)}")

    # Breakout stocks
    st.header("🚀 Breakout Analysis")

    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend

        # Get NIFTY stocks breakout data
        breakout_result = detect_breakouts()  # Now works without parameters
        breakout_data = breakout_result.get('breakouts', []) if isinstance(
            breakout_result, dict) else []

        if breakout_data and len(breakout_data) > 0:
            col1, col2 = st.columns([2, 1])

            with col1:
                # Create histogram of breakout ranges using matplotlib
                fig, ax = plt.subplots(figsize=(10, 6))

                # Extract breakout range data
                breakout_ranges = []
                for stock in breakout_data:
                    if 'breakout_range' in stock:
                        breakout_ranges.append(stock['breakout_range'])

                if breakout_ranges:
                    # Create histogram
                    ax.hist(breakout_ranges,
                            bins=20,
                            alpha=0.7,
                            color='#FF6B6B',
                            edgecolor='black')
                    ax.set_xlabel('Breakout Range (Days)', fontsize=12)
                    ax.set_ylabel('Number of Stocks', fontsize=12)
                    ax.set_title(
                        'NIFTY Stocks Breakout Distribution (6-8 Day Range)',
                        fontsize=14,
                        fontweight='bold')
                    ax.grid(True, alpha=0.3)

                    # Add statistics text
                    mean_range = np.mean(breakout_ranges)
                    ax.axvline(mean_range,
                               color='red',
                               linestyle='--',
                               linewidth=2,
                               label=f'Mean: {mean_range:.1f} days')
                    ax.legend()

                    # Style the plot
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()  # Close figure to free memory
                else:
                    st.info("No breakout range data available for histogram")

            with col2:
                st.subheader("📊 Breakout Statistics")

                if breakout_ranges:
                    st.metric("Total Breakouts", len(breakout_ranges))
                    st.metric("Average Range",
                              f"{np.mean(breakout_ranges):.1f} days")
                    st.metric("Max Range", f"{max(breakout_ranges):.1f} days")
                    st.metric("Min Range", f"{min(breakout_ranges):.1f} days")

                # Filter for 6-8 day range breakouts
                filtered_breakouts = [
                    stock for stock in breakout_data
                    if stock.get('breakout_range', 0) >= 6
                    and stock.get('breakout_range', 0) <= 8
                ]

                if filtered_breakouts:
                    st.subheader("🎯 6-8 Day Breakouts")
                    for stock in filtered_breakouts[:5]:  # Show top 5
                        symbol = stock.get('symbol', 'Unknown')
                        breakout_range = stock.get('breakout_range', 0)
                        strength = stock.get('strength', 0)

                        st.write(
                            f"**{symbol}**: {breakout_range:.1f} days (Strength: {strength:.1f})"
                        )

            # Display breakout table
            st.subheader("📈 Recent Breakouts")

            breakout_df = pd.DataFrame([
                {
                    'Symbol': stock.get('symbol', ''),
                    'Current Price': f"₹{stock.get('current_price', 0):.2f}",
                    'Breakout Range (Days)':
                    f"{stock.get('breakout_range', 0):.1f}",
                    'Strength Score': f"{stock.get('strength', 0):.1f}",
                    'Volume Ratio': f"{stock.get('volume_ratio', 1):.1f}x"
                } for stock in breakout_data[:15]  # Top 15 breakouts
            ])

            if not breakout_df.empty:
                st.dataframe(breakout_df,
                             use_container_width=True,
                             hide_index=True)
            else:
                st.info("No breakout data available at the moment")

        else:
            st.info(
                "🔍 No current breakouts detected. Breakout analysis will update during market hours."
            )

            # Show a sample histogram for demonstration
            st.subheader("📊 Sample NIFTY Breakout Distribution")

            # Create sample data for demonstration
            np.random.seed(42)
            sample_ranges = np.random.normal(7, 2, 100)  # Mean 7 days, std 2
            sample_ranges = np.clip(sample_ranges, 3,
                                    15)  # Clip to reasonable range

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist(sample_ranges,
                    bins=15,
                    alpha=0.7,
                    color='#4ECDC4',
                    edgecolor='black')
            ax.set_xlabel('Breakout Range (Days)', fontsize=12)
            ax.set_ylabel('Number of Stocks', fontsize=12)
            ax.set_title('Sample NIFTY Stocks Breakout Distribution',
                         fontsize=14,
                         fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.axvline(np.mean(sample_ranges),
                       color='red',
                       linestyle='--',
                       linewidth=2,
                       label=f'Mean: {np.mean(sample_ranges):.1f} days')
            ax.legend()
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            st.info(
                "This is a sample histogram. Live data will appear when market breakouts are detected."
            )

    except Exception as e:
        st.error(f"Error in breakout analysis: {str(e)}")
        st.info("Breakout analysis temporarily unavailable")

    # Quick stock lookup
    st.header("🔍 Quick Stock Lookup")

    col1, col2 = st.columns([1, 2])

    with col1:
        symbol_input = st.text_input("Enter Stock Symbol (e.g., RELIANCE)",
                                     value="RELIANCE")

        if st.button("Get Quote", use_container_width=True):
            if symbol_input:
                with col2:
                    with st.spinner(f"Fetching data for {symbol_input}..."):
                        try:
                            # Get real-time price
                            current_price = get_real_time_price(symbol_input)

                            if current_price:
                                # Get additional data
                                stock_data = yf.Ticker(
                                    f"{symbol_input}.NS").history(period="5d")

                                if not stock_data.empty:
                                    prev_price = stock_data['Close'].iloc[
                                        -2] if len(
                                            stock_data) > 1 else current_price
                                    change = current_price - prev_price
                                    change_pct = (change / prev_price) * 100

                                    st.metric(
                                        label=symbol_input,
                                        value=f"₹{current_price:.2f}",
                                        delta=
                                        f"{change:+.2f} ({change_pct:+.2f}%)")

                                    # Get fundamental data
                                    fundamental = get_fundamental_data(
                                        symbol_input)
                                    if fundamental:
                                        basic_info = fundamental.get(
                                            'basic_info', {})
                                        valuation = fundamental.get(
                                            'valuation_ratios', {})

                                        info_col1, info_col2 = st.columns(2)

                                        with info_col1:
                                            st.write(
                                                f"**Company:** {basic_info.get('company_name', 'N/A')}"
                                            )
                                            st.write(
                                                f"**Sector:** {basic_info.get('sector', 'N/A')}"
                                            )

                                        with info_col2:
                                            pe_ratio = valuation.get(
                                                'pe_ratio')
                                            if pe_ratio:
                                                st.write(
                                                    f"**P/E Ratio:** {pe_ratio:.2f}"
                                                )
                                            market_cap = basic_info.get(
                                                'market_cap', 0)
                                            if market_cap:
                                                st.write(
                                                    f"**Market Cap:** ₹{market_cap/10000000:.1f} Cr"
                                                )
                                else:
                                    st.error("Unable to fetch historical data")
                            else:
                                st.error(
                                    f"Unable to fetch price for {symbol_input}"
                                )

                        except Exception as e:
                            st.error(f"Error fetching data: {str(e)}")

    # Auto-refresh option
    st.sidebar.header("⚙️ Dashboard Settings")

    auto_refresh = st.sidebar.checkbox("Auto-refresh (30 seconds)")

    if auto_refresh:
        st.sidebar.info(
            "Dashboard will refresh automatically every 30 seconds")
        time.sleep(30)
        st.rerun()

    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

    # Last updated timestamp
    st.sidebar.markdown(
        f"**Last updated:** {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()
