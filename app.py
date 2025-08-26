import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import yfinance as yf
from utils.market_data import get_nifty_data, get_top_gainers_losers
from utils.fundamentals import get_fundamental_data
from utils.ai_analysis import get_market_sentiment_analysis
from utils.news_scraper import get_financial_news
import threading
import time

# ──────────────────────────────────────────────────────────────
# 🔧 ADVANCED TECHNICAL INDICATORS
# ──────────────────────────────────────────────────────────────

def supertrend(df, period=10, multiplier=3):
    """Calculate Supertrend indicator"""
    hl2 = (df['High'] + df['Low']) / 2
    atr = df['High'].rolling(window=period).max() - df['Low'].rolling(window=period).min()
    atr = atr.rolling(window=period).mean()

    upper_band = hl2 + multiplier * atr
    lower_band = hl2 - multiplier * atr

    supertrend_values = []
    trend_direction = []
    in_uptrend = True

    for i in range(len(df)):
        if i == 0:
            supertrend_values.append(hl2.iloc[i])
            trend_direction.append(1)
            continue

        if df['Close'].iloc[i] > upper_band.iloc[i-1]:
            in_uptrend = True
        elif df['Close'].iloc[i] < lower_band.iloc[i-1]:
            in_uptrend = False

        if in_uptrend:
            supertrend_values.append(lower_band.iloc[i])
            trend_direction.append(1)
        else:
            supertrend_values.append(upper_band.iloc[i])
            trend_direction.append(-1)

    return pd.Series(supertrend_values, index=df.index), pd.Series(trend_direction, index=df.index)

def bollinger_bands(close, window=20, num_std=2):
    """Calculate Bollinger Bands"""
    sma = close.rolling(window=window).mean()
    std = close.rolling(window=window).std()
    upper_band = sma + (num_std * std)
    lower_band = sma - (num_std * std)
    return sma, upper_band, lower_band

def rsi(close, window=14):
    """Calculate RSI"""
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def fisher_transform(high, low, period=9):
    """Calculate Fisher Transform"""
    hl2 = (high + low) / 2

    # Normalize the values
    highest = hl2.rolling(window=period).max()
    lowest = hl2.rolling(window=period).min()

    normalized = 2 * ((hl2 - lowest) / (highest - lowest)) - 1
    normalized = normalized.fillna(0).clip(-0.999, 0.999)

    fisher = pd.Series(index=high.index, dtype=float)
    fisher_signal = pd.Series(index=high.index, dtype=float)

    for i in range(len(normalized)):
        if i == 0:
            fisher.iloc[i] = 0
            fisher_signal.iloc[i] = 0
        else:
            fisher_value = 0.5 * np.log((1 + normalized.iloc[i]) / (1 - normalized.iloc[i]))
            fisher.iloc[i] = 0.33 * fisher_value + 0.67 * fisher.iloc[i-1]
            fisher_signal.iloc[i] = fisher.iloc[i-1]

    return fisher, fisher_signal

def macd(close, fast=12, slow=26, signal=9):
    """Calculate MACD"""
    exp1 = close.ewm(span=fast).mean()
    exp2 = close.ewm(span=slow).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def stochastic(high, low, close, k_period=14, d_period=3):
    """Calculate Stochastic Oscillator"""
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()

    k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d_percent = k_percent.rolling(window=d_period).mean()

    return k_percent, d_percent

def volume_profile(close, volume, bins=20):
    """Calculate Volume Profile"""
    price_min = close.min()
    price_max = close.max()

    # Create price levels
    price_levels = np.linspace(price_min, price_max, bins)
    volume_at_price = []

    for i in range(len(price_levels) - 1):
        level_low = price_levels[i]
        level_high = price_levels[i + 1]

        mask = (close >= level_low) & (close < level_high)
        level_volume = volume[mask].sum()

        volume_at_price.append({
            'price': (level_low + level_high) / 2,
            'volume': level_volume
        })

    return pd.DataFrame(volume_at_price)

