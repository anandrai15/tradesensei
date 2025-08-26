import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Optional, List
import requests
import json
from datetime import datetime, timedelta

def get_fundamental_data(symbol: str) -> Dict:
    """
    Get comprehensive fundamental data for a stock
    """
    try:
        # Add .NS suffix for NSE stocks if not present
        if not symbol.endswith('.NS') and not symbol.startswith('^'):
            symbol = f"{symbol}.NS"
        
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Get financial statements
        financials = ticker.financials
        balance_sheet = ticker.balance_sheet
        cash_flow = ticker.cashflow
        
        fundamental_data = {
            'basic_info': {
                'symbol': symbol.replace('.NS', ''),
                'company_name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'current_price': info.get('currentPrice', 0),
                'currency': info.get('currency', 'INR')
            },
            'valuation_ratios': {
                'pe_ratio': info.get('trailingPE', None),
                'forward_pe': info.get('forwardPE', None),
                'peg_ratio': info.get('pegRatio', None),
                'price_to_book': info.get('priceToBook', None),
                'price_to_sales': info.get('priceToSalesTrailing12Months', None),
                'ev_to_revenue': info.get('enterpriseToRevenue', None),
                'ev_to_ebitda': info.get('enterpriseToEbitda', None)
            },
            'profitability_ratios': {
                'roe': info.get('returnOnEquity', None),
                'roa': info.get('returnOnAssets', None),
                'profit_margin': info.get('profitMargins', None),
                'operating_margin': info.get('operatingMargins', None),
                'gross_margin': info.get('grossMargins', None)
            },
            'financial_health': {
                'debt_to_equity': info.get('debtToEquity', None),
                'current_ratio': info.get('currentRatio', None),
                'quick_ratio': info.get('quickRatio', None),
                'total_cash': info.get('totalCash', None),
                'total_debt': info.get('totalDebt', None),
                'free_cash_flow': info.get('freeCashflow', None)
            },
            'growth_metrics': {
                'revenue_growth': info.get('revenueGrowth', None),
                'earnings_growth': info.get('earningsGrowth', None),
                'revenue_quarterly_growth': info.get('revenueQuarterlyGrowth', None),
                'earnings_quarterly_growth': info.get('earningsQuarterlyGrowth', None)
            },
            'dividend_info': {
                'dividend_yield': info.get('dividendYield', None),
                'dividend_rate': info.get('dividendRate', None),
                'payout_ratio': info.get('payoutRatio', None),
                'ex_dividend_date': info.get('exDividendDate', None)
            },
            'analyst_info': {
                'recommendation': info.get('recommendationKey', 'N/A'),
                'target_price': info.get('targetMeanPrice', None),
                'analyst_count': info.get('numberOfAnalystOpinions', 0)
            }
        }
        
        # Calculate additional ratios if financial data is available
        if not financials.empty and not balance_sheet.empty:
            try:
                # Get latest year data
                latest_financials = financials.iloc[:, 0]
                latest_balance = balance_sheet.iloc[:, 0]
                
                # Calculate custom ratios
                total_revenue = latest_financials.get('Total Revenue', 0)
                net_income = latest_financials.get('Net Income', 0)
                total_assets = latest_balance.get('Total Assets', 0)
                total_equity = latest_balance.get('Stockholders Equity', 0)
                
                if total_assets > 0:
                    fundamental_data['custom_ratios'] = {
                        'asset_turnover': total_revenue / total_assets if total_assets > 0 else None,
                        'equity_multiplier': total_assets / total_equity if total_equity > 0 else None,
                        'net_profit_margin': net_income / total_revenue if total_revenue > 0 else None
                    }
            except Exception as e:
                print(f"Error calculating custom ratios: {e}")
        
        return fundamental_data
        
    except Exception as e:
        print(f"Error fetching fundamental data for {symbol}: {e}")
        return {}

