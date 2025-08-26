import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import json
from typing import Tuple, Optional

def get_nifty_data(period: str = "1mo") -> pd.DataFrame:
    """
    Fetch NIFTY 50 historical data
    """
    try:
        nifty = yf.Ticker("^NSEI")
        data = nifty.history(period=period)
        return data
    except Exception as e:
        print(f"Error fetching NIFTY data: {e}")
        return pd.DataFrame()

def get_stock_data(symbol: str, period: str = "1mo") -> pd.DataFrame:
    """
    Fetch individual stock data with NSE suffix
    """
    try:
        # Add .NS suffix for NSE stocks if not present
        if not symbol.endswith('.NS') and not symbol.startswith('^'):
            symbol = f"{symbol}.NS"
        
        stock = yf.Ticker(symbol)
        data = stock.history(period=period)
        return data
    except Exception as e:
        print(f"Error fetching stock data for {symbol}: {e}")
        return pd.DataFrame()

def get_multiple_stocks_data(symbols: list, period: str = "1mo") -> dict:
    """
    Fetch data for multiple stocks
    """
    stocks_data = {}
    for symbol in symbols:
        data = get_stock_data(symbol, period)
        if not data.empty:
            stocks_data[symbol] = data
    return stocks_data

def get_top_gainers_losers() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Get top gainers and losers from NSE
    Note: This is a simplified version. In production, you'd use NSE API or scraping
    """
    try:
        # Sample NIFTY 50 stocks for demonstration
        nifty_stocks = [
            'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'HINDUNILVR.NS',
            'ICICIBANK.NS', 'KOTAKBANK.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS',
            'ASIANPAINT.NS', 'LT.NS', 'AXISBANK.NS', 'MARUTI.NS', 'SUNPHARMA.NS',
            'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'NESTLEIND.NS', 'POWERGRID.NS'
        ]
        
        gainers_data = []
        losers_data = []
        
        for stock in nifty_stocks:
            try:
                ticker = yf.Ticker(stock)
                hist = ticker.history(period="2d")
                
                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    change = current_price - prev_price
                    change_pct = (change / prev_price) * 100
                    
                    stock_data = {
                        'Symbol': stock.replace('.NS', ''),
                        'LTP': round(current_price, 2),
                        'Change': round(change, 2),
                        '% Change': round(change_pct, 2)
                    }
                    
                    if change_pct > 0:
                        gainers_data.append(stock_data)
                    else:
                        losers_data.append(stock_data)
            except:
                continue
        
        # Sort by percentage change
        gainers_df = pd.DataFrame(gainers_data).sort_values('% Change', ascending=False)
        losers_df = pd.DataFrame(losers_data).sort_values('% Change', ascending=True)
        
        return gainers_df, losers_df
        
    except Exception as e:
        print(f"Error fetching top movers: {e}")
        return pd.DataFrame(), pd.DataFrame()

def get_real_time_price(symbol: str) -> Optional[float]:
    """
    Get real-time price for a stock
    """
    try:
        if not symbol.endswith('.NS') and not symbol.startswith('^'):
            symbol = f"{symbol}.NS"
            
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="1m")
        
        if not data.empty:
            return data['Close'].iloc[-1]
        return None
    except Exception as e:
        print(f"Error fetching real-time price for {symbol}: {e}")
        return None

def calculate_technical_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate common technical indicators
    """
    try:
        df = data.copy()
        
        # Moving averages
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['EMA_12'] = df['Close'].ewm(span=12).mean()
        df['EMA_26'] = df['Close'].ewm(span=26).mean()
        
        # MACD
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        return df
        
    except Exception as e:
        print(f"Error calculating technical indicators: {e}")
        return data

def detect_breakouts(symbol: str = None, days_range: int = 7):
    """
    Detect if a stock is breaking out of its recent range
    If no symbol provided, returns breakouts for multiple NIFTY stocks
    """
    if symbol is None:
        # Get breakouts for multiple NIFTY stocks
        breakouts_list = get_nifty_breakouts(days_range)
        return {'breakouts': breakouts_list}
    
    try:
        data = get_stock_data(symbol, period="3mo")
        if data.empty:
            return {}
        
        # Get recent range
        recent_data = data.tail(days_range)
        range_high = recent_data['High'].max()
        range_low = recent_data['Low'].min()
        current_price = data['Close'].iloc[-1]
        
        # Check for breakout
        is_breakout = current_price > range_high
        volume_spike = data['Volume'].iloc[-1] / data['Volume'].rolling(20).mean().iloc[-1]
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'range_high': range_high,
            'range_low': range_low,
            'is_breakout': is_breakout,
            'volume_spike': volume_spike,
            'days_in_range': days_range
        }
        
    except Exception as e:
        print(f"Error detecting breakout for {symbol}: {e}")
        return {}

def get_nifty_breakouts(days_range: int = 7):
    """
    Get breakout analysis for multiple NIFTY 50 stocks
    """
    nifty_stocks = [
        'RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK', 'KOTAKBANK', 'HDFCBANK',
        'ITC', 'LT', 'SBIN', 'BHARTIARTL', 'ASIANPAINT', 'MARUTI', 'NESTLEIND',
        'ULTRACEMCO', 'AXISBANK', 'M&M', 'SUNPHARMA', 'TITAN', 'WIPRO'
    ]
    
    breakouts = []
    
    for stock in nifty_stocks:
        try:
            data = get_stock_data(stock, period="2mo")
            if data.empty:
                continue
                
            # Get recent range (6-8 days)
            recent_data = data.tail(days_range)
            range_high = recent_data['High'].max()
            range_low = recent_data['Low'].min()
            current_price = data['Close'].iloc[-1]
            range_size = range_high - range_low
            
            # Check for breakout
            is_breakout = current_price > range_high
            volume_ratio = 1.0
            
            try:
                volume_ratio = data['Volume'].iloc[-1] / data['Volume'].rolling(10).mean().iloc[-1]
            except:
                volume_ratio = 1.0
            
            # Calculate breakout strength
            strength = 0
            if is_breakout:
                price_above_range = (current_price - range_high) / range_high * 100
                strength = min(price_above_range * volume_ratio, 10)
            
            # Only include if it's a actual breakout or strong volume
            if is_breakout or volume_ratio > 1.5:
                breakouts.append({
                    'symbol': stock,
                    'current_price': current_price,
                    'breakout_range': days_range,
                    'strength': strength,
                    'volume_ratio': volume_ratio,
                    'is_breakout': is_breakout,
                    'range_high': range_high,
                    'range_low': range_low
                })
                
        except Exception as e:
            continue
    
    # Sort by strength and return top breakouts
    breakouts.sort(key=lambda x: x['strength'], reverse=True)
    return breakouts[:15]  # Return top 15

def get_market_status() -> dict:
    """
    Get current market status (open/closed)
    """
    try:
        now = datetime.now()
        
        # NSE trading hours: 9:15 AM to 3:30 PM IST (Monday to Friday)
        market_open_time = now.replace(hour=9, minute=15, second=0)
        market_close_time = now.replace(hour=15, minute=30, second=0)
        
        is_weekday = now.weekday() < 5  # Monday is 0, Friday is 4
        is_trading_hours = market_open_time <= now <= market_close_time
        
        market_open = is_weekday and is_trading_hours
        
        return {
            'is_open': market_open,
            'current_time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'next_open': 'Next trading day 9:15 AM' if not market_open else 'Market is open',
            'market_session': 'Regular' if market_open else 'Closed'
        }
        
    except Exception as e:
        print(f"Error getting market status: {e}")
        return {'is_open': False, 'error': str(e)}