# Configure page
st.set_page_config(page_title="Dravyum",
                   page_icon="⚡",
                   layout="wide",
                   initial_sidebar_state="expanded")

# Custom CSS for DRAVYUM - Sleek Black & White Theme

# -- Theme selector & centralized theme variables --
if 'theme' not in st.session_state:
    st.session_state['theme'] = 'Light'

theme_choice = st.sidebar.radio("Theme", ("Light", "Dark"), index=0, key="theme")

# CSS templates for Light and Dark themes. Heading/subheading color set to #EB4511
_light_vars = {
    "bg": "#f5f7fa",
    "text": "#1a1a1a",
    "muted": "#6b7280",
    "card": "#ffffff",
    "accent": "#0b5fff",
    "heading": "#EB4511"
}
_dark_vars = {
    "bg": "#0f1724",
    "text": "#e6eef8",
    "muted": "#9aa6b2",
    "card": "#0b1220",
    "accent": "#2b8cff",
    "heading": "#EB4511"
}

_vars = _light_vars if theme_choice == "Light" else _dark_vars

_theme_css = f"""
<style>
:root {{
    --bg: {_vars['bg']};
    --text: {_vars['text']};
    --muted: {_vars['muted']};
    --card: {_vars['card']};
    --accent: {_vars['accent']};
    --heading-color: {_vars['heading']};
}}

/* Apply base variables */
html, body, .stApp {{
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Helvetica Neue', Arial, sans-serif;
}}

/* Headings and brand */
h1, h2, h3, .main-header, .stHeader, .stSubheader, .css-1d391kg, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
    color: var(--heading-color) !important;
}}

/* Links and accents */
a, .link, .stButton button {{
    color: var(--accent) !important;
}}

/* Cards and panels */
.section, .card, .stCard, .stSidebar, .sidebar {{
    background-color: var(--card) !important;
    color: var(--text) !important;
}}

</style>
"""
st.markdown(_theme_css, unsafe_allow_html=True)
# -- End theme injection --
,
            unsafe_allow_html=True)