def calculate_financial_score(fundamental_data: Dict) -> Dict:
    """
    Calculate a comprehensive financial health score
    """
    try:
        score_components = {
            'valuation': 0,
            'profitability': 0,
            'financial_health': 0,
            'growth': 0,
            'dividend': 0
        }
        
        max_scores = {
            'valuation': 25,
            'profitability': 25,
            'financial_health': 25,
            'growth': 20,
            'dividend': 5
        }
        
        # Valuation scoring
        valuation = fundamental_data.get('valuation_ratios', {})
        pe_ratio = valuation.get('pe_ratio')
        pb_ratio = valuation.get('price_to_book')
        
        if pe_ratio:
            if 10 <= pe_ratio <= 25:
                score_components['valuation'] += 15
            elif 5 <= pe_ratio < 10 or 25 < pe_ratio <= 35:
                score_components['valuation'] += 10
            elif pe_ratio < 5 or pe_ratio > 35:
                score_components['valuation'] += 5
        
        if pb_ratio:
            if 1 <= pb_ratio <= 3:
                score_components['valuation'] += 10
            elif 0.5 <= pb_ratio < 1 or 3 < pb_ratio <= 5:
                score_components['valuation'] += 5
        
        # Profitability scoring
        profitability = fundamental_data.get('profitability_ratios', {})
        roe = profitability.get('roe')
        profit_margin = profitability.get('profit_margin')
        
        if roe:
            if roe >= 0.15:
                score_components['profitability'] += 15
            elif roe >= 0.10:
                score_components['profitability'] += 10
            elif roe >= 0.05:
                score_components['profitability'] += 5
        
        if profit_margin:
            if profit_margin >= 0.15:
                score_components['profitability'] += 10
            elif profit_margin >= 0.10:
                score_components['profitability'] += 7
            elif profit_margin >= 0.05:
                score_components['profitability'] += 5
        
        # Financial health scoring
        financial_health = fundamental_data.get('financial_health', {})
        debt_to_equity = financial_health.get('debt_to_equity')
        current_ratio = financial_health.get('current_ratio')
        
        if debt_to_equity is not None:
            if debt_to_equity <= 0.5:
                score_components['financial_health'] += 15
            elif debt_to_equity <= 1.0:
                score_components['financial_health'] += 10
            elif debt_to_equity <= 2.0:
                score_components['financial_health'] += 5
        
        if current_ratio:
            if current_ratio >= 1.5:
                score_components['financial_health'] += 10
            elif current_ratio >= 1.0:
                score_components['financial_health'] += 7
        
        # Growth scoring
        growth = fundamental_data.get('growth_metrics', {})
        revenue_growth = growth.get('revenue_growth')
        earnings_growth = growth.get('earnings_growth')
        
        if revenue_growth:
            if revenue_growth >= 0.20:
                score_components['growth'] += 10
            elif revenue_growth >= 0.10:
                score_components['growth'] += 7
            elif revenue_growth >= 0.05:
                score_components['growth'] += 5
        
        if earnings_growth:
            if earnings_growth >= 0.20:
                score_components['growth'] += 10
            elif earnings_growth >= 0.10:
                score_components['growth'] += 7
            elif earnings_growth >= 0.05:
                score_components['growth'] += 5
        
        # Dividend scoring
        dividend = fundamental_data.get('dividend_info', {})
        dividend_yield = dividend.get('dividend_yield')
        
        if dividend_yield and dividend_yield > 0:
            if 0.02 <= dividend_yield <= 0.06:
                score_components['dividend'] += 5
            elif dividend_yield > 0:
                score_components['dividend'] += 3
        
        # Calculate total score and rating
        total_score = sum(score_components.values())
        max_total = sum(max_scores.values())
        percentage_score = (total_score / max_total) * 100
        
        # Determine rating
        if percentage_score >= 80:
            rating = 'Excellent'
        elif percentage_score >= 70:
            rating = 'Good'
        elif percentage_score >= 60:
            rating = 'Average'
        elif percentage_score >= 50:
            rating = 'Below Average'
        else:
            rating = 'Poor'
        
        return {
            'total_score': total_score,
            'max_score': max_total,
            'percentage': percentage_score,
            'rating': rating,
            'component_scores': score_components,
            'max_component_scores': max_scores
        }
        
    except Exception as e:
        print(f"Error calculating financial score: {e}")
        return {}

