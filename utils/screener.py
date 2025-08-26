import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import concurrent.futures
from .fundamentals import get_fundamental_data, calculate_financial_score
from .market_data import calculate_technical_indicators, get_stock_data

# Common Indian stock universe
INDIAN_STOCKS = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR', 'ICICIBANK', 'KOTAKBANK',
    'SBIN', 'BHARTIARTL', 'ITC', 'ASIANPAINT', 'LT', 'AXISBANK', 'MARUTI', 'SUNPHARMA',
    'TITAN', 'ULTRACEMCO', 'WIPRO', 'NESTLEIND', 'POWERGRID', 'TATAMOTORS', 'ONGC',
    'NTPC', 'TECHM', 'HCLTECH', 'DIVISLAB', 'CIPLA', 'DRREDDY', 'BAJFINANCE',
    'BAJAJFINSV', 'COALINDIA', 'IOC', 'GRASIM', 'JSWSTEEL', 'HINDALCO', 'INDUSINDBK',
    'ADANIPORTS', 'BRITANNIA', 'EICHERMOT', 'HEROMOTOCO', 'SHREECEM', 'BAJAJ-AUTO',
    'TATASTEEL', 'BPCL', 'APOLLOHOSP', 'HDFCLIFE', 'SBILIFE', 'ICICIPRULI',
    'PIDILITIND', 'GODREJCP', 'MARICO', 'DABUR'
]

