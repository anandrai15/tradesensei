import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.portfolio import Portfolio
from utils.market_data import get_real_time_price, get_stock_data
from utils.fundamentals import get_fundamental_data

st.set_page_config(page_title="Portfolio Tracker - TRADESENSEI",
                   page_icon="🥋",
                   layout="wide")


def create_portfolio_pie_chart(sector_allocation):
    """Create pie chart for sector allocation"""
    if not sector_allocation:
        return None

    sectors = list(sector_allocation.keys())
    values = [sector_allocation[sector]['value'] for sector in sectors]

    fig = go.Figure(data=go.Pie(
        labels=sectors, values=values, hole=0.3, textinfo='label+percent'))

    fig.update_layout(title="Portfolio Sector Allocation", height=400)

    return fig


def create_performance_chart(performance_history):
    """Create portfolio performance timeline chart"""
    if not performance_history or 'portfolio_timeline' not in performance_history:
        return None

    timeline_data = performance_history['portfolio_timeline']
    dates = list(timeline_data.keys())
    values = list(timeline_data.values())

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(x=dates,
                   y=values,
                   mode='lines',
                   name='Portfolio Value',
                   line=dict(color='#FF6B6B', width=2)))

    fig.update_layout(title="Portfolio Performance Timeline",
                      xaxis_title="Date",
                      yaxis_title="Portfolio Value (₹)",
                      height=400)

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
        <h1 style="margin: 0; font-size: 2.5rem;">Portfolio Tracker</h1>
        <p style="margin: 0.3rem 0 0 0; opacity: 0.9;">Monitor and manage your investment portfolio</p>
    </div>
    """,
                unsafe_allow_html=True)

    # Initialize portfolio
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = Portfolio()

    portfolio = st.session_state.portfolio

    # Tab layout
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📈 Overview", "💼 Holdings", "👁️ Watchlist", "⚖️ Risk Analysis"])

    with tab1:
        st.header("Portfolio Overview")

        # Get portfolio summary
        portfolio_summary = portfolio.get_portfolio_summary()

        if portfolio_summary.get('holdings_count', 0) > 0:
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Value",
                          f"₹{portfolio_summary['total_value']:,.2f}",
                          help="Current market value of all holdings")

            with col2:
                st.metric("Total Invested",
                          f"₹{portfolio_summary['total_invested']:,.2f}",
                          help="Total amount invested")

            with col3:
                pnl = portfolio_summary['total_pnl']
                pnl_pct = portfolio_summary['total_pnl_percent']
                st.metric("Total P&L",
                          f"₹{pnl:,.2f}",
                          delta=f"{pnl_pct:+.2f}%",
                          help="Profit/Loss since investment")

            with col4:
                st.metric("Holdings",
                          portfolio_summary['holdings_count'],
                          help="Number of stocks in portfolio")

            # Performance charts
            col1, col2 = st.columns(2)

            with col1:
                # Sector allocation
                sector_allocation = portfolio.get_sector_allocation()
                pie_chart = create_portfolio_pie_chart(sector_allocation)

                if pie_chart:
                    st.plotly_chart(pie_chart, use_container_width=True)
                else:
                    st.info("Sector allocation data not available")

            with col2:
                # Performance history
                performance_history = portfolio.get_portfolio_performance_history(
                )
                perf_chart = create_performance_chart(performance_history)

                if perf_chart:
                    st.plotly_chart(perf_chart, use_container_width=True)
                else:
                    st.info("Performance history not available")

            # Holdings performance table
            st.subheader("📋 Holdings Performance")

            holdings_perf = portfolio_summary.get('holdings_performance', [])

            if holdings_perf:
                df_holdings = pd.DataFrame(holdings_perf)

                # Format the dataframe for display
                display_df = df_holdings[[
                    'symbol', 'quantity', 'buy_price', 'current_price',
                    'invested_amount', 'current_value', 'pnl', 'pnl_percent'
                ]].copy()

                display_df.columns = [
                    'Symbol', 'Quantity', 'Buy Price', 'Current Price',
                    'Invested', 'Current Value', 'P&L', 'P&L %'
                ]

                # Format numbers
                for col in ['Buy Price', 'Current Price']:
                    display_df[col] = display_df[col].round(2)

                for col in ['Invested', 'Current Value', 'P&L']:
                    display_df[col] = display_df[col].round(2)

                display_df['P&L %'] = display_df['P&L %'].round(2)

                # Color coding for P&L
                def color_pnl(val):
                    if val > 0:
                        return 'color: green'
                    elif val < 0:
                        return 'color: red'
                    return ''

                styled_df = display_df.style.applymap(color_pnl,
                                                      subset=['P&L', 'P&L %'])
                st.dataframe(styled_df,
                             use_container_width=True,
                             hide_index=True)

            # Top and worst performers
            if portfolio_summary.get(
                    'top_performer') and portfolio_summary.get(
                        'worst_performer'):
                col1, col2 = st.columns(2)

                with col1:
                    top = portfolio_summary['top_performer']
                    st.success(
                        f"🏆 **Best Performer:** {top['symbol']} (+{top['pnl_percent']:.2f}%)"
                    )

                with col2:
                    worst = portfolio_summary['worst_performer']
                    st.error(
                        f"📉 **Worst Performer:** {worst['symbol']} ({worst['pnl_percent']:.2f}%)"
                    )

            # Portfolio recommendations
            st.subheader("💡 AI Recommendations")

            with st.spinner("Generating portfolio recommendations..."):
                recommendations = portfolio.get_portfolio_recommendations()

                if recommendations:
                    if recommendations.get('rebalancing'):
                        st.warning("⚖️ **Rebalancing Suggestions:**")
                        for rec in recommendations['rebalancing']:
                            st.write(
                                f"• {rec['description']} (Priority: {rec.get('priority', 'Medium')})"
                            )

                    if recommendations.get('reductions'):
                        st.error("📉 **Consider Reviewing:**")
                        for rec in recommendations['reductions']:
                            st.write(f"• {rec['description']}")

                    if recommendations.get('additions'):
                        st.info("📈 **Growth Opportunities:**")
                        for rec in recommendations['additions']:
                            st.write(
                                f"• {rec['description']} (Priority: {rec.get('priority', 'Medium')})"
                            )
                else:
                    st.info(
                        "Portfolio recommendations not available at the moment"
                    )

        else:
            st.info(
                "📝 Your portfolio is empty. Add some holdings to get started!")

            # Quick add section
            st.subheader("🚀 Quick Add Holdings")

            with st.form("quick_add_form"):
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    symbol = st.text_input("Stock Symbol",
                                           placeholder="e.g., RELIANCE")
                with col2:
                    quantity = st.number_input("Quantity",
                                               min_value=1,
                                               value=10)
                with col3:
                    buy_price = st.number_input("Buy Price",
                                                min_value=0.01,
                                                value=100.0,
                                                step=0.01)
                with col4:
                    buy_date = st.date_input("Buy Date", value=datetime.now())

                submitted = st.form_submit_button("Add to Portfolio",
                                                  use_container_width=True)

                if submitted and symbol:
                    success = portfolio.add_holding(
                        symbol.upper(), quantity, buy_price,
                        buy_date.strftime('%Y-%m-%d'))

                    if success:
                        st.success(
                            f"Added {quantity} shares of {symbol.upper()} to portfolio!"
                        )
                        st.rerun()
                    else:
                        st.error("Failed to add holding. Please try again.")

    with tab2:
        st.header("💼 Manage Holdings")

        # Add new holding
        with st.expander("➕ Add New Holding", expanded=False):
            with st.form("add_holding_form"):
                col1, col2 = st.columns(2)

                with col1:
                    symbol = st.text_input("Stock Symbol*",
                                           placeholder="e.g., RELIANCE")
                    quantity = st.number_input("Quantity*",
                                               min_value=1,
                                               value=10)

                with col2:
                    buy_price = st.number_input("Buy Price*",
                                                min_value=0.01,
                                                value=100.0,
                                                step=0.01)
                    buy_date = st.date_input("Buy Date", value=datetime.now())

                submitted = st.form_submit_button("Add Holding")

                if submitted:
                    if symbol and quantity > 0 and buy_price > 0:
                        success = portfolio.add_holding(
                            symbol.upper(), quantity, buy_price,
                            buy_date.strftime('%Y-%m-%d'))

                        if success:
                            st.success(
                                f"Successfully added {quantity} shares of {symbol.upper()}!"
                            )
                            st.rerun()
                        else:
                            st.error(
                                "Failed to add holding. Please check your inputs."
                            )
                    else:
                        st.error("Please fill all required fields.")

        # Current holdings management
        if portfolio.holdings:
            st.subheader("📋 Current Holdings")

            for i, holding in enumerate(portfolio.holdings):
                with st.expander(
                        f"{holding['symbol']} - {holding['quantity']} shares"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**Symbol:** {holding['symbol']}")
                        st.write(f"**Quantity:** {holding['quantity']}")
                        st.write(f"**Buy Price:** ₹{holding['buy_price']:.2f}")
                        st.write(f"**Buy Date:** {holding['buy_date']}")

                    with col2:
                        # Get current price
                        current_price = get_real_time_price(holding['symbol'])
                        if current_price:
                            pnl = (current_price -
                                   holding['buy_price']) * holding['quantity']
                            pnl_pct = ((current_price - holding['buy_price']) /
                                       holding['buy_price']) * 100

                            st.write(
                                f"**Current Price:** ₹{current_price:.2f}")
                            st.write(
                                f"**Current Value:** ₹{current_price * holding['quantity']:,.2f}"
                            )

                            if pnl >= 0:
                                st.success(
                                    f"**P&L:** +₹{pnl:,.2f} (+{pnl_pct:.2f}%)")
                            else:
                                st.error(
                                    f"**P&L:** ₹{pnl:,.2f} ({pnl_pct:.2f}%)")
                        else:
                            st.warning("Current price unavailable")

                    with col3:
                        st.write("**Actions:**")

                        # Reduce quantity
                        reduce_qty = st.number_input(
                            f"Reduce quantity",
                            min_value=1,
                            max_value=holding['quantity'],
                            value=1,
                            key=f"reduce_{i}")

                        col_a, col_b = st.columns(2)

                        with col_a:
                            if st.button(f"Reduce", key=f"reduce_btn_{i}"):
                                success = portfolio.remove_holding(
                                    holding['symbol'], reduce_qty)
                                if success:
                                    st.success(f"Reduced {reduce_qty} shares")
                                    st.rerun()
                                else:
                                    st.error("Failed to reduce holding")

                        with col_b:
                            if st.button(f"Remove All", key=f"remove_btn_{i}"):
                                success = portfolio.remove_holding(
                                    holding['symbol'])
                                if success:
                                    st.success("Holding removed completely")
                                    st.rerun()
                                else:
                                    st.error("Failed to remove holding")
        else:
            st.info(
                "No holdings in portfolio. Add some holdings to get started!")

    with tab3:
        st.header("👁️ Watchlist Management")

        # Add to watchlist
        col1, col2 = st.columns([3, 1])

        with col1:
            new_symbol = st.text_input(
                "Add Stock to Watchlist",
                placeholder="Enter stock symbol (e.g., RELIANCE)")

        with col2:
            st.write("")  # Empty line for alignment
            if st.button("Add to Watchlist", use_container_width=True):
                if new_symbol:
                    success = portfolio.add_to_watchlist(new_symbol.upper())
                    if success:
                        st.success(f"Added {new_symbol.upper()} to watchlist!")
                        st.rerun()
                    else:
                        st.warning(
                            f"{new_symbol.upper()} is already in watchlist!")

        # Display watchlist
        if portfolio.watchlist:
            st.subheader("📋 Your Watchlist")

            watchlist_data = portfolio.get_watchlist_data()

            if watchlist_data:
                df_watchlist = pd.DataFrame(watchlist_data)

                # Format display
                display_cols = [
                    'symbol', 'company_name', 'current_price', 'change',
                    'change_percent', 'sector'
                ]
                df_display = df_watchlist[display_cols].copy()
                df_display.columns = [
                    'Symbol', 'Company', 'Price', 'Change', 'Change %',
                    'Sector'
                ]

                # Format numbers
                df_display['Price'] = df_display['Price'].round(2)
                df_display['Change'] = df_display['Change'].round(2)
                df_display['Change %'] = df_display['Change %'].round(2)

                # Color coding
                def color_change(val):
                    if val > 0:
                        return 'color: green'
                    elif val < 0:
                        return 'color: red'
                    return ''

                styled_watchlist = df_display.style.applymap(
                    color_change, subset=['Change', 'Change %'])
                st.dataframe(styled_watchlist,
                             use_container_width=True,
                             hide_index=True)

                # Remove from watchlist
                st.subheader("🗑️ Remove from Watchlist")

                col1, col2 = st.columns([3, 1])

                with col1:
                    symbol_to_remove = st.selectbox("Select symbol to remove:",
                                                    portfolio.watchlist)

                with col2:
                    st.write("")  # Alignment
                    if st.button("Remove", use_container_width=True):
                        success = portfolio.remove_from_watchlist(
                            symbol_to_remove)
                        if success:
                            st.success(
                                f"Removed {symbol_to_remove} from watchlist!")
                            st.rerun()
                        else:
                            st.error("Failed to remove from watchlist")
            else:
                st.info("Watchlist data temporarily unavailable")
        else:
            st.info("Your watchlist is empty. Add some stocks to monitor!")

    with tab4:
        st.header("⚖️ Risk Analysis")

        if portfolio.holdings:
            with st.spinner("Analyzing portfolio risk..."):
                risk_analysis = portfolio.calculate_portfolio_risk()

                if risk_analysis:
                    # Risk metrics
                    col1, col2, col3 = st.columns(3)

                    concentration = risk_analysis.get('concentration_risk', {})

                    with col1:
                        st.metric(
                            "Top 3 Holdings %",
                            f"{concentration.get('top_3_holdings_percentage', 0):.1f}%",
                            help="Percentage of portfolio in top 3 holdings")

                    with col2:
                        st.metric(
                            "Max Sector Allocation",
                            f"{concentration.get('max_sector_allocation', 0):.1f}%",
                            help="Highest sector concentration")

                    with col3:
                        st.metric(
                            "Diversification Score",
                            f"{risk_analysis.get('diversification_score', 0):.0f}/100",
                            help="Portfolio diversification rating")

                    # Risk assessment
                    st.subheader("📊 Risk Assessment")

                    # Concentration risk warnings
                    if concentration.get('top_3_holdings_percentage', 0) > 60:
                        st.error(
                            "⚠️ **High Concentration Risk**: Top 3 holdings represent more than 60% of portfolio"
                        )
                    elif concentration.get('top_3_holdings_percentage',
                                           0) > 40:
                        st.warning(
                            "⚠️ **Medium Concentration Risk**: Consider diversifying beyond top holdings"
                        )
                    else:
                        st.success(
                            "✅ **Good Diversification**: Holdings are well distributed"
                        )

                    if concentration.get('max_sector_allocation', 0) > 40:
                        st.error(
                            "⚠️ **High Sector Risk**: Over-concentration in single sector"
                        )
                    elif concentration.get('max_sector_allocation', 0) > 25:
                        st.warning(
                            "⚠️ **Medium Sector Risk**: Consider sector diversification"
                        )
                    else:
                        st.success(
                            "✅ **Good Sector Mix**: Well diversified across sectors"
                        )

                    # AI Risk Analysis
                    ai_analysis = risk_analysis.get('ai_analysis', {})
                    if ai_analysis:
                        st.subheader("🤖 AI Risk Insights")

                        col1, col2 = st.columns(2)

                        with col1:
                            if 'diversification_score' in ai_analysis:
                                st.metric(
                                    "AI Diversification Score",
                                    f"{ai_analysis['diversification_score']:.1f}/10"
                                )

                            if 'risk_rating' in ai_analysis:
                                st.metric("Risk Rating",
                                          f"{ai_analysis['risk_rating']}/10")

                        with col2:
                            if 'sector_concentration' in ai_analysis:
                                st.write("**Sector Breakdown:**")
                                for sector, pct in ai_analysis[
                                        'sector_concentration'].items():
                                    st.write(f"• {sector}: {pct}%")

                        if 'recommendations' in ai_analysis:
                            st.subheader("📋 Risk Mitigation Recommendations")
                            for rec in ai_analysis['recommendations']:
                                st.info(f"💡 {rec}")
                else:
                    st.warning("Risk analysis temporarily unavailable")
        else:
            st.info("Add holdings to your portfolio to analyze risk")

    # Sidebar actions
    st.sidebar.header("📊 Portfolio Actions")

    # Export portfolio
    if st.sidebar.button("📥 Export Portfolio Data", use_container_width=True):
        export_data = portfolio.export_portfolio_data()

        if export_data:
            # Convert to JSON for download
            import json
            json_data = json.dumps(export_data, indent=2, default=str)

            st.sidebar.download_button(
                label="Download JSON",
                data=json_data,
                file_name=
                f"portfolio_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json")

    # Portfolio summary
    portfolio_summary = portfolio.get_portfolio_summary()

    if portfolio_summary.get('holdings_count', 0) > 0:
        st.sidebar.metric("Portfolio Value",
                          f"₹{portfolio_summary['total_value']:,.2f}")
        st.sidebar.metric("Total P&L",
                          f"{portfolio_summary['total_pnl_percent']:+.2f}%")

    # Refresh data
    if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

    st.sidebar.markdown(
        f"**Last updated:** {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()