def get_peer_comparison(symbol: str, sector: str = None) -> Dict:
    """
    Compare stock with sector peers
    """
    try:
        # Get fundamental data for the stock
        stock_data = get_fundamental_data(symbol)
        
        if not stock_data:
            return {}
        
        # Common Indian stocks by sector for comparison
        sector_stocks = {
            'Technology': ['TCS.NS', 'INFY.NS', 'WIPRO.NS', 'TECHM.NS', 'HCLTECH.NS'],
            'Banking': ['HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'KOTAKBANK.NS', 'AXISBANK.NS'],
            'Oil & Gas': ['RELIANCE.NS', 'ONGC.NS', 'IOC.NS', 'BPCL.NS', 'HINDPETRO.NS'],
            'Pharmaceuticals': ['SUNPHARMA.NS', 'DRREDDY.NS', 'CIPLA.NS', 'DIVISLAB.NS', 'BIOCON.NS'],
            'Automobiles': ['MARUTI.NS', 'TATAMOTORS.NS', 'M&M.NS', 'BAJAJ-AUTO.NS', 'EICHERMOT.NS']
        }
        
        # Determine sector
        stock_sector = sector or stock_data.get('basic_info', {}).get('sector', '')
        peer_symbols = []
        
        # Find appropriate peer group
        for sect, stocks in sector_stocks.items():
            if sect.lower() in stock_sector.lower():
                peer_symbols = [s for s in stocks if s != f"{symbol}.NS"]
                break
        
        if not peer_symbols:
            # Use random selection from all stocks if sector not found
            all_stocks = [stock for stocks in sector_stocks.values() for stock in stocks]
            peer_symbols = all_stocks[:5]
        
        # Get peer data
        peer_data = []
        for peer_symbol in peer_symbols[:5]:  # Limit to 5 peers
            peer_fundamentals = get_fundamental_data(peer_symbol.replace('.NS', ''))
            if peer_fundamentals:
                peer_data.append(peer_fundamentals)
        
        # Calculate sector averages
        sector_averages = {}
        if peer_data:
            metrics_to_average = [
                ('valuation_ratios', 'pe_ratio'),
                ('valuation_ratios', 'price_to_book'),
                ('profitability_ratios', 'roe'),
                ('profitability_ratios', 'profit_margin'),
                ('financial_health', 'debt_to_equity'),
                ('growth_metrics', 'revenue_growth')
            ]
            
            for category, metric in metrics_to_average:
                values = []
                for peer in peer_data:
                    value = peer.get(category, {}).get(metric)
                    if value is not None:
                        values.append(value)
                
                if values:
                    sector_averages[f"{category}_{metric}"] = {
                        'average': np.mean(values),
                        'median': np.median(values),
                        'min': np.min(values),
                        'max': np.max(values)
                    }
        
        # Compare stock with sector
        stock_metrics = {}
        for category, metric in [
            ('valuation_ratios', 'pe_ratio'),
            ('valuation_ratios', 'price_to_book'),
            ('profitability_ratios', 'roe'),
            ('profitability_ratios', 'profit_margin'),
            ('financial_health', 'debt_to_equity'),
            ('growth_metrics', 'revenue_growth')
        ]:
            stock_value = stock_data.get(category, {}).get(metric)
            sector_avg = sector_averages.get(f"{category}_{metric}", {}).get('average')
            
            if stock_value is not None and sector_avg is not None:
                stock_metrics[f"{category}_{metric}"] = {
                    'stock_value': stock_value,
                    'sector_average': sector_avg,
                    'vs_sector': ((stock_value - sector_avg) / sector_avg) * 100 if sector_avg != 0 else 0
                }
        
        return {
            'stock_symbol': symbol,
            'sector': stock_sector,
            'peer_symbols': [p.replace('.NS', '') for p in peer_symbols],
            'sector_averages': sector_averages,
            'comparison': stock_metrics,
            'peer_count': len(peer_data)
        }
        
    except Exception as e:
        print(f"Error in peer comparison for {symbol}: {e}")
        return {}

def get_dividend_analysis(symbol: str) -> Dict:
    """
    Detailed dividend analysis
    """
    try:
        if not symbol.endswith('.NS') and not symbol.startswith('^'):
            symbol = f"{symbol}.NS"
        
        ticker = yf.Ticker(symbol)
        
        # Get dividend history
        dividends = ticker.dividends
        
        if dividends.empty:
            return {'has_dividends': False, 'message': 'No dividend history found'}
        
        # Calculate dividend metrics
        recent_dividends = dividends.tail(4)  # Last 4 dividends
        annual_dividend = recent_dividends.sum()
        
        # Get current price
        current_price = ticker.info.get('currentPrice', 0)
        dividend_yield = (annual_dividend / current_price) * 100 if current_price > 0 else 0
        
        # Dividend growth analysis
        yearly_dividends = dividends.resample('Y').sum()
        if len(yearly_dividends) >= 2:
            dividend_growth_rates = yearly_dividends.pct_change().dropna()
            avg_growth_rate = dividend_growth_rates.mean() * 100
            consistent_growth = (dividend_growth_rates > 0).sum() / len(dividend_growth_rates) * 100
        else:
            avg_growth_rate = 0
            consistent_growth = 0
        
        # Payout ratio
        earnings_per_share = ticker.info.get('trailingEps', 0)
        payout_ratio = (annual_dividend / earnings_per_share) * 100 if earnings_per_share > 0 else 0
        
        return {
            'has_dividends': True,
            'annual_dividend': annual_dividend,
            'dividend_yield': dividend_yield,
            'avg_growth_rate': avg_growth_rate,
            'payout_ratio': payout_ratio,
            'consistent_growth_percentage': consistent_growth,
            'total_payments': len(dividends),
            'last_payment_date': dividends.index[-1] if not dividends.empty else None,
            'last_payment_amount': dividends.iloc[-1] if not dividends.empty else 0,
            'dividend_frequency': 'Quarterly' if len(recent_dividends) >= 4 else 'Annual'
        }
        
    except Exception as e:
        print(f"Error in dividend analysis for {symbol}: {e}")
        return {'has_dividends': False, 'error': str(e)}

def get_financial_statements_summary(symbol: str) -> Dict:
    """
    Get summarized financial statements
    """
    try:
        if not symbol.endswith('.NS') and not symbol.startswith('^'):
            symbol = f"{symbol}.NS"
        
        ticker = yf.Ticker(symbol)
        
        # Get financial statements
        financials = ticker.financials
        balance_sheet = ticker.balance_sheet
        cash_flow = ticker.cashflow
        
        summary = {}
        
        # Income Statement Summary (latest year)
        if not financials.empty:
            latest_financials = financials.iloc[:, 0]
            summary['income_statement'] = {
                'total_revenue': latest_financials.get('Total Revenue', 0),
                'gross_profit': latest_financials.get('Gross Profit', 0),
                'operating_income': latest_financials.get('Operating Income', 0),
                'net_income': latest_financials.get('Net Income', 0),
                'ebitda': latest_financials.get('EBITDA', 0),
                'year': financials.columns[0].year if len(financials.columns) > 0 else None
            }
        
        # Balance Sheet Summary (latest year)
        if not balance_sheet.empty:
            latest_balance = balance_sheet.iloc[:, 0]
            summary['balance_sheet'] = {
                'total_assets': latest_balance.get('Total Assets', 0),
                'total_liabilities': latest_balance.get('Total Liabilities Net Minority Interest', 0),
                'stockholders_equity': latest_balance.get('Stockholders Equity', 0),
                'cash_and_equivalents': latest_balance.get('Cash And Cash Equivalents', 0),
                'total_debt': latest_balance.get('Total Debt', 0),
                'year': balance_sheet.columns[0].year if len(balance_sheet.columns) > 0 else None
            }
        
        # Cash Flow Summary (latest year)
        if not cash_flow.empty:
            latest_cash_flow = cash_flow.iloc[:, 0]
            summary['cash_flow'] = {
                'operating_cash_flow': latest_cash_flow.get('Operating Cash Flow', 0),
                'investing_cash_flow': latest_cash_flow.get('Investing Cash Flow', 0),
                'financing_cash_flow': latest_cash_flow.get('Financing Cash Flow', 0),
                'free_cash_flow': latest_cash_flow.get('Free Cash Flow', 0),
                'capital_expenditure': latest_cash_flow.get('Capital Expenditure', 0),
                'year': cash_flow.columns[0].year if len(cash_flow.columns) > 0 else None
            }
        
        # Calculate trends if multiple years available
        if len(financials.columns) >= 2:
            revenue_growth = ((financials.loc['Total Revenue'].iloc[0] - 
                             financials.loc['Total Revenue'].iloc[1]) / 
                            financials.loc['Total Revenue'].iloc[1]) * 100
            
            net_income_growth = ((financials.loc['Net Income'].iloc[0] - 
                                financials.loc['Net Income'].iloc[1]) / 
                               abs(financials.loc['Net Income'].iloc[1])) * 100
            
            summary['growth_trends'] = {
                'revenue_growth_yoy': revenue_growth,
                'net_income_growth_yoy': net_income_growth
            }
        
        return summary
        
    except Exception as e:
        print(f"Error getting financial statements summary for {symbol}: {e}")
        return {}