class StockScreener:
    def __init__(self):
        self.stock_universe = INDIAN_STOCKS
        self.cache = {}
        self.cache_expiry = timedelta(hours=1)
        
    def _get_stock_data_cached(self, symbol: str) -> Optional[Dict]:
        """Get stock data with caching"""
        cache_key = f"{symbol}_data"
        current_time = datetime.now()
        
        # Check if data is in cache and not expired
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if current_time - timestamp < self.cache_expiry:
                return cached_data
        
        # Fetch fresh data
        try:
            fundamental_data = get_fundamental_data(symbol)
            price_data = get_stock_data(symbol, period="3mo")
            
            if fundamental_data and not price_data.empty:
                # Add technical indicators
                technical_data = calculate_technical_indicators(price_data)
                
                combined_data = {
                    'symbol': symbol,
                    'fundamental': fundamental_data,
                    'technical': technical_data,
                    'current_price': technical_data['Close'].iloc[-1] if not technical_data.empty else 0
                }
                
                # Cache the data
                self.cache[cache_key] = (combined_data, current_time)
                return combined_data
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
        
        return None
    
    def rsi_screen(self, criteria: Dict) -> List[Dict]:
        """Screen stocks based on RSI criteria"""
        try:
            screened_stocks = []
            
            # RSI criteria
            rsi_low = criteria.get('rsi_low', 30)
            rsi_high = criteria.get('rsi_high', 70)
            rsi_condition = criteria.get('rsi_condition', 'oversold')  # oversold, overbought, or range
            
            for symbol in self.stock_universe:
                stock_data = self._get_stock_data_cached(symbol)
                if not stock_data:
                    continue
                
                technical_data = stock_data.get('technical', pd.DataFrame())
                if technical_data.empty or 'RSI' not in technical_data.columns:
                    continue
                
                current_rsi = technical_data['RSI'].iloc[-1]
                current_price = technical_data['Close'].iloc[-1]
                
                # Check RSI condition
                match_condition = False
                if rsi_condition == 'oversold' and current_rsi <= rsi_low:
                    match_condition = True
                elif rsi_condition == 'overbought' and current_rsi >= rsi_high:
                    match_condition = True
                elif rsi_condition == 'range' and rsi_low <= current_rsi <= rsi_high:
                    match_condition = True
                
                if match_condition:
                    screened_stocks.append({
                        'symbol': symbol,
                        'current_price': current_price,
                        'rsi': round(current_rsi, 2),
                        'signal': rsi_condition,
                        'score': 100 - abs(current_rsi - 50)  # Higher score for extreme values
                    })
            
            # Sort by RSI value based on condition
            if rsi_condition == 'oversold':
                screened_stocks.sort(key=lambda x: x['rsi'])
            elif rsi_condition == 'overbought':
                screened_stocks.sort(key=lambda x: x['rsi'], reverse=True)
            else:
                screened_stocks.sort(key=lambda x: x['score'], reverse=True)
            
            return screened_stocks[:20]  # Return top 20 matches
            
        except Exception as e:
            print(f"Error in RSI screening: {e}")
            return []
    
    def supertrend_screen(self, criteria: Dict) -> List[Dict]:
        """Screen stocks based on Supertrend indicator"""
        try:
            screened_stocks = []
            
            # Supertrend criteria
            signal_type = criteria.get('signal_type', 'buy')  # buy, sell
            
            for symbol in self.stock_universe:
                stock_data = self._get_stock_data_cached(symbol)
                if not stock_data:
                    continue
                
                technical_data = stock_data.get('technical', pd.DataFrame())
                if technical_data.empty:
                    continue
                
                # Calculate Supertrend
                supertrend_data = self._calculate_supertrend(technical_data)
                if supertrend_data.empty:
                    continue
                
                current_price = technical_data['Close'].iloc[-1]
                current_supertrend = supertrend_data['Supertrend'].iloc[-1]
                current_signal = supertrend_data['Signal'].iloc[-1]
                
                # Check signal condition
                match_condition = False
                if signal_type == 'buy' and current_signal == 'Buy':
                    match_condition = True
                elif signal_type == 'sell' and current_signal == 'Sell':
                    match_condition = True
                
                if match_condition:
                    # Calculate strength based on price distance from supertrend
                    distance_pct = abs((current_price - current_supertrend) / current_supertrend) * 100
                    
                    screened_stocks.append({
                        'symbol': symbol,
                        'current_price': current_price,
                        'supertrend': round(current_supertrend, 2),
                        'signal': current_signal,
                        'distance_pct': round(distance_pct, 2),
                        'score': 100 - distance_pct  # Higher score for closer to supertrend
                    })
            
            # Sort by score (best signals first)
            screened_stocks.sort(key=lambda x: x['score'], reverse=True)
            return screened_stocks[:15]
            
        except Exception as e:
            print(f"Error in Supertrend screening: {e}")
            return []
    
    def quarterly_earnings_screen(self, criteria: Dict) -> List[Dict]:
        """Screen stocks based on quarterly earnings performance"""
        try:
            screened_stocks = []
            
            # Earnings criteria
            min_growth = criteria.get('min_growth', 10)  # Minimum earnings growth %
            min_revenue_growth = criteria.get('min_revenue_growth', 5)
            max_pe = criteria.get('max_pe', 25)
            
            for symbol in self.stock_universe:
                stock_data = self._get_stock_data_cached(symbol)
                if not stock_data:
                    continue
                
                fundamental_data = stock_data.get('fundamental', {})
                if not fundamental_data:
                    continue
                
                current_price = stock_data.get('current_price', 0)
                
                # Extract key metrics (simplified)
                pe_ratio = fundamental_data.get('pe_ratio', 0)
                profit_growth = fundamental_data.get('profit_growth', 0)
                revenue_growth = fundamental_data.get('revenue_growth', 0)
                roe = fundamental_data.get('roe', 0)
                
                # Apply filters
                if (pe_ratio > 0 and pe_ratio <= max_pe and 
                    profit_growth >= min_growth and 
                    revenue_growth >= min_revenue_growth):
                    
                    # Calculate composite score
                    growth_score = (profit_growth + revenue_growth) / 2
                    efficiency_score = min(roe / 15 * 25, 25)  # ROE normalized to 25 points
                    valuation_score = max(0, 25 - (pe_ratio / max_pe * 25))  # Lower PE = higher score
                    
                    total_score = growth_score + efficiency_score + valuation_score
                    
                    screened_stocks.append({
                        'symbol': symbol,
                        'current_price': current_price,
                        'pe_ratio': round(pe_ratio, 2),
                        'profit_growth': round(profit_growth, 1),
                        'revenue_growth': round(revenue_growth, 1),
                        'roe': round(roe, 1),
                        'score': round(total_score, 1)
                    })
            
            # Sort by total score
            screened_stocks.sort(key=lambda x: x['score'], reverse=True)
            return screened_stocks[:20]
            
        except Exception as e:
            print(f"Error in quarterly earnings screening: {e}")
            return []
    
    def _calculate_supertrend(self, data: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
        """Calculate Supertrend indicator"""
        try:
            if data.empty or len(data) < period:
                return pd.DataFrame()
            
            # Calculate ATR (Average True Range)
            high = data['High']
            low = data['Low']
            close = data['Close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            
            tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
            atr = tr.rolling(window=period).mean()
            
            # Calculate basic upper and lower bands
            hl_avg = (high + low) / 2
            upper_band = hl_avg + (multiplier * atr)
            lower_band = hl_avg - (multiplier * atr)
            
            # Calculate final upper and lower bands
            final_upper = upper_band.copy()
            final_lower = lower_band.copy()
            
            for i in range(1, len(data)):
                if upper_band.iloc[i] < final_upper.iloc[i-1] or close.iloc[i-1] > final_upper.iloc[i-1]:
                    final_upper.iloc[i] = upper_band.iloc[i]
                else:
                    final_upper.iloc[i] = final_upper.iloc[i-1]
                
                if lower_band.iloc[i] > final_lower.iloc[i-1] or close.iloc[i-1] < final_lower.iloc[i-1]:
                    final_lower.iloc[i] = lower_band.iloc[i]
                else:
                    final_lower.iloc[i] = final_lower.iloc[i-1]
            
            # Determine Supertrend and signals
            supertrend = pd.Series(index=data.index, dtype=float)
            signal = pd.Series(index=data.index, dtype=str)
            
            # Initial values
            supertrend.iloc[0] = final_lower.iloc[0] if close.iloc[0] > final_upper.iloc[0] else final_upper.iloc[0]
            signal.iloc[0] = 'Buy' if close.iloc[0] > final_upper.iloc[0] else 'Sell'
            
            for i in range(1, len(data)):
                if close.iloc[i] > final_upper.iloc[i]:
                    supertrend.iloc[i] = final_lower.iloc[i]
                    signal.iloc[i] = 'Buy'
                elif close.iloc[i] < final_lower.iloc[i]:
                    supertrend.iloc[i] = final_upper.iloc[i]
                    signal.iloc[i] = 'Sell'
                else:
                    supertrend.iloc[i] = supertrend.iloc[i-1]
                    signal.iloc[i] = signal.iloc[i-1]
            
            result = pd.DataFrame({
                'Supertrend': supertrend,
                'Signal': signal,
                'Upper_Band': final_upper,
                'Lower_Band': final_lower
            }, index=data.index)
            
            return result
            
        except Exception as e:
            print(f"Error calculating Supertrend: {e}")
            return pd.DataFrame()
    
    def fundamental_screen(self, criteria: Dict) -> List[Dict]:
        """Screen stocks based on fundamental criteria"""
        try:
            screened_stocks = []
            
            # Default criteria
            default_criteria = {
                'min_market_cap': 0,
                'max_market_cap': float('inf'),
                'min_pe_ratio': 0,
                'max_pe_ratio': 50,
                'min_roe': 0,
                'max_debt_to_equity': 2.0,
                'min_profit_margin': 0,
                'min_revenue_growth': -0.5,
                'dividend_yield': False,
                'sectors': None  # List of sectors or None for all
            }
            
            # Update with user criteria
            screen_criteria = {**default_criteria, **criteria}
            
            # Screen stocks
            for symbol in self.stock_universe:
                stock_data = self._get_stock_data_cached(symbol)
                
                if not stock_data:
                    continue
                
                fundamental = stock_data['fundamental']
                
                # Extract values for screening
                basic_info = fundamental.get('basic_info', {})
                valuation = fundamental.get('valuation_ratios', {})
                profitability = fundamental.get('profitability_ratios', {})
                financial_health = fundamental.get('financial_health', {})
                growth = fundamental.get('growth_metrics', {})
                dividend = fundamental.get('dividend_info', {})
                
                # Market cap filter
                market_cap = basic_info.get('market_cap', 0)
                if not (screen_criteria['min_market_cap'] <= market_cap <= screen_criteria['max_market_cap']):
                    continue
                
                # PE ratio filter
                pe_ratio = valuation.get('pe_ratio')
                if pe_ratio and not (screen_criteria['min_pe_ratio'] <= pe_ratio <= screen_criteria['max_pe_ratio']):
                    continue
                
                # ROE filter
                roe = profitability.get('roe')
                if roe and roe < screen_criteria['min_roe']:
                    continue
                
                # Debt to equity filter
                debt_to_equity = financial_health.get('debt_to_equity')
                if debt_to_equity and debt_to_equity > screen_criteria['max_debt_to_equity']:
                    continue
                
                # Profit margin filter
                profit_margin = profitability.get('profit_margin')
                if profit_margin and profit_margin < screen_criteria['min_profit_margin']:
                    continue
                
                # Revenue growth filter
                revenue_growth = growth.get('revenue_growth')
                if revenue_growth and revenue_growth < screen_criteria['min_revenue_growth']:
                    continue
                
                # Dividend yield filter
                if screen_criteria['dividend_yield']:
                    div_yield = dividend.get('dividend_yield', 0)
                    if not div_yield or div_yield <= 0:
                        continue
                
                # Sector filter
                if screen_criteria['sectors']:
                    sector = basic_info.get('sector', '')
                    if sector not in screen_criteria['sectors']:
                        continue
                
                # Calculate financial score
                financial_score = calculate_financial_score(fundamental)
                
                # Add to results
                screened_stocks.append({
                    'symbol': symbol,
                    'company_name': basic_info.get('company_name', 'N/A'),
                    'sector': basic_info.get('sector', 'N/A'),
                    'current_price': stock_data['current_price'],
                    'market_cap': market_cap,
                    'pe_ratio': pe_ratio,
                    'roe': roe,
                    'debt_to_equity': debt_to_equity,
                    'profit_margin': profit_margin,
                    'revenue_growth': revenue_growth,
                    'dividend_yield': dividend.get('dividend_yield'),
                    'financial_score': financial_score.get('percentage', 0),
                    'financial_rating': financial_score.get('rating', 'N/A')
                })
            
            # Sort by financial score
            screened_stocks.sort(key=lambda x: x['financial_score'], reverse=True)
            return screened_stocks
            
        except Exception as e:
            print(f"Error in fundamental screening: {e}")
            return []
    
    def technical_screen(self, criteria: Dict) -> List[Dict]:
        """Screen stocks based on technical criteria"""
        try:
            screened_stocks = []
            
            # Default technical criteria
            default_criteria = {
                'rsi_min': 30,
                'rsi_max': 70,
                'price_above_sma20': False,
                'price_above_sma50': False,
                'macd_bullish': False,
                'volume_spike': False,
                'breakout_pattern': False,
                'min_volume': 0
            }
            
            screen_criteria = {**default_criteria, **criteria}
            
            for symbol in self.stock_universe:
                stock_data = self._get_stock_data_cached(symbol)
                
                if not stock_data:
                    continue
                
                technical = stock_data['technical']
                
                if technical.empty:
                    continue
                
                # Get latest values
                current_price = technical['Close'].iloc[-1]
                rsi = technical['RSI'].iloc[-1] if 'RSI' in technical.columns else None
                sma20 = technical['SMA_20'].iloc[-1] if 'SMA_20' in technical.columns else None
                sma50 = technical['SMA_50'].iloc[-1] if 'SMA_50' in technical.columns else None
                macd = technical['MACD'].iloc[-1] if 'MACD' in technical.columns else None
                macd_signal = technical['MACD_Signal'].iloc[-1] if 'MACD_Signal' in technical.columns else None
                volume = technical['Volume'].iloc[-1]
                avg_volume = technical['Volume'].rolling(20).mean().iloc[-1]
                
                # RSI filter
                if rsi and not (screen_criteria['rsi_min'] <= rsi <= screen_criteria['rsi_max']):
                    continue
                
                # Price above SMA filters
                if screen_criteria['price_above_sma20'] and sma20 and current_price <= sma20:
                    continue
                
                if screen_criteria['price_above_sma50'] and sma50 and current_price <= sma50:
                    continue
                
                # MACD bullish filter
                if screen_criteria['macd_bullish'] and macd and macd_signal:
                    if macd <= macd_signal:
                        continue
                
                # Volume spike filter
                if screen_criteria['volume_spike'] and avg_volume:
                    volume_ratio = volume / avg_volume
                    if volume_ratio < 1.5:  # At least 1.5x average volume
                        continue
                
                # Minimum volume filter
                if volume < screen_criteria['min_volume']:
                    continue
                
                # Breakout pattern detection
                breakout_score = 0
                if screen_criteria['breakout_pattern']:
                    # Simple breakout detection
                    high_20 = technical['High'].rolling(20).max().iloc[-2]  # Previous 20 days high
                    if current_price > high_20:
                        breakout_score = 1
                    else:
                        continue
                
                # Calculate technical score
                technical_score = 0
                total_indicators = 0
                
                if rsi:
                    if 40 <= rsi <= 60:
                        technical_score += 20
                    elif 30 <= rsi <= 70:
                        technical_score += 15
                    total_indicators += 20
                
                if sma20 and current_price > sma20:
                    technical_score += 15
                total_indicators += 15
                
                if sma50 and current_price > sma50:
                    technical_score += 15
                total_indicators += 15
                
                if macd and macd_signal and macd > macd_signal:
                    technical_score += 20
                total_indicators += 20
                
                if avg_volume and volume / avg_volume > 1.2:
                    technical_score += 10
                total_indicators += 10
                
                technical_score_pct = (technical_score / total_indicators * 100) if total_indicators > 0 else 0
                
                screened_stocks.append({
                    'symbol': symbol,
                    'current_price': current_price,
                    'rsi': rsi,
                    'price_vs_sma20': ((current_price - sma20) / sma20 * 100) if sma20 else None,
                    'price_vs_sma50': ((current_price - sma50) / sma50 * 100) if sma50 else None,
                    'macd_signal': 'Bullish' if macd and macd_signal and macd > macd_signal else 'Bearish',
                    'volume_ratio': volume / avg_volume if avg_volume else 1,
                    'breakout_score': breakout_score,
                    'technical_score': technical_score_pct
                })
            
            # Sort by technical score
            screened_stocks.sort(key=lambda x: x['technical_score'], reverse=True)
            return screened_stocks
            
        except Exception as e:
            print(f"Error in technical screening: {e}")
            return []
    
    def combined_screen(self, fundamental_criteria: Dict, technical_criteria: Dict, weights: Dict = None) -> List[Dict]:
        """Combine fundamental and technical screening with weights"""
        try:
            if weights is None:
                weights = {'fundamental': 0.6, 'technical': 0.4}
            
            # Get both screens
            fundamental_results = self.fundamental_screen(fundamental_criteria)
            technical_results = self.technical_screen(technical_criteria)
            
            # Create lookup for technical scores
            technical_lookup = {result['symbol']: result for result in technical_results}
            
            combined_results = []
            
            for fund_result in fundamental_results:
                symbol = fund_result['symbol']
                tech_result = technical_lookup.get(symbol, {})
                
                # Calculate combined score
                fund_score = fund_result.get('financial_score', 0)
                tech_score = tech_result.get('technical_score', 0)
                
                combined_score = (fund_score * weights['fundamental'] + 
                                tech_score * weights['technical'])
                
                # Combine data
                combined_data = {**fund_result, **tech_result}
                combined_data['combined_score'] = combined_score
                
                combined_results.append(combined_data)
            
            # Sort by combined score
            combined_results.sort(key=lambda x: x['combined_score'], reverse=True)
            return combined_results
            
        except Exception as e:
            print(f"Error in combined screening: {e}")
            return []
    
    def momentum_screen(self) -> List[Dict]:
        """Screen for momentum stocks"""
        momentum_criteria = {
            'price_above_sma20': True,
            'price_above_sma50': True,
            'volume_spike': True,
            'rsi_min': 50,
            'rsi_max': 80,
            'macd_bullish': True
        }
        
        return self.technical_screen(momentum_criteria)
    
    def value_screen(self) -> List[Dict]:
        """Screen for value stocks"""
        value_criteria = {
            'max_pe_ratio': 20,
            'min_roe': 0.12,
            'max_debt_to_equity': 1.0,
            'min_profit_margin': 0.05,
            'dividend_yield': True
        }
        
        return self.fundamental_screen(value_criteria)
    
    def growth_screen(self) -> List[Dict]:
        """Screen for growth stocks"""
        growth_criteria = {
            'min_revenue_growth': 0.15,
            'min_roe': 0.15,
            'min_profit_margin': 0.10,
            'max_pe_ratio': 40
        }
        
        return self.fundamental_screen(growth_criteria)
    
    def dividend_screen(self) -> List[Dict]:
        """Screen for dividend-paying stocks"""
        dividend_criteria = {
            'dividend_yield': True,
            'min_roe': 0.10,
            'max_debt_to_equity': 1.5,
            'min_profit_margin': 0.05
        }
        
        results = self.fundamental_screen(dividend_criteria)
        
        # Sort by dividend yield
        results.sort(key=lambda x: x.get('dividend_yield', 0), reverse=True)
        return results
    
    def quality_screen(self) -> List[Dict]:
        """Screen for quality stocks"""
        quality_criteria = {
            'min_roe': 0.15,
            'min_profit_margin': 0.10,
            'max_debt_to_equity': 0.5,
            'min_revenue_growth': 0.05
        }
        
        return self.fundamental_screen(quality_criteria)
    
    def get_sector_leaders(self, sector: str) -> List[Dict]:
        """Get leading stocks in a specific sector"""
        sector_criteria = {
            'sectors': [sector],
            'min_market_cap': 1000000000,  # 1 billion minimum
            'min_roe': 0.10
        }
        
        results = self.fundamental_screen(sector_criteria)
        
        # Sort by market cap (largest first)
        results.sort(key=lambda x: x.get('market_cap', 0), reverse=True)
        return results[:10]  # Top 10 in sector
    
    def custom_screen(self, user_criteria: Dict) -> List[Dict]:
        """Allow users to create custom screens"""
        try:
            # Separate fundamental and technical criteria
            fundamental_keys = [
                'min_market_cap', 'max_market_cap', 'min_pe_ratio', 'max_pe_ratio',
                'min_roe', 'max_debt_to_equity', 'min_profit_margin', 'min_revenue_growth',
                'dividend_yield', 'sectors'
            ]
            
            technical_keys = [
                'rsi_min', 'rsi_max', 'price_above_sma20', 'price_above_sma50',
                'macd_bullish', 'volume_spike', 'breakout_pattern', 'min_volume'
            ]
            
            fundamental_criteria = {k: v for k, v in user_criteria.items() if k in fundamental_keys}
            technical_criteria = {k: v for k, v in user_criteria.items() if k in technical_keys}
            
            # If both types of criteria, use combined screen
            if fundamental_criteria and technical_criteria:
                weights = user_criteria.get('weights', {'fundamental': 0.6, 'technical': 0.4})
                return self.combined_screen(fundamental_criteria, technical_criteria, weights)
            elif fundamental_criteria:
                return self.fundamental_screen(fundamental_criteria)
            elif technical_criteria:
                return self.technical_screen(technical_criteria)
            else:
                # Return top stocks by financial score if no criteria
                return self.fundamental_screen({})[:20]
            
        except Exception as e:
            print(f"Error in custom screening: {e}")
            return []
