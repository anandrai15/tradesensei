import json
import os
import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import requests
from .market_data import get_nifty_data, get_stock_data, get_top_gainers_losers

def get_market_sentiment_analysis() -> Optional[Dict]:
    """
    Generate statistical market sentiment analysis using current market data
    Free and open-source alternative to paid AI APIs
    """
    try:
        # Fetch current market data
        nifty_data = get_nifty_data(period="1mo")
        gainers, losers = get_top_gainers_losers()
        
        if nifty_data.empty:
            return None
        
        # Prepare market context
        current_price = nifty_data['Close'].iloc[-1]
        prev_price = nifty_data['Close'].iloc[-2] if len(nifty_data) > 1 else current_price
        change_pct = ((current_price - prev_price) / prev_price) * 100 if prev_price != 0 else 0
        
        # Calculate technical indicators
        returns = nifty_data['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252) * 100 if len(returns) > 0 else 0
        
        # Volume analysis
        if 'Volume' in nifty_data.columns and len(nifty_data) >= 20:
            avg_volume = nifty_data['Volume'].rolling(20).mean().iloc[-1]
            current_volume = nifty_data['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        else:
            volume_ratio = 1
        
        # Moving averages for trend analysis
        if len(nifty_data) >= 20:
            ma_20 = nifty_data['Close'].rolling(20).mean().iloc[-1]
            trend_strength = (current_price - ma_20) / ma_20 * 100
        else:
            trend_strength = change_pct
            
        # Sentiment scoring algorithm (rule-based)
        sentiment_score = 0
        sentiment_score += min(max(change_pct / 2, -1), 1)  # Price change component
        sentiment_score += min(max((len(gainers) - len(losers)) / 100, -0.5), 0.5)  # Breadth component
        sentiment_score += min(max((volume_ratio - 1) * 0.3, -0.3), 0.3)  # Volume component
        sentiment_score += min(max(trend_strength / 5, -0.4), 0.4)  # Trend component
        
        # Determine sentiment
        if sentiment_score > 0.3:
            sentiment = "bullish"
            direction = "upward"
        elif sentiment_score < -0.3:
            sentiment = "bearish"
            direction = "downward"
        else:
            sentiment = "neutral"
            direction = "sideways"
            
        # Calculate probability based on trend strength and volatility
        probability = min(0.9, max(0.1, 0.5 + abs(sentiment_score) * 0.8))
        
        # Duration based on volatility and momentum
        if volatility > 25:
            duration = "1-3 days"
        elif volatility > 15:
            duration = "1-2 weeks"
        else:
            duration = "1 month"
            
        # Risk level assessment
        if volatility > 30:
            risk_level = "high"
        elif volatility > 20:
            risk_level = "medium"
        else:
            risk_level = "low"
            
        # Key factors identification
        key_factors = []
        if abs(change_pct) > 1:
            key_factors.append(f"Strong price movement ({change_pct:+.1f}%)")
        if volume_ratio > 1.5:
            key_factors.append("High trading volume")
        elif volume_ratio < 0.7:
            key_factors.append("Low trading volume")
        if volatility > 25:
            key_factors.append("High market volatility")
        if len(gainers) > len(losers) * 2:
            key_factors.append("Broad market strength")
        elif len(losers) > len(gainers) * 2:
            key_factors.append("Broad market weakness")
            
        analysis_text = f"Market shows {sentiment} sentiment with {probability:.1%} confidence. " \
                       f"Current NIFTY at {current_price:.2f} ({change_pct:+.2f}%). " \
                       f"Volatility at {volatility:.1f}% indicates {risk_level} risk environment."
        
        # Return statistical analysis result (free alternative to OpenAI)
        result = {
            "analysis": analysis_text,
            "sentiment": sentiment,
            "probability": round(probability, 2),
            "direction": direction,
            "duration": duration,
            "risk_level": risk_level,
            "key_factors": key_factors if key_factors else ["Standard market conditions"]
        }
        
        return result
        
    except Exception as e:
        print(f"Error in AI market sentiment analysis: {e}")
        return None

def analyze_stock_probability(symbol: str, timeframe: str = "1 week") -> Optional[Dict]:
    """
    Analyze probability of stock price movement using statistical methods
    Free and open-source alternative to paid AI APIs
    """
    try:
        # Fetch stock data
        stock_data = get_stock_data(symbol, period="3mo")
        if stock_data.empty:
            return None
        
        # Calculate technical indicators
        current_price = stock_data['Close'].iloc[-1]
        
        # Ensure we have enough data
        if len(stock_data) < 50:
            return None
            
        sma_20 = stock_data['Close'].rolling(20).mean().iloc[-1]
        sma_50 = stock_data['Close'].rolling(50).mean().iloc[-1]
        
        # Calculate RSI
        delta = stock_data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs.iloc[-1])) if rs.iloc[-1] > 0 else 50
        
        # Volume analysis
        if 'Volume' in stock_data.columns:
            avg_volume = stock_data['Volume'].rolling(20).mean().iloc[-1]
            current_volume = stock_data['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        else:
            volume_ratio = 1
        
        # Statistical probability calculation
        returns = stock_data['Close'].pct_change().dropna()
        mean_return = returns.mean()
        std_return = returns.std()
        
        # Price momentum indicators
        price_momentum = (current_price - sma_20) / sma_20 * 100
        trend_strength = (sma_20 - sma_50) / sma_50 * 100
        
        # Probability scoring system
        upward_signals = 0
        downward_signals = 0
        
        # RSI signals
        if rsi < 30:
            upward_signals += 2  # Oversold
        elif rsi > 70:
            downward_signals += 2  # Overbought
        elif 45 <= rsi <= 55:
            upward_signals += 1  # Neutral momentum
            
        # Moving average signals
        if current_price > sma_20 > sma_50:
            upward_signals += 2  # Strong uptrend
        elif current_price < sma_20 < sma_50:
            downward_signals += 2  # Strong downtrend
        elif current_price > sma_20:
            upward_signals += 1  # Price above short MA
            
        # Volume confirmation
        if volume_ratio > 1.2:
            if price_momentum > 0:
                upward_signals += 1
            else:
                downward_signals += 1
                
        # Statistical momentum
        if mean_return > 0:
            upward_signals += 1
        else:
            downward_signals += 1
            
        # Calculate probabilities
        total_signals = upward_signals + downward_signals
        if total_signals > 0:
            upward_prob = upward_signals / total_signals
            downward_prob = downward_signals / total_signals
        else:
            upward_prob = downward_prob = 0.5
            
        # Adjust for volatility
        volatility = std_return * np.sqrt(252) * 100
        confidence = max(0.3, min(0.9, 1 - volatility / 50))
        
        # Price range estimation
        volatility_factor = std_return * 1.96  # 95% confidence interval
        if timeframe == "1 week":
            time_factor = np.sqrt(5)  # 5 trading days
        elif timeframe == "1 month":
            time_factor = np.sqrt(20)  # 20 trading days
        else:
            time_factor = np.sqrt(5)
            
        price_range_factor = volatility_factor * time_factor
        upper_range = current_price * (1 + price_range_factor)
        lower_range = current_price * (1 - price_range_factor)
        
        # Technical signals summary
        signals = []
        if rsi < 30:
            signals.append("Oversold RSI")
        elif rsi > 70:
            signals.append("Overbought RSI")
        if current_price > sma_20:
            signals.append("Above 20-day MA")
        if sma_20 > sma_50:
            signals.append("Bullish MA crossover")
        if volume_ratio > 1.5:
            signals.append("High volume")
        elif volume_ratio < 0.7:
            signals.append("Low volume")
        
        # Recommendation logic
        if upward_prob > 0.6:
            recommendation = "buy"
        elif downward_prob > 0.6:
            recommendation = "sell"
        else:
            recommendation = "hold"
            
        # Return statistical analysis result (free alternative to OpenAI)
        result = {
            "symbol": symbol,
            "timeframe": timeframe,
            "upward_probability": round(upward_prob, 2),
            "downward_probability": round(downward_prob, 2),
            "expected_price_range": {
                "low": round(lower_range, 2),
                "high": round(upper_range, 2)
            },
            "confidence": round(confidence, 2),
            "technical_signals": signals if signals else ["Standard technical setup"],
            "recommendation": recommendation
        }
        
        return result
        
    except Exception as e:
        print(f"Error in stock probability analysis for {symbol}: {e}")
        return None

def generate_daily_market_summary() -> Optional[str]:
    """
    Generate a comprehensive daily market summary using statistical analysis
    Free and open-source alternative to paid AI APIs
    """
    try:
        # Gather market data
        nifty_data = get_nifty_data(period="5d")
        gainers, losers = get_top_gainers_losers()
        
        if nifty_data.empty:
            return None
        
        # Market metrics
        current_price = nifty_data['Close'].iloc[-1]
        prev_price = nifty_data['Close'].iloc[-2] if len(nifty_data) > 1 else current_price
        daily_change = current_price - prev_price
        daily_change_pct = (daily_change / prev_price) * 100 if prev_price != 0 else 0
        
        # Volume analysis
        if 'Volume' in nifty_data.columns and len(nifty_data) >= 5:
            current_volume = nifty_data['Volume'].iloc[-1]
            avg_volume = nifty_data['Volume'].rolling(5).mean().iloc[-2]
            volume_change = ((current_volume - avg_volume) / avg_volume) * 100 if avg_volume > 0 else 0
        else:
            volume_change = 0
        
        # Top performers
        top_gainers = gainers.head(3)['Symbol'].tolist() if not gainers.empty else []
        top_losers = losers.head(3)['Symbol'].tolist() if not losers.empty else []
        
        # Market analysis (rule-based)
        market_direction = "bullish" if daily_change_pct > 1 else "bearish" if daily_change_pct < -1 else "neutral"
        volume_assessment = "high" if volume_change > 20 else "low" if volume_change < -20 else "average"
        breadth_ratio = len(gainers) / (len(gainers) + len(losers)) if (len(gainers) + len(losers)) > 0 else 0.5
        market_breadth = "positive" if breadth_ratio > 0.6 else "negative" if breadth_ratio < 0.4 else "mixed"
        
        # Generate summary
        summary = f"""Daily Market Summary for {datetime.now().strftime('%Y-%m-%d')}:

MARKET OVERVIEW:
The NIFTY 50 closed at {current_price:.2f}, {daily_change:+.2f} points ({daily_change_pct:+.2f}%). 
Market sentiment appears {market_direction} with {volume_assessment} trading volume ({volume_change:+.1f}% vs 5-day average).

MARKET BREADTH:
Market breadth was {market_breadth} with {len(gainers)} advancing stocks and {len(losers)} declining stocks.
This indicates {'strong buying interest' if breadth_ratio > 0.6 else 'selling pressure' if breadth_ratio < 0.4 else 'mixed sentiment'} across the market.

TOP PERFORMERS:
Leading gainers: {', '.join(top_gainers) if top_gainers else 'No significant gainers'}
Major decliners: {', '.join(top_losers) if top_losers else 'No significant losers'}

TECHNICAL OUTLOOK:
{'Positive momentum suggests continued uptrend if sustained above current levels.' if daily_change_pct > 0 else 'Weakness observed, watch for support levels and potential reversal signals.' if daily_change_pct < -1 else 'Sideways movement indicates consolidation phase.'}

TRADING RECOMMENDATIONS:
{'Focus on momentum stocks with strong volume confirmation.' if market_direction == 'bullish' else 'Exercise caution, consider defensive positions and strict stop-losses.' if market_direction == 'bearish' else 'Range-bound trading approach recommended with defined entry/exit levels.'}

KEY LEVELS TO WATCH:
Support: {current_price * 0.98:.2f} | Resistance: {current_price * 1.02:.2f}

*This analysis is generated using statistical methods and market data. Please conduct your own research before making investment decisions.*"""
        
        return summary
        
    except Exception as e:
        print(f"Error generating daily market summary: {e}")
        return None

def analyze_portfolio_risk(portfolio: List[Dict]) -> Optional[Dict]:
    """
    Analyze portfolio risk using statistical methods
    Free and open-source alternative to paid AI APIs
    """
    try:
        if not portfolio:
            return None
        
        total_value = 0
        sector_values = {}
        stock_count = len(portfolio)
        
        # Calculate portfolio composition
        for holding in portfolio:
            symbol = holding.get('symbol', '')
            quantity = holding.get('quantity', 0)
            price = holding.get('current_price', 0)
            value = quantity * price
            total_value += value
            
            # Basic sector classification (simplified)
            sector = "other"  # Default
            if any(bank in symbol.upper() for bank in ['HDFC', 'ICICI', 'SBI', 'AXIS', 'KOTAK']):
                sector = "banking"
            elif any(tech in symbol.upper() for tech in ['TCS', 'INFY', 'WIPRO', 'HCLT', 'TECHM']):
                sector = "technology"
            elif any(pharma in symbol.upper() for pharma in ['DRREDDY', 'CIPLA', 'SUNPHARMA', 'BIOCON']):
                sector = "pharma"
            elif any(fmcg in symbol.upper() for fmcg in ['HINDUNILVR', 'ITC', 'NESTLIND', 'BRITANNIA']):
                sector = "fmcg"
            
            sector_values[sector] = sector_values.get(sector, 0) + value
        
        # Calculate sector concentration percentages
        sector_concentration = {}
        for sector, value in sector_values.items():
            sector_concentration[sector] = round((value / total_value) * 100, 1) if total_value > 0 else 0
        
        # Diversification score (higher is better)
        # Based on number of stocks and sector distribution
        diversification_score = min(10, (stock_count / 2) + (len(sector_values) / 2))
        diversification_score = max(1, diversification_score)  # Minimum 1
        
        # Risk rating calculation
        # Higher concentration = higher risk
        max_sector_concentration = max(sector_concentration.values()) if sector_concentration else 100
        concentration_risk = min(5, max_sector_concentration / 20)  # 0-5 scale
        
        # Portfolio size risk
        size_risk = max(0, 3 - stock_count / 5)  # 0-3 scale, lower for larger portfolios
        
        risk_rating = min(10, max(1, int(concentration_risk + size_risk + 2)))  # 1-10 scale
        
        # Risk factors identification
        risk_factors = []
        if max_sector_concentration > 50:
            risk_factors.append(f"High sector concentration ({max_sector_concentration:.1f}% in single sector)")
        if stock_count < 5:
            risk_factors.append("Low diversification (fewer than 5 stocks)")
        if stock_count < 3:
            risk_factors.append("Very high concentration risk")
        if len(sector_values) < 3:
            risk_factors.append("Limited sector diversification")
            
        # Recommendations
        recommendations = []
        if max_sector_concentration > 40:
            recommendations.append("Reduce sector concentration by diversifying across industries")
        if stock_count < 10:
            recommendations.append("Consider adding more stocks to improve diversification")
        if "banking" in sector_concentration and sector_concentration["banking"] > 30:
            recommendations.append("Consider reducing banking sector exposure")
        if len(sector_values) < 4:
            recommendations.append("Add stocks from different sectors (pharma, FMCG, auto, etc.)")
        if not recommendations:
            recommendations.append("Portfolio shows reasonable diversification")
            
        result = {
            "diversification_score": round(diversification_score, 1),
            "sector_concentration": sector_concentration,
            "risk_rating": risk_rating,
            "risk_factors": risk_factors if risk_factors else ["Standard portfolio risk"],
            "recommendations": recommendations,
            "total_stocks": stock_count,
            "total_value": total_value
        }
        
        return result
        
    except Exception as e:
        print(f"Error in portfolio risk analysis: {e}")
        return None

def get_ai_stock_recommendations(criteria: Dict) -> Optional[List[Dict]]:
    """
    Get stock recommendations based on criteria using rule-based system
    Free and open-source alternative to paid AI APIs
    """
    try:
        market_cap = criteria.get('market_cap', 'large')
        sector = criteria.get('sector', 'any')
        risk_level = criteria.get('risk_level', 'medium')
        time_horizon = criteria.get('time_horizon', 'medium-term')
        
        # Predefined stock recommendations based on criteria
        stock_universe = {
            'large_cap_banking': [
                {'symbol': 'HDFCBANK', 'company_name': 'HDFC Bank', 'sector': 'banking'},
                {'symbol': 'ICICIBANK', 'company_name': 'ICICI Bank', 'sector': 'banking'},
                {'symbol': 'SBIN', 'company_name': 'State Bank of India', 'sector': 'banking'},
                {'symbol': 'AXISBANK', 'company_name': 'Axis Bank', 'sector': 'banking'}
            ],
            'large_cap_technology': [
                {'symbol': 'TCS', 'company_name': 'Tata Consultancy Services', 'sector': 'technology'},
                {'symbol': 'INFY', 'company_name': 'Infosys', 'sector': 'technology'},
                {'symbol': 'WIPRO', 'company_name': 'Wipro', 'sector': 'technology'},
                {'symbol': 'HCLTECH', 'company_name': 'HCL Technologies', 'sector': 'technology'}
            ],
            'large_cap_pharma': [
                {'symbol': 'SUNPHARMA', 'company_name': 'Sun Pharmaceutical', 'sector': 'pharma'},
                {'symbol': 'DRREDDY', 'company_name': 'Dr Reddys Labs', 'sector': 'pharma'},
                {'symbol': 'CIPLA', 'company_name': 'Cipla', 'sector': 'pharma'},
                {'symbol': 'DIVISLAB', 'company_name': 'Divis Laboratories', 'sector': 'pharma'}
            ],
            'large_cap_fmcg': [
                {'symbol': 'HINDUNILVR', 'company_name': 'Hindustan Unilever', 'sector': 'fmcg'},
                {'symbol': 'ITC', 'company_name': 'ITC Limited', 'sector': 'fmcg'},
                {'symbol': 'NESTLEIND', 'company_name': 'Nestle India', 'sector': 'fmcg'},
                {'symbol': 'BRITANNIA', 'company_name': 'Britannia Industries', 'sector': 'fmcg'}
            ],
            'large_cap_diversified': [
                {'symbol': 'RELIANCE', 'company_name': 'Reliance Industries', 'sector': 'energy'},
                {'symbol': 'ADANIPORTS', 'company_name': 'Adani Ports', 'sector': 'infrastructure'},
                {'symbol': 'TATASTEEL', 'company_name': 'Tata Steel', 'sector': 'metals'},
                {'symbol': 'LT', 'company_name': 'Larsen & Toubro', 'sector': 'engineering'}
            ]
        }
        
        # Select stocks based on criteria
        recommendations = []
        
        # Choose stock pool based on sector preference
        if sector == 'banking':
            stock_pool = stock_universe['large_cap_banking']
        elif sector == 'technology':
            stock_pool = stock_universe['large_cap_technology']
        elif sector == 'pharma':
            stock_pool = stock_universe['large_cap_pharma']
        elif sector == 'fmcg':
            stock_pool = stock_universe['large_cap_fmcg']
        else:  # 'any' or other
            # Mix from different sectors
            stock_pool = (stock_universe['large_cap_banking'][:2] + 
                         stock_universe['large_cap_technology'][:2] + 
                         stock_universe['large_cap_diversified'][:2])
        
        # Generate recommendations with scoring logic
        for stock in stock_pool[:6]:  # Limit to 6 recommendations
            # Simple scoring based on criteria
            base_score = 7.0  # Base score out of 10
            
            # Adjust based on risk level
            if risk_level == 'low':
                risk_adjustment = 0.5 if stock['sector'] in ['banking', 'fmcg'] else -0.5
            elif risk_level == 'high':
                risk_adjustment = 0.5 if stock['sector'] in ['technology'] else 0
            else:  # medium
                risk_adjustment = 0
            
            final_score = min(10, max(5, base_score + risk_adjustment))
            
            # Generate target price (simplified estimation)
            current_price = 1000  # Placeholder - would be fetched from market data in real implementation
            upside = final_score * 2  # Simple correlation
            target_price = current_price * (1 + upside / 100)
            
            # Generate rationale based on sector and criteria
            rationales = {
                'banking': 'Strong fundamentals, stable dividend yield, and regulatory compliance',
                'technology': 'Digital transformation trends, export revenue, and margin expansion',
                'pharma': 'Defensive sector, global market presence, and R&D pipeline',
                'fmcg': 'Consistent demand, brand strength, and rural market penetration',
                'energy': 'Integrated business model and renewable energy investments',
                'infrastructure': 'Government infrastructure spending and economic growth',
                'metals': 'Infrastructure demand and commodity price recovery',
                'engineering': 'Order book visibility and execution capabilities'
            }
            
            recommendation = {
                'symbol': stock['symbol'],
                'company_name': stock['company_name'],
                'target_price': round(target_price, 2),
                'upside_potential': round(upside, 1),
                'rationale': rationales.get(stock['sector'], 'Solid business fundamentals and growth potential'),
                'risk_rating': risk_level,
                'sector': stock['sector'],
                'score': round(final_score, 1),
                'time_horizon': time_horizon
            }
            
            recommendations.append(recommendation)
        
        return recommendations[:5]  # Return top 5 recommendations
        
    except Exception as e:
        print(f"Error getting stock recommendations: {e}")
        return None
