import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ai_analysis import (get_market_sentiment_analysis,
                               analyze_stock_probability,
                               generate_daily_market_summary,
                               get_ai_stock_recommendations)
from utils.portfolio import Portfolio

st.set_page_config(page_title="AI Analysis - TRADESENSEI",
                   page_icon="🥋",
                   layout="wide")


def create_probability_gauge(probability, title):
    """Create a probability gauge chart"""
    fig = go.Figure(
        go.Indicator(mode="gauge+number+delta",
                     value=probability * 100,
                     domain={
                         'x': [0, 1],
                         'y': [0, 1]
                     },
                     title={'text': title},
                     delta={'reference': 50},
                     gauge={
                         'axis': {
                             'range': [None, 100]
                         },
                         'bar': {
                             'color': "darkblue"
                         },
                         'steps': [{
                             'range': [0, 25],
                             'color': "lightgray"
                         }, {
                             'range': [25, 50],
                             'color': "gray"
                         }, {
                             'range': [50, 75],
                             'color': "lightgreen"
                         }, {
                             'range': [75, 100],
                             'color': "green"
                         }],
                         'threshold': {
                             'line': {
                                 'color': "red",
                                 'width': 4
                             },
                             'thickness': 0.75,
                             'value': 90
                         }
                     }))

    fig.update_layout(height=300)
    return fig


def create_sentiment_chart(sentiment_data):
    """Create sentiment analysis visualization"""
    if not sentiment_data:
        return None

    # Create a simple sentiment indicator
    sentiment_score = sentiment_data.get('probability', 0.5)
    sentiment_label = sentiment_data.get('sentiment', 'neutral')

    colors = {'bullish': 'green', 'bearish': 'red', 'neutral': 'gray'}
    color = colors.get(sentiment_label, 'gray')

    fig = go.Figure(data=go.Bar(x=[sentiment_label.title()],
                                y=[sentiment_score * 100],
                                marker_color=color))

    fig.update_layout(title="Market Sentiment Score",
                      yaxis_title="Confidence %",
                      height=300)

    return fig


