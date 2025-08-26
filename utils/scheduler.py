import schedule
import time
import threading
from datetime import datetime, timedelta
import logging
from typing import Callable, Dict, List
import os
from .market_data import get_nifty_data, get_top_gainers_losers, get_market_status
from .ai_analysis import generate_daily_market_summary, get_market_sentiment_analysis
from .notifications import send_daily_notifications
from .portfolio import Portfolio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)

class TradingScheduler:
    def __init__(self):
        self.running = False
        self.scheduler_thread = None
        self.portfolio = Portfolio()
        
        # Configuration from environment variables
        self.notification_email = os.environ.get("NOTIFICATION_EMAIL", "user@example.com")
        self.notification_phone = os.environ.get("NOTIFICATION_PHONE", "+919999999999")
        
        # Market timing (IST)
        self.market_open_time = "09:15"
        self.market_close_time = "15:30"
        self.daily_report_time = "08:00"  # Before market opens
        
        # Setup scheduled jobs
        self._setup_scheduled_jobs()
    
    def _setup_scheduled_jobs(self):
        """Setup all scheduled jobs"""
        try:
            # Daily morning report
            schedule.every().day.at(self.daily_report_time).do(self._send_daily_report)
            
            # Market opening alert
            schedule.every().monday.at(self.market_open_time).do(self._market_opening_alert)
            schedule.every().tuesday.at(self.market_open_time).do(self._market_opening_alert)
            schedule.every().wednesday.at(self.market_open_time).do(self._market_opening_alert)
            schedule.every().thursday.at(self.market_open_time).do(self._market_opening_alert)
            schedule.every().friday.at(self.market_open_time).do(self._market_opening_alert)
            
            # Market closing summary
            schedule.every().monday.at(self.market_close_time).do(self._market_closing_summary)
            schedule.every().tuesday.at(self.market_close_time).do(self._market_closing_summary)
            schedule.every().wednesday.at(self.market_close_time).do(self._market_closing_summary)
            schedule.every().thursday.at(self.market_close_time).do(self._market_closing_summary)
            schedule.every().friday.at(self.market_close_time).do(self._market_closing_summary)
            
            # Portfolio review (weekly)
            schedule.every().friday.at("17:00").do(self._weekly_portfolio_review)
            
            # Hourly market monitoring during trading hours
            for hour in range(9, 16):  # 9 AM to 3 PM
                for minute in [0, 30]:  # Every 30 minutes
                    time_str = f"{hour:02d}:{minute:02d}"
                    schedule.every().monday.at(time_str).do(self._hourly_market_check)
                    schedule.every().tuesday.at(time_str).do(self._hourly_market_check)
                    schedule.every().wednesday.at(time_str).do(self._hourly_market_check)
                    schedule.every().thursday.at(time_str).do(self._hourly_market_check)
                    schedule.every().friday.at(time_str).do(self._hourly_market_check)
            
            logging.info("Scheduled jobs setup completed")
            
        except Exception as e:
            logging.error(f"Error setting up scheduled jobs: {e}")
    
    def _send_daily_report(self):
        """Generate and send daily market report"""
        try:
            logging.info("Generating daily market report...")
            
            # Generate market summary using AI
            market_summary = generate_daily_market_summary()
            
            # Get market data
            gainers, losers = get_top_gainers_losers()
            
            # Get AI insights
            ai_insights = get_market_sentiment_analysis()
            
            # Get NIFTY change
            nifty_data = get_nifty_data(period="2d")
            nifty_change = 0
            if not nifty_data.empty and len(nifty_data) >= 2:
                current = nifty_data['Close'].iloc[-1]
                previous = nifty_data['Close'].iloc[-2]
                nifty_change = ((current - previous) / previous) * 100
            
            # Prepare market data for notifications
            market_data = {
                'summary': market_summary or "Market analysis not available",
                'gainers': gainers.to_dict('records') if not gainers.empty else [],
                'losers': losers.to_dict('records') if not losers.empty else [],
                'ai_insights': ai_insights or {},
                'nifty_change': nifty_change,
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            
            # Send notifications
            notification_results = send_daily_notifications(
                self.notification_email,
                self.notification_phone,
                market_data
            )
            
            logging.info(f"Daily report sent - Email: {notification_results['email']}, WhatsApp: {notification_results['whatsapp']}")
            
        except Exception as e:
            logging.error(f"Error sending daily report: {e}")
    
    def _market_opening_alert(self):
        """Send market opening alert"""
        try:
            market_status = get_market_status()
            
            if market_status.get('is_open', False):
                message = "🚀 Market is now OPEN! Good luck with your trades today."
                
                # Send quick alert
                from .notifications import send_whatsapp_message
                send_whatsapp_message(self.notification_phone, message)
                
                logging.info("Market opening alert sent")
        
        except Exception as e:
            logging.error(f"Error sending market opening alert: {e}")
    
    def _market_closing_summary(self):
        """Send market closing summary"""
        try:
            # Get end-of-day data
            nifty_data = get_nifty_data(period="1d")
            gainers, losers = get_top_gainers_losers()
            
            if not nifty_data.empty:
                current_price = nifty_data['Close'].iloc[-1]
                # Get previous day's close for comparison
                prev_data = get_nifty_data(period="2d")
                if len(prev_data) >= 2:
                    prev_price = prev_data['Close'].iloc[-2]
                    change = current_price - prev_price
                    change_pct = (change / prev_price) * 100
                else:
                    change_pct = 0
                
                direction = "📈" if change_pct >= 0 else "📉"
                
                message = f"""🔔 Market CLOSED
                
{direction} NIFTY 50: {current_price:.2f} ({change_pct:+.2f}%)

📊 Top Performer: {gainers.iloc[0]['Symbol'] if not gainers.empty else 'N/A'}
📊 Worst Performer: {losers.iloc[0]['Symbol'] if not losers.empty else 'N/A'}

See you tomorrow! 🌙"""
                
                from .notifications import send_whatsapp_message
                send_whatsapp_message(self.notification_phone, message)
                
                logging.info("Market closing summary sent")
        
        except Exception as e:
            logging.error(f"Error sending market closing summary: {e}")
    
    def _hourly_market_check(self):
        """Hourly market monitoring during trading hours"""
        try:
            market_status = get_market_status()
            
            if not market_status.get('is_open', False):
                return
            
            # Check for significant market movements
            nifty_data = get_nifty_data(period="1d")
            
            if not nifty_data.empty and len(nifty_data) >= 2:
                current_price = nifty_data['Close'].iloc[-1]
                hour_ago_price = nifty_data['Close'].iloc[-2] if len(nifty_data) >= 2 else current_price
                
                hourly_change = ((current_price - hour_ago_price) / hour_ago_price) * 100
                
                # Alert for significant movements (>1% in an hour)
                if abs(hourly_change) > 1.0:
                    direction = "📈 SURGE" if hourly_change > 0 else "📉 FALL"
                    
                    message = f"""🚨 MARKET ALERT
                    
{direction}: NIFTY moved {hourly_change:+.2f}% in the last hour!

Current: {current_price:.2f}
Time: {datetime.now().strftime('%H:%M')}

Stay alert! 👀"""
                    
                    from .notifications import send_whatsapp_message
                    send_whatsapp_message(self.notification_phone, message)
                    
                    logging.info(f"Significant market movement alert sent: {hourly_change:.2f}%")
        
        except Exception as e:
            logging.error(f"Error in hourly market check: {e}")
    
    def _weekly_portfolio_review(self):
        """Weekly portfolio performance review"""
        try:
            portfolio_summary = self.portfolio.get_portfolio_summary()
            
            if portfolio_summary.get('holdings_count', 0) == 0:
                return
            
            total_pnl_pct = portfolio_summary.get('total_pnl_percent', 0)
            top_performer = portfolio_summary.get('top_performer', {})
            worst_performer = portfolio_summary.get('worst_performer', {})
            
            performance_emoji = "🟢" if total_pnl_pct >= 0 else "🔴"
            
            message = f"""📊 WEEKLY PORTFOLIO REVIEW
            
{performance_emoji} Overall P&L: {total_pnl_pct:+.2f}%
💰 Portfolio Value: ₹{portfolio_summary.get('total_value', 0):,.2f}

🏆 Best: {top_performer.get('symbol', 'N/A')} ({top_performer.get('pnl_percent', 0):+.1f}%)
📉 Worst: {worst_performer.get('symbol', 'N/A')} ({worst_performer.get('pnl_percent', 0):+.1f}%)

Review your strategy! 💡"""
            
            from .notifications import send_whatsapp_message
            send_whatsapp_message(self.notification_phone, message)
            
            # Also send detailed email report
            portfolio_data = self.portfolio.export_portfolio_data()
            from .notifications import send_email_report
            
            email_subject = f"Weekly Portfolio Review - {datetime.now().strftime('%Y-%m-%d')}"
            email_body = f"""
            <h2>Weekly Portfolio Performance Report</h2>
            <p>Overall P&L: {total_pnl_pct:+.2f}%</p>
            <p>Portfolio Value: ₹{portfolio_summary.get('total_value', 0):,.2f}</p>
            <p>Holdings Count: {portfolio_summary.get('holdings_count', 0)}</p>
            """
            
            send_email_report(self.notification_email, email_subject, email_body)
            
            logging.info("Weekly portfolio review sent")
        
        except Exception as e:
            logging.error(f"Error in weekly portfolio review: {e}")
    
    def start_scheduler(self):
        """Start the scheduler in a separate thread"""
        if self.running:
            logging.warning("Scheduler is already running")
            return
        
        self.running = True
        
        def run_scheduler():
            logging.info("Scheduler started")
            while self.running:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logging.error(f"Error in scheduler loop: {e}")
                    time.sleep(60)
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logging.info("Scheduler thread started")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        if not self.running:
            logging.warning("Scheduler is not running")
            return
        
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        logging.info("Scheduler stopped")
    
    def get_scheduled_jobs(self) -> List[Dict]:
        """Get list of scheduled jobs"""
        jobs = []
        for job in schedule.jobs:
            jobs.append({
                'job_func': job.job_func.__name__,
                'interval': str(job.interval),
                'unit': job.unit,
                'at_time': str(job.at_time) if job.at_time else None,
                'next_run': str(job.next_run) if job.next_run else None
            })
        return jobs
    
    def add_custom_alert(self, symbol: str, condition: str, value: float, alert_type: str = "price"):
        """Add custom price or percentage alerts"""
        try:
            # This would be implemented to add custom alerts
            # For now, just log the request
            logging.info(f"Custom alert requested: {symbol} {condition} {value} ({alert_type})")
            
            # In a full implementation, this would:
            # 1. Store the alert in a database or file
            # 2. Add a scheduled job to check the condition
            # 3. Send notification when condition is met
            
        except Exception as e:
            logging.error(f"Error adding custom alert: {e}")
    
    def test_notifications(self) -> Dict:
        """Test notification system"""
        try:
            from .notifications import test_notification_setup
            
            test_results = test_notification_setup()
            
            # Send test messages if configuration is working
            if test_results['email_config'] and test_results['smtp_connection']:
                from .notifications import send_email_report
                send_email_report(
                    self.notification_email,
                    "🧪 Test Email - AI Trading Agent",
                    "<h2>Email notifications are working!</h2><p>Your daily reports will be delivered here.</p>"
                )
            
            if test_results['twilio_config'] and test_results['twilio_connection']:
                from .notifications import send_whatsapp_message
                send_whatsapp_message(
                    self.notification_phone,
                    "🧪 Test message from AI Trading Agent! WhatsApp notifications are working perfectly. 🚀"
                )
            
            logging.info(f"Notification test completed: {test_results}")
            return test_results
            
        except Exception as e:
            logging.error(f"Error testing notifications: {e}")
            return {'error': str(e)}

# Global scheduler instance
trading_scheduler = TradingScheduler()

def get_scheduler_instance():
    """Get the global scheduler instance"""
    return trading_scheduler
