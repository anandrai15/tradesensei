import streamlit as st
import json
import os
from datetime import datetime, time, timedelta
import sys

# Add the parent directory to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.scheduler import get_scheduler_instance
from utils.notifications import test_notification_setup, save_report_notification, save_alert_notification
from utils.ai_analysis import generate_daily_market_summary
from utils.market_data import get_top_gainers_losers, get_nifty_data

st.set_page_config(page_title="Reports & Settings - TRADESENSEI",
                   page_icon="🥋",
                   layout="wide")


def save_settings(settings):
    """Save settings to file"""
    try:
        with open('app_settings.json', 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving settings: {e}")
        return False


def load_settings():
    """Load settings from file"""
    try:
        if os.path.exists('app_settings.json'):
            with open('app_settings.json', 'r') as f:
                return json.load(f)
        else:
            # Return default settings
            return {
                'email_notifications': True,
                'whatsapp_notifications': True,
                'daily_report_time': '08:00',
                'recipient_email': 'user@example.com',
                'recipient_phone': '+919999999999',
                'report_frequency': 'daily',
                'include_ai_insights': True,
                'include_top_movers': True,
                'include_portfolio_summary': True,
                'alert_thresholds': {
                    'nifty_change': 2.0,
                    'stock_change': 5.0,
                    'volume_spike': 2.0
                },
                'watchlist_alerts': True,
                'portfolio_alerts': True
            }
    except Exception as e:
        st.error(f"Error loading settings: {e}")
        return {}


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
        <h1 style="margin: 0; font-size: 2.5rem;">Reports & Settings</h1>
        <p style="margin: 0.3rem 0 0 0; opacity: 0.9;">Configure automated reports and alert preferences</p>
    </div>
    """,
                unsafe_allow_html=True)

    # Load current settings
    if 'app_settings' not in st.session_state:
        st.session_state.app_settings = load_settings()

    settings = st.session_state.app_settings

    # Tab layout
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Report Settings", "🔔 Notifications", "⚡ Alerts", "🧪 Testing"])

    with tab1:
        st.header("📊 Daily Report Configuration")

        # Report schedule
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📅 Schedule Settings")

            report_frequency = st.selectbox(
                "Report Frequency", ["daily", "weekdays", "weekly"],
                index=["daily", "weekdays", "weekly"
                       ].index(settings.get('report_frequency', 'daily')))
            settings['report_frequency'] = report_frequency

            # Time selection
            report_time = st.time_input("Daily Report Time",
                                        value=time.fromisoformat(
                                            settings.get(
                                                'daily_report_time', '08:00')))
            settings['daily_report_time'] = report_time.strftime('%H:%M')

            # Timezone info
            st.info("📍 All times are in Indian Standard Time (IST)")

        with col2:
            st.subheader("📧 Delivery Settings")

            recipient_email = st.text_input(
                "Email Address",
                value=settings.get('recipient_email', 'user@example.com'),
                help="Email address for daily reports")
            settings['recipient_email'] = recipient_email

            recipient_phone = st.text_input(
                "WhatsApp Number",
                value=settings.get('recipient_phone', '+919999999999'),
                help="Phone number with country code (e.g., +919999999999)")
            settings['recipient_phone'] = recipient_phone

        # Report content
        st.subheader("📋 Report Content")

        col1, col2, col3 = st.columns(3)

        with col1:
            include_ai_insights = st.checkbox(
                "🤖 AI Market Insights",
                value=settings.get('include_ai_insights', True),
                help="Include AI-generated market analysis")
            settings['include_ai_insights'] = include_ai_insights

        with col2:
            include_top_movers = st.checkbox(
                "🔥 Top Gainers/Losers",
                value=settings.get('include_top_movers', True),
                help="Include top performing stocks")
            settings['include_top_movers'] = include_top_movers

        with col3:
            include_portfolio = st.checkbox(
                "💼 Portfolio Summary",
                value=settings.get('include_portfolio_summary', True),
                help="Include your portfolio performance")
            settings['include_portfolio_summary'] = include_portfolio

        # Additional options
        st.subheader("⚙️ Advanced Options")

        col1, col2 = st.columns(2)

        with col1:
            include_breakouts = st.checkbox(
                "🚀 Breakout Analysis",
                value=settings.get('include_breakouts', True),
                help="Include stocks breaking technical levels")
            settings['include_breakouts'] = include_breakouts

            include_sector_analysis = st.checkbox(
                "🏭 Sector Performance",
                value=settings.get('include_sector_analysis', True),
                help="Include sectoral performance overview")
            settings['include_sector_analysis'] = include_sector_analysis

        with col2:
            include_technical_levels = st.checkbox(
                "📈 Key Technical Levels",
                value=settings.get('include_technical_levels', True),
                help="Include support/resistance levels")
            settings['include_technical_levels'] = include_technical_levels

            include_news_sentiment = st.checkbox(
                "📰 News Sentiment",
                value=settings.get('include_news_sentiment', False),
                help="Include news-based market sentiment")
            settings['include_news_sentiment'] = include_news_sentiment

    with tab2:
        st.header("🔔 Notification Preferences")

        # Notification methods
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📧 Email Notifications")

            email_notifications = st.checkbox("Enable Email Notifications",
                                              value=settings.get(
                                                  'email_notifications', True))
            settings['email_notifications'] = email_notifications

            if email_notifications:
                st.success("✅ Email notifications enabled")

                email_types = st.multiselect(
                    "Email Notification Types", [
                        "Daily Reports", "Portfolio Alerts", "Market Alerts",
                        "Breakout Alerts"
                    ],
                    default=settings.get('email_types',
                                         ["Daily Reports", "Market Alerts"]))
                settings['email_types'] = email_types
            else:
                st.warning("⚠️ Email notifications disabled")

        with col2:
            st.subheader("💬 WhatsApp Notifications")

            whatsapp_notifications = st.checkbox(
                "Enable WhatsApp Notifications",
                value=settings.get('whatsapp_notifications', True))
            settings['whatsapp_notifications'] = whatsapp_notifications

            if whatsapp_notifications:
                st.success("✅ WhatsApp notifications enabled")

                whatsapp_types = st.multiselect(
                    "WhatsApp Notification Types", [
                        "Market Summary", "Critical Alerts",
                        "Portfolio Updates", "Quick Insights"
                    ],
                    default=settings.get(
                        'whatsapp_types',
                        ["Market Summary", "Critical Alerts"]))
                settings['whatsapp_types'] = whatsapp_types
            else:
                st.warning("⚠️ WhatsApp notifications disabled")

        # Notification timing
        st.subheader("⏰ Notification Timing")

        col1, col2, col3 = st.columns(3)

        with col1:
            market_open_alert = st.checkbox(
                "Market Opening Alert",
                value=settings.get('market_open_alert', True),
                help="Get notified when market opens")
            settings['market_open_alert'] = market_open_alert

        with col2:
            market_close_alert = st.checkbox(
                "Market Closing Summary",
                value=settings.get('market_close_alert', True),
                help="Get end-of-day market summary")
            settings['market_close_alert'] = market_close_alert

        with col3:
            midday_update = st.checkbox("Mid-day Update",
                                        value=settings.get(
                                            'midday_update', False),
                                        help="Get market update at lunch time")
            settings['midday_update'] = midday_update

        # Quiet hours
        st.subheader("🔇 Do Not Disturb")

        col1, col2 = st.columns(2)

        with col1:
            quiet_start = st.time_input(
                "Quiet Hours Start",
                value=time.fromisoformat(settings.get('quiet_start', '22:00')))
            settings['quiet_start'] = quiet_start.strftime('%H:%M')

        with col2:
            quiet_end = st.time_input("Quiet Hours End",
                                      value=time.fromisoformat(
                                          settings.get('quiet_end', '07:00')))
            settings['quiet_end'] = quiet_end.strftime('%H:%M')

        st.info(
            f"🔇 No notifications will be sent between {quiet_start} and {quiet_end}"
        )

    with tab3:
        st.header("⚡ Alert Configuration")

        # Price change alerts
        st.subheader("📊 Price Change Alerts")

        col1, col2 = st.columns(2)

        with col1:
            nifty_threshold = st.number_input(
                "NIFTY Change Threshold (%)",
                min_value=0.5,
                max_value=10.0,
                value=settings.get('alert_thresholds',
                                   {}).get('nifty_change', 2.0),
                step=0.5,
                help="Alert when NIFTY moves by this percentage")

            stock_threshold = st.number_input(
                "Individual Stock Threshold (%)",
                min_value=1.0,
                max_value=20.0,
                value=settings.get('alert_thresholds',
                                   {}).get('stock_change', 5.0),
                step=0.5,
                help="Alert for individual stock movements")

        with col2:
            volume_threshold = st.number_input(
                "Volume Spike Threshold (x)",
                min_value=1.5,
                max_value=10.0,
                value=settings.get('alert_thresholds',
                                   {}).get('volume_spike', 2.0),
                step=0.5,
                help="Alert when volume is X times the average")

            breakout_sensitivity = st.selectbox(
                "Breakout Alert Sensitivity", ["Low", "Medium", "High"],
                index=["Low", "Medium", "High"
                       ].index(settings.get('breakout_sensitivity', 'Medium')))

        # Update alert thresholds
        if 'alert_thresholds' not in settings:
            settings['alert_thresholds'] = {}

        settings['alert_thresholds']['nifty_change'] = nifty_threshold
        settings['alert_thresholds']['stock_change'] = stock_threshold
        settings['alert_thresholds']['volume_spike'] = volume_threshold
        settings['breakout_sensitivity'] = breakout_sensitivity

        # Portfolio alerts
        st.subheader("💼 Portfolio Alerts")

        col1, col2 = st.columns(2)

        with col1:
            portfolio_alerts = st.checkbox(
                "Enable Portfolio Alerts",
                value=settings.get('portfolio_alerts', True),
                help="Get alerts about your portfolio holdings")
            settings['portfolio_alerts'] = portfolio_alerts

            if portfolio_alerts:
                portfolio_threshold = st.number_input(
                    "Portfolio Alert Threshold (%)",
                    min_value=1.0,
                    max_value=10.0,
                    value=settings.get('portfolio_threshold', 3.0),
                    step=0.5,
                    help="Alert when portfolio moves by this percentage")
                settings['portfolio_threshold'] = portfolio_threshold

        with col2:
            watchlist_alerts = st.checkbox(
                "Enable Watchlist Alerts",
                value=settings.get('watchlist_alerts', True),
                help="Get alerts about watchlist stocks")
            settings['watchlist_alerts'] = watchlist_alerts

            if watchlist_alerts:
                watchlist_threshold = st.number_input(
                    "Watchlist Alert Threshold (%)",
                    min_value=1.0,
                    max_value=15.0,
                    value=settings.get('watchlist_threshold', 5.0),
                    step=0.5,
                    help="Alert when watchlist stocks move by this percentage")
                settings['watchlist_threshold'] = watchlist_threshold

        # Custom alerts
        st.subheader("Custom Price Alerts")

        if 'custom_alerts' not in settings:
            settings['custom_alerts'] = []

        # Add new custom alert
        with st.expander("➕ Add Custom Alert"):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                alert_symbol = st.text_input("Stock Symbol",
                                             placeholder="e.g., RELIANCE")

            with col2:
                alert_condition = st.selectbox("Condition", ["Above", "Below"])

            with col3:
                alert_price = st.number_input("Price",
                                              min_value=0.01,
                                              value=100.0)

            with col4:
                st.write("")  # Spacing
                if st.button("Add Alert"):
                    if alert_symbol and alert_price > 0:
                        new_alert = {
                            'symbol': alert_symbol.upper(),
                            'condition': alert_condition.lower(),
                            'price': alert_price,
                            'created': datetime.now().isoformat()
                        }
                        settings['custom_alerts'].append(new_alert)
                        st.success(
                            f"Alert added: {alert_symbol} {alert_condition.lower()} ₹{alert_price}"
                        )
                        st.rerun()

        # Display existing custom alerts
        if settings['custom_alerts']:
            st.write("**Active Custom Alerts:**")

            for i, alert in enumerate(settings['custom_alerts']):
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.write(
                        f"• {alert['symbol']} {alert['condition']} ₹{alert['price']:.2f}"
                    )

                with col2:
                    if st.button("🗑️", key=f"delete_alert_{i}"):
                        settings['custom_alerts'].pop(i)
                        st.rerun()

    with tab4:
        st.header("🧪 Testing & Diagnostics")

        # Test notifications
        st.subheader("📧 Test Notifications")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📧 Send Test Email", use_container_width=True):
                with st.spinner("Sending test email..."):
                    try:
                        success = send_email_report(
                            settings.get('recipient_email',
                                         'user@example.com'),
                            "🧪 Test Email - AI Trading Agent",
                            "<h2>Test Email</h2><p>Your email notifications are working correctly!</p><p>This is a test message from your AI Trading Agent.</p>"
                        )

                        if success:
                            st.success("✅ Test email sent successfully!")
                        else:
                            st.error("❌ Failed to send test email")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        with col2:
            if st.button("💬 Send Test WhatsApp", use_container_width=True):
                with st.spinner("Sending test WhatsApp..."):
                    try:
                        success = send_whatsapp_message(
                            settings.get('recipient_phone', '+919999999999'),
                            "🧪 Test message from AI Trading Agent! Your WhatsApp notifications are working perfectly. 🚀"
                        )

                        if success:
                            st.success("✅ Test WhatsApp sent successfully!")
                        else:
                            st.error("❌ Failed to send test WhatsApp")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        # System diagnostics
        st.subheader("🔧 System Diagnostics")

        if st.button("🔍 Run System Check", use_container_width=True):
            with st.spinner("Running diagnostics..."):
                try:
                    test_results = test_notification_setup()

                    st.write("**📊 Diagnostic Results:**")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.write("**Email Configuration:**")
                        if test_results.get('email_config'):
                            st.success("✅ Email settings configured")
                        else:
                            st.error("❌ Email settings missing")

                        if test_results.get('smtp_connection'):
                            st.success("✅ SMTP connection successful")
                        else:
                            st.error("❌ SMTP connection failed")

                    with col2:
                        st.write("**WhatsApp Configuration:**")
                        if test_results.get('twilio_config'):
                            st.success("✅ Twilio settings configured")
                        else:
                            st.error("❌ Twilio settings missing")

                        if test_results.get('twilio_connection'):
                            st.success("✅ Twilio connection successful")
                        else:
                            st.error("❌ Twilio connection failed")

                except Exception as e:
                    st.error(f"Diagnostic error: {str(e)}")

        # Scheduler status
        st.subheader("⏰ Scheduler Status")

        try:
            scheduler = get_scheduler_instance()

            if scheduler.running:
                st.success("✅ Automated scheduler is running")
            else:
                st.warning("⚠️ Automated scheduler is stopped")

            # Display scheduled jobs
            jobs = scheduler.get_scheduled_jobs()

            if jobs:
                st.write("**Scheduled Jobs:**")
                job_df = pd.DataFrame(jobs)
                st.dataframe(job_df, use_container_width=True, hide_index=True)

            # Scheduler controls
            col1, col2 = st.columns(2)

            with col1:
                if st.button("▶️ Start Scheduler"):
                    scheduler.start_scheduler()
                    st.success("Scheduler started!")
                    st.rerun()

            with col2:
                if st.button("⏸️ Stop Scheduler"):
                    scheduler.stop_scheduler()
                    st.warning("Scheduler stopped!")
                    st.rerun()

        except Exception as e:
            st.error(f"Scheduler error: {str(e)}")

        # Generate sample report
        st.subheader("📄 Sample Report Preview")

        if st.button("📖 Generate Sample Report"):
            with st.spinner("Generating sample daily report..."):
                try:
                    # Generate sample market summary
                    market_summary = generate_daily_market_summary()

                    if market_summary:
                        st.write("**Sample Daily Report Content:**")
                        st.markdown(market_summary)
                    else:
                        st.info(
                            "Sample report generation temporarily unavailable")

                except Exception as e:
                    st.error(f"Error generating sample report: {str(e)}")

    # Save settings button
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button("💾 Save All Settings", use_container_width=True):
            # Update session state
            st.session_state.app_settings = settings

            # Save to file
            if save_settings(settings):
                st.success("✅ Settings saved successfully!")

                # Restart scheduler with new settings if needed
                try:
                    scheduler = get_scheduler_instance()
                    if scheduler.running:
                        st.info("🔄 Restarting scheduler with new settings...")
                        scheduler.stop_scheduler()
                        scheduler.start_scheduler()
                except:
                    pass
            else:
                st.error("❌ Failed to save settings")

    # Environment variables info
    st.sidebar.header("🔧 Environment Setup")

    st.sidebar.info("""
    **Required Environment Variables:**
    - `OPENAI_API_KEY`: OpenAI API key
    - `EMAIL_ADDRESS`: SMTP email
    - `EMAIL_PASSWORD`: SMTP password  
    - `TWILIO_ACCOUNT_SID`: Twilio SID
    - `TWILIO_AUTH_TOKEN`: Twilio token
    - `TWILIO_PHONE_NUMBER`: Twilio phone
    """)

    # Current environment status
    env_vars = [
        'OPENAI_API_KEY', 'EMAIL_ADDRESS', 'EMAIL_PASSWORD',
        'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_PHONE_NUMBER'
    ]

    st.sidebar.write("**Environment Status:**")
    for var in env_vars:
        if os.environ.get(var):
            st.sidebar.success(f"✅ {var}")
        else:
            st.sidebar.error(f"❌ {var}")

    st.sidebar.markdown(
        f"**Last updated:** {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()