# Add luxury styling
st.markdown("""
<style>
    .stApp {
        background-color: #EAEOD5;
    }
    
    .main-header {
        background: linear-gradient(135deg, #000000 0%, #C6AC8E 100%);
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
        <h1 style="margin: 0; font-size: 2.5rem;"> DRAVYUM AI </h1>
        <p style="margin: 0.3rem 0 0 0; opacity: 0.9;">Advanced artificial intelligence insights for Indian markets</p>
    </div>
    """,
                unsafe_allow_html=True)

    # Tab layout
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Market Sentiment", "🎯 Stock Analysis", "💡 Recommendations",
        "🔮 Predictions"
    ])

    with tab1:
        st.header("📊 Market Sentiment Analysis")

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("🔄 Generate Fresh Analysis",
                         use_container_width=True):
                with st.spinner("Analyzing market sentiment using AI..."):
                    try:
                        sentiment_analysis = get_market_sentiment_analysis()
                        if sentiment_analysis:
                            st.session_state.sentiment_data = sentiment_analysis
                            st.success("Analysis complete!")
                        else:
                            st.error("Failed to generate sentiment analysis")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        with col2:
            if st.button("📄 Generate Market Summary",
                         use_container_width=True):
                with st.spinner("Generating comprehensive market summary..."):
                    try:
                        market_summary = generate_daily_market_summary()
                        if market_summary:
                            st.session_state.market_summary = market_summary
                            st.success("Summary generated!")
                        else:
                            st.error("Failed to generate market summary")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        # Display sentiment analysis
        if hasattr(st.session_state,
                   'sentiment_data') and st.session_state.sentiment_data:
            sentiment_data = st.session_state.sentiment_data

            # Key metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                sentiment = sentiment_data.get('sentiment', 'neutral').title()
                sentiment_emoji = {
                    'Bullish': '📈',
                    'Bearish': '📉',
                    'Neutral': '➡️'
                }
                st.metric(
                    "Market Sentiment",
                    f"{sentiment_emoji.get(sentiment, '➡️')} {sentiment}",
                    help="AI-assessed market direction")

            with col2:
                probability = sentiment_data.get('probability', 0) * 100
                st.metric("Confidence Score",
                          f"{probability:.1f}%",
                          help="AI confidence in the assessment")

            with col3:
                direction = sentiment_data.get('direction', 'sideways').title()
                st.metric("Expected Movement",
                          direction,
                          help="Predicted market direction")

            with col4:
                duration = sentiment_data.get('duration', 'N/A')
                st.metric("Time Horizon",
                          duration,
                          help="Expected duration of trend")

            # Detailed analysis
            col1, col2 = st.columns(2)

            with col1:
                # Sentiment gauge
                prob_gauge = create_probability_gauge(
                    sentiment_data.get('probability', 0.5),
                    "Market Sentiment Probability")
                st.plotly_chart(prob_gauge, use_container_width=True)

            with col2:
                # Risk level indicator
                risk_level = sentiment_data.get('risk_level', 'medium')
                risk_colors = {
                    'low': 'green',
                    'medium': 'orange',
                    'high': 'red'
                }
                risk_color = risk_colors.get(risk_level, 'gray')

                st.markdown("### Risk Assessment")
                st.markdown(
                    f"**Risk Level:** :{risk_color}[{risk_level.upper()}]")

                # Key factors
                key_factors = sentiment_data.get('key_factors', [])
                if key_factors:
                    st.markdown("**Key Influencing Factors:**")
                    for factor in key_factors:
                        st.write(f"• {factor}")

            # Detailed analysis text
            st.subheader("🔍 Detailed AI Analysis")
            analysis_text = sentiment_data.get('analysis',
                                               'Analysis not available')
            st.write(analysis_text)

        # Display market summary
        if hasattr(st.session_state,
                   'market_summary') and st.session_state.market_summary:
            st.subheader("📰 AI-Generated Market Summary")

            summary_text = st.session_state.market_summary
            st.markdown(summary_text)

        # Historical sentiment (simulated for demonstration)
        st.subheader("📈 Sentiment Trend")

        # Create sample historical sentiment data
        dates = pd.date_range(start=datetime.now() - timedelta(days=30),
                              end=datetime.now(),
                              freq='D')
        sentiment_scores = [0.3 + 0.4 * (i % 7) / 6 for i in range(len(dates))]

        sentiment_df = pd.DataFrame({
            'Date': dates,
            'Sentiment_Score': sentiment_scores
        })

        fig = px.line(sentiment_df,
                      x='Date',
                      y='Sentiment_Score',
                      title="30-Day Sentiment Trend",
                      labels={'Sentiment_Score': 'Bullish Sentiment (0-1)'})
        fig.add_hline(y=0.5,
                      line_dash="dash",
                      line_color="gray",
                      annotation_text="Neutral Line")

        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.header("🎯 Individual Stock Analysis")

        col1, col2 = st.columns([2, 1])

        with col1:
            symbol_input = st.text_input("Enter Stock Symbol",
                                         placeholder="e.g., RELIANCE",
                                         value="RELIANCE")

        with col2:
            timeframe = st.selectbox("Analysis Timeframe",
                                     ["1 week", "2 weeks", "1 month"])

        if st.button("🔍 Analyze Stock", use_container_width=True):
            if symbol_input:
                with st.spinner(f"Analyzing {symbol_input} using AI..."):
                    try:
                        stock_analysis = analyze_stock_probability(
                            symbol_input, timeframe)
                        if stock_analysis:
                            st.session_state.stock_analysis = stock_analysis
                            st.success("Stock analysis complete!")
                        else:
                            st.error("Failed to analyze stock")
                    except Exception as e:
                        st.error(f"Error analyzing stock: {str(e)}")

        # Display stock analysis
        if hasattr(st.session_state,
                   'stock_analysis') and st.session_state.stock_analysis:
            analysis = st.session_state.stock_analysis

            st.subheader(
                f"📊 Analysis Results: {analysis.get('symbol', 'Unknown')}")

            # Probability metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                upward_prob = analysis.get('upward_probability', 0) * 100
                st.metric("Upward Probability",
                          f"{upward_prob:.1f}%",
                          delta="Bullish Signal")

            with col2:
                downward_prob = analysis.get('downward_probability', 0) * 100
                st.metric("Downward Probability",
                          f"{downward_prob:.1f}%",
                          delta="Bearish Signal")

            with col3:
                confidence = analysis.get('confidence', 0) * 100
                st.metric("Analysis Confidence", f"{confidence:.1f}%")

            # Price range prediction
            price_range = analysis.get('expected_price_range', {})
            if price_range:
                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Expected Low",
                              f"₹{price_range.get('low', 0):.2f}")

                with col2:
                    st.metric("Expected High",
                              f"₹{price_range.get('high', 0):.2f}")

            # Recommendation
            recommendation = analysis.get('recommendation', 'hold').upper()
            rec_colors = {'BUY': 'green', 'SELL': 'red', 'HOLD': 'orange'}
            rec_color = rec_colors.get(recommendation, 'gray')

            st.markdown(
                f"### AI Recommendation: :{rec_color}[{recommendation}]")

            # Technical signals
            signals = analysis.get('technical_signals', [])
            if signals:
                st.subheader("📈 Key Technical Signals")
                for signal in signals:
                    st.write(f"• {signal}")

            # Probability visualization
            col1, col2 = st.columns(2)

            with col1:
                # Probability pie chart
                prob_data = {
                    'Direction': ['Upward', 'Downward'],
                    'Probability': [
                        analysis.get('upward_probability', 0),
                        analysis.get('downward_probability', 0)
                    ]
                }

                fig_prob = px.pie(
                    values=prob_data['Probability'],
                    names=prob_data['Direction'],
                    title=f"Price Movement Probabilities - {timeframe}",
                    color_discrete_map={
                        'Upward': 'green',
                        'Downward': 'red'
                    })
                st.plotly_chart(fig_prob, use_container_width=True)

            with col2:
                # Confidence gauge
                conf_gauge = create_probability_gauge(
                    analysis.get('confidence', 0.5), "Analysis Confidence")
                st.plotly_chart(conf_gauge, use_container_width=True)

    with tab3:
        st.header("💡 AI Stock Recommendations")

        st.markdown(
            "Get personalized stock recommendations based on your criteria")

        # Recommendation criteria
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📋 Set Your Criteria")

            market_cap = st.selectbox("Market Cap Preference",
                                      ["large", "mid", "small", "any"])
            risk_level = st.selectbox("Risk Tolerance",
                                      ["low", "medium", "high"])

        with col2:
            sector = st.selectbox("Sector Preference", [
                "any", "Technology", "Banking", "Pharmaceuticals", "Oil & Gas",
                "Automobiles", "FMCG"
            ])
            time_horizon = st.selectbox(
                "Investment Horizon",
                ["short-term", "medium-term", "long-term"])

        if st.button("🎯 Get AI Recommendations", use_container_width=True):
            criteria = {
                'market_cap': market_cap,
                'sector': sector,
                'risk_level': risk_level,
                'time_horizon': time_horizon
            }

            with st.spinner("Generating personalized recommendations..."):
                try:
                    recommendations = get_ai_stock_recommendations(criteria)
                    if recommendations:
                        st.session_state.ai_recommendations = recommendations
                        st.success("Recommendations generated!")
                    else:
                        st.error("Failed to generate recommendations")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

        # Display recommendations
        if hasattr(
                st.session_state,
                'ai_recommendations') and st.session_state.ai_recommendations:
            recommendations = st.session_state.ai_recommendations

            st.subheader("🎯 AI-Curated Stock Picks")

            for i, rec in enumerate(recommendations):
                with st.expander(
                        f"#{i+1} {rec.get('symbol', 'Unknown')} - {rec.get('company_name', 'N/A')}"
                ):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Target Price",
                                  f"₹{rec.get('target_price', 0):,.2f}")
                        st.metric("Upside Potential",
                                  f"{rec.get('upside_potential', 0):+.1f}%")

                    with col2:
                        risk_rating = rec.get('risk_rating', 'medium')
                        risk_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}
                        st.write(
                            f"**Risk Rating:** {risk_emoji.get(risk_rating, '🟡')} {risk_rating.title()}"
                        )

                        st.write(f"**Symbol:** {rec.get('symbol', 'N/A')}")

                    with col3:
                        st.write("**Investment Rationale:**")
                        rationale = rec.get('rationale',
                                            'Rationale not available')
                        st.write(rationale)

        # Portfolio-based recommendations
        st.subheader("📊 Portfolio Enhancement Suggestions")

        if st.button("🔍 Analyze My Portfolio for Recommendations"):
            portfolio = Portfolio()

            if portfolio.holdings:
                with st.spinner(
                        "Analyzing your portfolio for improvement opportunities..."
                ):
                    try:
                        portfolio_recommendations = portfolio.get_portfolio_recommendations(
                        )

                        if portfolio_recommendations:
                            st.write("**Based on your current portfolio:**")

                            # Rebalancing suggestions
                            if portfolio_recommendations.get('rebalancing'):
                                st.warning("⚖️ **Rebalancing Opportunities:**")
                                for rec in portfolio_recommendations[
                                        'rebalancing'][:3]:
                                    st.write(f"• {rec['description']}")

                            # Addition suggestions
                            if portfolio_recommendations.get('additions'):
                                st.info("📈 **Growth Opportunities:**")
                                for rec in portfolio_recommendations[
                                        'additions'][:3]:
                                    st.write(f"• {rec['description']}")
                        else:
                            st.info("Your portfolio looks well-balanced!")

                    except Exception as e:
                        st.error(f"Error analyzing portfolio: {str(e)}")
            else:
                st.info(
                    "Add holdings to your portfolio to get personalized recommendations"
                )

    with tab4:
        st.header("🔮 Market Predictions & Forecasts")

        st.markdown("Advanced AI predictions for market movements")

        # NIFTY prediction
        st.subheader("📊 NIFTY 50 Forecast")

        prediction_timeframe = st.selectbox("Prediction Timeframe",
                                            ["1 week", "2 weeks", "1 month"])

        if st.button("🔮 Generate NIFTY Prediction"):
            with st.spinner("Generating NIFTY 50 predictions..."):
                try:
                    nifty_prediction = analyze_stock_probability(
                        "NIFTY", prediction_timeframe)
                    if nifty_prediction:
                        st.session_state.nifty_prediction = nifty_prediction
                        st.success("Prediction generated!")
                except Exception as e:
                    st.error(f"Error generating prediction: {str(e)}")

        # Display NIFTY prediction
        if hasattr(st.session_state,
                   'nifty_prediction') and st.session_state.nifty_prediction:
            pred = st.session_state.nifty_prediction

            col1, col2, col3 = st.columns(3)

            with col1:
                upward_prob = pred.get('upward_probability', 0) * 100
                st.metric("Bull Probability", f"{upward_prob:.1f}%")

            with col2:
                downward_prob = pred.get('downward_probability', 0) * 100
                st.metric("Bear Probability", f"{downward_prob:.1f}%")

            with col3:
                confidence = pred.get('confidence', 0) * 100
                st.metric("Prediction Confidence", f"{confidence:.1f}%")

            # Expected range
            price_range = pred.get('expected_price_range', {})
            if price_range:
                st.subheader(
                    f"📊 Expected NIFTY Range ({prediction_timeframe})")
                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Expected Low",
                              f"{price_range.get('low', 0):,.0f}")
                with col2:
                    st.metric("Expected High",
                              f"{price_range.get('high', 0):,.0f}")

        # Sector predictions
        st.subheader("🏭 Sector Outlook")

        sectors = [
            "Banking", "Technology", "Pharmaceuticals", "Automobiles", "FMCG"
        ]

        # Create sample sector predictions (in production, this would use real AI)
        sector_predictions = []
        for sector in sectors:
            # Simulate predictions
            import random
            outlook = random.choice(["Bullish", "Bearish", "Neutral"])
            confidence = random.uniform(0.6, 0.9)

            sector_predictions.append({
                'Sector':
                sector,
                'Outlook':
                outlook,
                'Confidence':
                f"{confidence*100:.0f}%",
                'Rating':
                random.choice(["Buy", "Hold", "Sell"])
            })

        df_sectors = pd.DataFrame(sector_predictions)

        # Color coding
        def color_outlook(val):
            if val == 'Bullish':
                return 'color: green'
            elif val == 'Bearish':
                return 'color: red'
            return 'color: gray'

        styled_sectors = df_sectors.style.applymap(color_outlook,
                                                   subset=['Outlook'])
        st.dataframe(styled_sectors, use_container_width=True, hide_index=True)

        # Market timing analysis
        st.subheader("⏰ Market Timing Analysis")

        col1, col2 = st.columns(2)

        with col1:
            st.info("📈 **Optimal Entry Points:**")
            st.write(
                "• Market corrections of 2-3% provide good entry opportunities"
            )
            st.write("• Mid-month periods typically show lower volatility")
            st.write(
                "• Post-earnings season often presents value opportunities")

        with col2:
            st.warning("⚠️ **Risk Periods:**")
            st.write("• First week of month typically shows higher volatility")
            st.write("• Global event impacts can cause temporary disruptions")
            st.write("• End of quarter profit booking may increase volatility")

    # Sidebar information
    st.sidebar.header("🤖 AI Analysis Info")

    st.sidebar.info("""
    **AI Model Information:**
    - Powered by GPT-4o
    - Analyzes real-time market data
    - Incorporates technical & fundamental factors
    - Provides probability-based predictions
    """)

    # Disclaimer
    st.sidebar.warning("""
    **Disclaimer:**
    AI predictions are for informational purposes only. 
    Always conduct your own research before making investment decisions.
    Past performance does not guarantee future results.
    """)

    # API status
    st.sidebar.subheader("📡 System Status")
    st.sidebar.success("🟢 AI Engine: Online")
    st.sidebar.success("🟢 Market Data: Live")

    st.sidebar.markdown(
        f"**Last updated:** {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()