def main():
    # Luxury header with brand name
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 3rem; font-weight: bold; color: #FFFFFF;"> Dravyum</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9; color: #FFFFFF;">Master AI Trading Intelligence for Indian Markets</p>
        <p style="margin: 0.3rem 0 0 0; font-size: 1rem; opacity: 0.7;">NSE • BSE • Advanced Analytics • Free & Open Source</p>
    </div>
    """,
                unsafe_allow_html=True)

    # Sidebar for quick market overview
    with st.sidebar:
        st.header("Quick Market Overview")
        try:
            # Get NIFTY 50 data
            nifty_data = get_nifty_data()
            if not nifty_data.empty:
                current_price = nifty_data['Close'].iloc[-1]
                prev_price = nifty_data['Close'].iloc[-2]
                change = current_price - prev_price
                change_pct = (change / prev_price) * 100

                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="NIFTY 50",
                              value=f"₹{current_price:,.2f}",
                              delta=f"{change:+.2f} ({change_pct:+.2f}%)")

                # Mini chart
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(x=nifty_data.index[-30:],
                               y=nifty_data['Close'].iloc[-30:],
                               mode='lines',
                               line=dict(color='#FF6B6B', width=2),
                               name='NIFTY 50'))

                fig.update_layout(height=200,
                                  margin=dict(l=0, r=0, t=0, b=0),
                                  showlegend=False,
                                  xaxis=dict(showgrid=False,
                                             showticklabels=False),
                                  yaxis=dict(showgrid=False,
                                             showticklabels=False),
                                  plot_bgcolor='rgba(0,0,0,0)',
                                  paper_bgcolor='rgba(0,0,0,0)')

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Unable to fetch NIFTY data")
        except Exception as e:
            st.error(f"Error loading market data: {str(e)}")

        # Latest Financial News Section
        st.markdown("---")
        st.header("Latest Market News")

        # Load news
        if 'latest_news' not in st.session_state:
            with st.spinner("Loading news..."):
                st.session_state.latest_news = get_financial_news()

        news_articles = st.session_state.latest_news[:5]  # Show top 5 in sidebar

        for article in news_articles:
            st.markdown(f"""
            <div style='padding: 0.5rem; margin: 0.3rem 0; background: linear-gradient(145deg, #C6AC8E, #EAEOD5); 
                 border-radius: 8px; border-left: 3px solid #000000;'>
                <p style='margin: 0; font-size: 0.8rem; font-weight: bold; color: #000000;'>{article['title'][:60]}...</p>
                <p style='margin: 0; font-size: 0.7rem; opacity: 0.7; color: #000000;'>{article['source']} • {article['timestamp']}</p>
            </div>
            """,
                        unsafe_allow_html=True)

        # Quick actions
        st.markdown("---")
        st.header("Quick Actions")

        col_news, col_data = st.columns(2)
        with col_news:
            if st.button("📰 Refresh News", use_container_width=True):
                with st.spinner("Loading news..."):
                    st.session_state.latest_news = get_financial_news()
                    st.rerun()

        with col_data:
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()

        if st.button("📧 Send Daily Report", use_container_width=True):
            st.success("Report generation initiated!")

    # Main content area - Updated with 5 tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Market Overview", "🔥 Top Movers", "📊 Breakout Analysis", 
        "📉 Advanced Charts", "🤖 AI Insights"
    ])

    with tab1:
        st.header("Market Overview")

        # Market News Section (Top of Overview)
        st.subheader("Latest Financial News")
        try:
            if 'latest_news' not in st.session_state:
                with st.spinner("Loading latest market news..."):
                    st.session_state.latest_news = get_financial_news()

            news_articles = st.session_state.latest_news[:8]  # Show top 8 in main area

            # Display news in 2 columns
            news_col1, news_col2 = st.columns(2)
            for i, article in enumerate(news_articles):
                with news_col1 if i % 2 == 0 else news_col2:
                    st.markdown(f"""
                    <div style='padding: 2rem; margin: 2rem 0; background: linear-gradient(145deg, #C6AC8E, #EAEOD5); 
                         border-radius: 10px; border: 2px solid #000000; box-shadow: 0 4px 8px rgba(0,0,0,0.1);'>
                        <h4 style='margin: 0; font-size: 1rem; font-weight: bold; color: #000000; line-height: 1.2;'>{article['title']}</h4>
                        <p style='margin: 0.3rem 0 0 0; font-size: 0.75rem; opacity: 0.8; color: #000000;'>
                            📺 {article['source']} • ⏰ {article['timestamp']}
                        </p>
                        {f"<p style='margin: 0.3rem 0 0 0; font-size: 0.7rem;'><a href='{article['url']}' target='_blank' style='color: #000000; text-decoration: none;'>🔗 Read Full Article</a></p>" if article['url'] != '#' else ''}
                    </div>
                    """,
                                unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error loading news: {str(e)}")
            st.info("News service temporarily unavailable")

        st.markdown("---")

        # Market Indices Section
        st.subheader("Market Indices")
        col1, col2, col3, col4 = st.columns(4)

        # Market indices
        indices = ["^NSEI", "^BSESN", "^NSEBANK"]
        index_names = ["NIFTY 50", "SENSEX", "BANK NIFTY"]

        for i, (index, name) in enumerate(zip(indices, index_names)):
            try:
                ticker = yf.Ticker(index)
                hist = ticker.history(period="2d")
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    change = current - prev
                    change_pct = (change / prev) * 100

                    with [col1, col2, col3][i]:
                        st.metric(label=name,
                                  value=f"₹{current:,.2f}",
                                  delta=f"{change:+.2f} ({change_pct:+.2f}%)")
            except Exception as e:
                with [col1, col2, col3][i]:
                    st.error(f"Error loading {name}")

        # Market sentiment gauge
        with col4:
            try:
                sentiment_score = 0.65  # This would come from AI analysis
                st.metric(label="Market Sentiment",
                          value="Bullish" if sentiment_score > 0.6 else
                          "Bearish" if sentiment_score < 0.4 else "Neutral",
                          delta=f"Score: {sentiment_score:.2f}")
            except:
                st.error("Sentiment unavailable")

    with tab2:
        st.header("Top Gainers & Losers")
        try:
            gainers, losers = get_top_gainers_losers()

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Top Gainers")
                if not gainers.empty:
                    st.dataframe(
                        gainers[['Symbol', 'LTP', 'Change',
                                 '% Change']].head(10),
                        use_container_width=True,
                        hide_index=True)
                else:
                    st.info("No gainers data available")

            with col2:
                st.subheader("Top Losers")
                if not losers.empty:
                    st.dataframe(
                        losers[['Symbol', 'LTP', 'Change',
                                '% Change']].head(10),
                        use_container_width=True,
                        hide_index=True)
                else:
                    st.info("No losers data available")
        except Exception as e:
            st.error(f"Error loading top movers: {str(e)}")

    with tab3:
        st.header("NIFTY Breakout Analysis")
        st.markdown("Stocks breaking out above 6-8 day trading range")
        try:
            # Sample breakout analysis - in production this would analyze all NIFTY stocks
            breakout_data = {
                'Symbol': ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICI'],
                'Current Price': [2450, 3890, 1650, 1580, 950],
                'Breakout Level': [2420, 3850, 1620, 1550, 930],
                'Volume Spike': [2.3, 1.8, 2.1, 1.5, 2.0],
                'Days in Range': [7, 6, 8, 7, 6]
            }

            df_breakout = pd.DataFrame(breakout_data)

            # Histogram of breakout stocks
            fig = px.histogram(
                df_breakout,
                x='Days in Range',
                title="Distribution of Breakout Stocks by Days in Range",
                nbins=5,
                color_discrete_sequence=['#FF6B6B'])

            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

            # Breakout stocks table
            st.subheader("Current Breakout Stocks")
            st.dataframe(df_breakout,
                         use_container_width=True,
                         hide_index=True)
        except Exception as e:
            st.error(f"Error in breakout analysis: {str(e)}")

    # ── NEW TAB 4: ADVANCED CHARTS ──
    with tab4:
        st.header("Advanced Interactive Charts")
        st.markdown("Professional charting with advanced technical indicators")

        # Stock selection and controls
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            symbol_input = st.text_input("Enter NSE Symbol", value="RELIANCE", 
                                       placeholder="e.g., RELIANCE, TCS, INFY")
            symbol = symbol_input.upper().strip()

        with col2:
            period = st.selectbox("Timeframe", 
                                ["1mo", "3mo", "6mo", "1y", "2y"], 
                                index=2)

        with col3:
            st.markdown("<br>", unsafe_allow_html=True)  # Space for alignment
            load_chart = st.button("📊 Load Chart", use_container_width=True)

        # Indicator controls
        st.markdown("### 🎛️ Technical Indicators")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            show_supertrend = st.checkbox("🔥 Supertrend", value=True)
            show_bb = st.checkbox("📊 Bollinger Bands", value=True)

        with col2:
            show_sma = st.checkbox("📈 SMA 20/50", value=True)
            show_rsi = st.checkbox("⚡ RSI", value=True)

        with col3:
            show_macd = st.checkbox("🌊 MACD", value=False)
            show_fisher = st.checkbox("🐟 Fisher Transform", value=False)

        with col4:
            show_stoch = st.checkbox("📉 Stochastic", value=False)
            show_volume_profile = st.checkbox("📊 Volume Profile", value=False)

        if load_chart or symbol:
            try:
                with st.spinner(f"Loading chart data for {symbol}..."):
                    # Fetch data
                    ticker_symbol = f"{symbol}.NS"
                    data = yf.download(ticker_symbol, period=period, interval="1d")

                    if data.empty:
                        st.error(f"❌ No data found for {symbol}. Please check the symbol.")
                    else:
                        # Calculate all indicators
                        data['SMA_20'] = data['Close'].rolling(20).mean()
                        data['SMA_50'] = data['Close'].rolling(50).mean()

                        bb_middle, bb_upper, bb_lower = bollinger_bands(data['Close'])
                        data['BB_Middle'] = bb_middle
                        data['BB_Upper'] = bb_upper
                        data['BB_Lower'] = bb_lower

                        data['RSI'] = rsi(data['Close'])

                        supertrend_line, supertrend_direction = supertrend(data)
                        data['Supertrend'] = supertrend_line
                        data['ST_Direction'] = supertrend_direction

                        fisher, fisher_signal = fisher_transform(data['High'], data['Low'])
                        data['Fisher'] = fisher
                        data['Fisher_Signal'] = fisher_signal

                        macd_line, macd_signal, macd_histogram = macd(data['Close'])
                        data['MACD'] = macd_line
                        data['MACD_Signal'] = macd_signal
                        data['MACD_Histogram'] = macd_histogram

                        stoch_k, stoch_d = stochastic(data['High'], data['Low'], data['Close'])
                        data['Stoch_K'] = stoch_k
                        data['Stoch_D'] = stoch_d

                        # Get company info
                        info = yf.Ticker(ticker_symbol).info
                        company_name = info.get('longName', symbol)

                        # Stock info header
                        current_price = data['Close'].iloc[-1]
                        prev_price = data['Close'].iloc[-2]
                        change = current_price - prev_price
                        change_pct = (change / prev_price) * 100

                        st.markdown(f"""
                        <div class="chart-container">
                            <h2>📈 {company_name} ({symbol})</h2>
                            <h3>₹{current_price:.2f} 
                            <span style="color: {'#00d562' if change >= 0 else '#f85149'}">
                            {'+' if change >= 0 else ''}{change:.2f} ({change_pct:+.2f}%)</span></h3>
                        </div>
                        """, unsafe_allow_html=True)

                        # Main price chart
                        fig_main = go.Figure()

                        # Candlestick chart
                        fig_main.add_trace(go.Candlestick(
                            x=data.index,
                            open=data['Open'],
                            high=data['High'],
                            low=data['Low'],
                            close=data['Close'],
                            name="Price",
                            increasing_line_color='#00d562',
                            decreasing_line_color='#f85149'
                        ))

                        # Add indicators based on user selection
                        if show_sma:
                            fig_main.add_trace(go.Scatter(
                                x=data.index, y=data['SMA_20'],
                                line=dict(color='#ff9500', width=1),
                                name='SMA 20'
                            ))
                            fig_main.add_trace(go.Scatter(
                                x=data.index, y=data['SMA_50'],
                                line=dict(color='#0969da', width=1),
                                name='SMA 50'
                            ))

                        if show_bb:
                            fig_main.add_trace(go.Scatter(
                                x=data.index, y=data['BB_Upper'],
                                line=dict(color='#8b949e', width=1),
                                name='BB Upper', opacity=0.7
                            ))
                            fig_main.add_trace(go.Scatter(
                                x=data.index, y=data['BB_Lower'],
                                line=dict(color='#8b949e', width=1),
                                name='BB Lower', opacity=0.7,
                                fill='tonexty', fillcolor='rgba(139, 148, 158, 0.1)'
                            ))

                        if show_supertrend:
                            # Color supertrend based on direction
                            fig_main.add_trace(go.Scatter(
                                x=data.index, y=data['Supertrend'],
                                line=dict(color='#EB4511', width=2),
                                name='Supertrend'
                            ))

                        fig_main.update_layout(
                            title=f"{symbol} - Price Chart with Indicators",
                            template="plotly_dark",
                            height=600,
                            xaxis_rangeslider_visible=False,
                            showlegend=True
                        )

                        st.plotly_chart(fig_main, use_container_width=True)

                        # Sub-charts for oscillators
                        if show_rsi:
                            fig_rsi = go.Figure()
                            fig_rsi.add_trace(go.Scatter(
                                x=data.index, y=data['RSI'],
                                line=dict(color='#a855f7', width=2),
                                name='RSI'
                            ))

                            # Add RSI reference lines
                            fig_rsi.add_hline(y=70, line_dash="dash", 
                                            line_color="#f85149", annotation_text="Overbought (70)")
                            fig_rsi.add_hline(y=30, line_dash="dash", 
                                            line_color="#00d562", annotation_text="Oversold (30)")
                            fig_rsi.add_hline(y=50, line_dash="dot", 
                                            line_color="#8b949e", annotation_text="Midline (50)")

                            fig_rsi.update_layout(
                                title="RSI (Relative Strength Index)",
                                template="plotly_dark",
                                height=300,
                                yaxis=dict(range=[0, 100])
                            )

                            st.plotly_chart(fig_rsi, use_container_width=True)

                        if show_macd:
                            fig_macd = go.Figure()
                            fig_macd.add_trace(go.Scatter(
                                x=data.index, y=data['MACD'],
                                line=dict(color='#0969da', width=2),
                                name='MACD'
                            ))
                            fig_macd.add_trace(go.Scatter(
                                x=data.index, y=data['MACD_Signal'],
                                line=dict(color='#f85149', width=1),
                                name='Signal'
                            ))
                            fig_macd.add_trace(go.Bar(
                                x=data.index, y=data['MACD_Histogram'],
                                name='Histogram', marker_color='#8b949e',
                                opacity=0.7
                            ))

                            fig_macd.update_layout(
                                title="MACD (Moving Average Convergence Divergence)",
                                template="plotly_dark",
                                height=300
                            )

                            st.plotly_chart(fig_macd, use_container_width=True)

                        if show_fisher:
                            fig_fisher = go.Figure()
                            fig_fisher.add_trace(go.Scatter(
                                x=data.index, y=data['Fisher'],
                                line=dict(color='#00d562', width=2),
                                name='Fisher Transform'
                            ))
                            fig_fisher.add_trace(go.Scatter(
                                x=data.index, y=data['Fisher_Signal'],
                                line=dict(color='#f85149', width=1),
                                name='Fisher Signal'
                            ))

                            fig_fisher.update_layout(
                                title="Fisher Transform",
                                template="plotly_dark",
                                height=300
                            )

                            st.plotly_chart(fig_fisher, use_container_width=True)

                        if show_stoch:
                            fig_stoch = go.Figure()
                            fig_stoch.add_trace(go.Scatter(
                                x=data.index, y=data['Stoch_K'],
                                line=dict(color='#EB4511', width=2),
                                name='%K'
                            ))
                            fig_stoch.add_trace(go.Scatter(
                                x=data.index, y=data['Stoch_D'],
                                line=dict(color='#0969da', width=1),
                                name='%D'
                            ))

                            # Add reference lines
                            fig_stoch.add_hline(y=80, line_dash="dash", 
                                              line_color="#f85149", annotation_text="Overbought (80)")
                            fig_stoch.add_hline(y=20, line_dash="dash", 
                                              line_color="#00d562", annotation_text="Oversold (20)")

                            fig_stoch.update_layout(
                                title="Stochastic Oscillator",
                                template="plotly_dark",
                                height=300,
                                yaxis=dict(range=[0, 100])
                            )

                            st.plotly_chart(fig_stoch, use_container_width=True)

                        # Volume chart
                        fig_volume = go.Figure()
                        fig_volume.add_trace(go.Bar(
                            x=data.index, y=data['Volume'],
                            name='Volume',
                            marker_color='#8b949e',
                            opacity=0.7
                        ))

                        fig_volume.update_layout(
                            title="Volume Analysis",
                            template="plotly_dark",
                            height=250
                        )

                        st.plotly_chart(fig_volume, use_container_width=True)

                        if show_volume_profile:
                            # Volume Profile
                            vp_data = volume_profile(data['Close'], data['Volume'])

                            fig_vp = go.Figure()
                            fig_vp.add_trace(go.Bar(
                                y=vp_data['price'],
                                x=vp_data['volume'],
                                orientation='h',
                                name='Volume Profile',
                                marker_color='#EB4511',
                                opacity=0.7
                            ))

                            fig_vp.update_layout(
                                title="Volume Profile",
                                template="plotly_dark",
                                height=400,
                                xaxis_title="Volume",
                                yaxis_title="Price Level"
                            )

                            st.plotly_chart(fig_vp, use_container_width=True)

                        # Technical Analysis Summary
                        st.markdown("### 📊 Technical Analysis Summary")

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            current_rsi = data['RSI'].iloc[-1]
                            rsi_signal = "Overbought" if current_rsi > 70 else "Oversold" if current_rsi < 30 else "Neutral"
                            rsi_color = "#f85149" if current_rsi > 70 else "#00d562" if current_rsi < 30 else "#8b949e"

                            st.metric("RSI Signal", rsi_signal, f"{current_rsi:.1f}")

                        with col2:
                            st_direction = data['ST_Direction'].iloc[-1]
                            st_signal = "🟢 Bullish" if st_direction > 0 else "🔴 Bearish"
                            st.metric("Supertrend", st_signal)

                        with col3:
                            # MACD signal
                            if 'MACD' in data.columns and 'MACD_Signal' in data.columns:
                                macd_diff = data['MACD'].iloc[-1] - data['MACD_Signal'].iloc[-1]
                                macd_signal = "🟢 Bullish" if macd_diff > 0 else "🔴 Bearish"
                                st.metric("MACD Signal", macd_signal)
                            else:
                                st.metric("MACD Signal", "Not Available")

                        with col4:
                            # Volume trend
                            recent_volume = data['Volume'].iloc[-5:].mean()
                            avg_volume = data['Volume'].mean()
                            volume_trend = "🔥 High" if recent_volume > avg_volume * 1.5 else "📉 Low" if recent_volume < avg_volume * 0.5 else "➡️ Normal"
                            st.metric("Volume Trend", volume_trend)

            except Exception as e:
                st.error(f"❌ Error loading chart: {str(e)}")
                st.info("Please check the symbol and try again. Make sure to use NSE symbols like RELIANCE, TCS, INFY etc.")

    # ── TAB 5: AI INSIGHTS (Moved from Tab 4) ──
    with tab5:
        st.header("AI Market Insights")
        try:
            # AI-powered market analysis
            with st.spinner("Generating AI insights..."):
                insights = get_market_sentiment_analysis()
                if insights:
                    st.markdown("### 🤖 AI Market Analysis")
                    st.write(insights.get('analysis',
                                          'Analysis not available'))

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Probability Score",
                                  f"{insights.get('probability', 0):.1%}",
                                  help="AI confidence in market direction")

                    with col2:
                        st.metric("Trend Direction",
                                  insights.get('direction', 'Neutral'),
                                  help="Expected market movement")

                    with col3:
                        st.metric("Time Horizon",
                                  insights.get('duration', 'N/A'),
                                  help="Expected duration of trend")
                else:
                    st.info("AI insights temporarily unavailable")
        except Exception as e:
            st.error(f"Error generating AI insights: {str(e)}")

    # Footer
    st.markdown("---")
    st.markdown(
        "🚀 **Dravyum AI Trading Agent** | Real-time Indian market analysis with AI-powered insights | "
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
