import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import os
from .market_data import get_stock_data, get_real_time_price
from .fundamentals import get_fundamental_data
from .ai_analysis import analyze_portfolio_risk

class Portfolio:
    def __init__(self, portfolio_file: str = "portfolio.json"):
        self.portfolio_file = portfolio_file
        self.holdings = self._load_portfolio()
        self.watchlist = self._load_watchlist()
    
    def _load_portfolio(self) -> List[Dict]:
        """Load portfolio from JSON file"""
        try:
            if os.path.exists(self.portfolio_file):
                with open(self.portfolio_file, 'r') as f:
                    data = json.load(f)
                    return data.get('holdings', [])
            return []
        except Exception as e:
            print(f"Error loading portfolio: {e}")
            return []
    
    def _load_watchlist(self) -> List[str]:
        """Load watchlist from JSON file"""
        try:
            if os.path.exists(self.portfolio_file):
                with open(self.portfolio_file, 'r') as f:
                    data = json.load(f)
                    return data.get('watchlist', [])
            return []
        except Exception as e:
            print(f"Error loading watchlist: {e}")
            return []
    
    def _save_portfolio(self):
        """Save portfolio and watchlist to JSON file"""
        try:
            data = {
                'holdings': self.holdings,
                'watchlist': self.watchlist,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.portfolio_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving portfolio: {e}")
    
    def add_holding(self, symbol: str, quantity: int, buy_price: float, buy_date: str = None) -> bool:
        """Add a new holding to portfolio"""
        try:
            if buy_date is None:
                buy_date = datetime.now().strftime('%Y-%m-%d')
            
            # Check if holding already exists
            for holding in self.holdings:
                if holding['symbol'] == symbol:
                    # Update existing holding (average cost)
                    total_cost = (holding['quantity'] * holding['buy_price']) + (quantity * buy_price)
                    total_quantity = holding['quantity'] + quantity
                    holding['buy_price'] = total_cost / total_quantity
                    holding['quantity'] = total_quantity
                    holding['last_updated'] = datetime.now().isoformat()
                    self._save_portfolio()
                    return True
            
            # Add new holding
            new_holding = {
                'symbol': symbol,
                'quantity': quantity,
                'buy_price': buy_price,
                'buy_date': buy_date,
                'added_date': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            
            self.holdings.append(new_holding)
            self._save_portfolio()
            return True
            
        except Exception as e:
            print(f"Error adding holding: {e}")
            return False
    
    def remove_holding(self, symbol: str, quantity: int = None) -> bool:
        """Remove holding or reduce quantity"""
        try:
            for i, holding in enumerate(self.holdings):
                if holding['symbol'] == symbol:
                    if quantity is None or quantity >= holding['quantity']:
                        # Remove entire holding
                        self.holdings.pop(i)
                    else:
                        # Reduce quantity
                        holding['quantity'] -= quantity
                        holding['last_updated'] = datetime.now().isoformat()
                    
                    self._save_portfolio()
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error removing holding: {e}")
            return False
    
    def add_to_watchlist(self, symbol: str) -> bool:
        """Add stock to watchlist"""
        try:
            if symbol not in self.watchlist:
                self.watchlist.append(symbol)
                self._save_portfolio()
                return True
            return False
        except Exception as e:
            print(f"Error adding to watchlist: {e}")
            return False
    
    def remove_from_watchlist(self, symbol: str) -> bool:
        """Remove stock from watchlist"""
        try:
            if symbol in self.watchlist:
                self.watchlist.remove(symbol)
                self._save_portfolio()
                return True
            return False
        except Exception as e:
            print(f"Error removing from watchlist: {e}")
            return False
    
    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary"""
        try:
            if not self.holdings:
                return {
                    'total_value': 0,
                    'total_invested': 0,
                    'total_pnl': 0,
                    'total_pnl_percent': 0,
                    'holdings_count': 0,
                    'top_performer': None,
                    'worst_performer': None
                }
            
            total_value = 0
            total_invested = 0
            holdings_performance = []
            
            for holding in self.holdings:
                symbol = holding['symbol']
                quantity = holding['quantity']
                buy_price = holding['buy_price']
                
                # Get current price
                current_price = get_real_time_price(symbol)
                if current_price is None:
                    current_price = buy_price  # Fallback to buy price
                
                # Calculate metrics
                invested_amount = quantity * buy_price
                current_value = quantity * current_price
                pnl = current_value - invested_amount
                pnl_percent = (pnl / invested_amount) * 100 if invested_amount > 0 else 0
                
                total_value += current_value
                total_invested += invested_amount
                
                holdings_performance.append({
                    'symbol': symbol,
                    'quantity': quantity,
                    'buy_price': buy_price,
                    'current_price': current_price,
                    'invested_amount': invested_amount,
                    'current_value': current_value,
                    'pnl': pnl,
                    'pnl_percent': pnl_percent
                })
            
            total_pnl = total_value - total_invested
            total_pnl_percent = (total_pnl / total_invested) * 100 if total_invested > 0 else 0
            
            # Find top and worst performers
            if holdings_performance:
                top_performer = max(holdings_performance, key=lambda x: x['pnl_percent'])
                worst_performer = min(holdings_performance, key=lambda x: x['pnl_percent'])
            else:
                top_performer = worst_performer = None
            
            return {
                'total_value': total_value,
                'total_invested': total_invested,
                'total_pnl': total_pnl,
                'total_pnl_percent': total_pnl_percent,
                'holdings_count': len(self.holdings),
                'holdings_performance': holdings_performance,
                'top_performer': top_performer,
                'worst_performer': worst_performer
            }
            
        except Exception as e:
            print(f"Error getting portfolio summary: {e}")
            return {}
    
    def get_sector_allocation(self) -> Dict:
        """Get portfolio allocation by sector"""
        try:
            if not self.holdings:
                return {}
            
            sector_allocation = {}
            total_value = 0
            
            for holding in self.holdings:
                symbol = holding['symbol']
                quantity = holding['quantity']
                current_price = get_real_time_price(symbol) or holding['buy_price']
                holding_value = quantity * current_price
                
                # Get sector information
                fundamental_data = get_fundamental_data(symbol)
                sector = fundamental_data.get('basic_info', {}).get('sector', 'Unknown')
                
                if sector not in sector_allocation:
                    sector_allocation[sector] = {
                        'value': 0,
                        'stocks': [],
                        'percentage': 0
                    }
                
                sector_allocation[sector]['value'] += holding_value
                sector_allocation[sector]['stocks'].append(symbol)
                total_value += holding_value
            
            # Calculate percentages
            for sector in sector_allocation:
                sector_allocation[sector]['percentage'] = (
                    sector_allocation[sector]['value'] / total_value * 100
                ) if total_value > 0 else 0
            
            return sector_allocation
            
        except Exception as e:
            print(f"Error getting sector allocation: {e}")
            return {}
    
    def get_portfolio_performance_history(self, period: str = "1mo") -> Dict:
        """Get historical performance of portfolio"""
        try:
            if not self.holdings:
                return {}
            
            # Get historical data for all holdings
            portfolio_history = {}
            
            for holding in self.holdings:
                symbol = holding['symbol']
                quantity = holding['quantity']
                
                # Get historical data
                stock_data = get_stock_data(symbol, period)
                
                if not stock_data.empty:
                    # Calculate holding value over time
                    holding_values = stock_data['Close'] * quantity
                    portfolio_history[symbol] = holding_values
            
            if not portfolio_history:
                return {}
            
            # Combine all holdings into portfolio timeline
            portfolio_df = pd.DataFrame(portfolio_history)
            portfolio_total = portfolio_df.sum(axis=1)
            
            # Calculate returns
            portfolio_returns = portfolio_total.pct_change().dropna()
            
            # Performance metrics
            total_return = (portfolio_total.iloc[-1] / portfolio_total.iloc[0] - 1) * 100
            volatility = portfolio_returns.std() * np.sqrt(252) * 100  # Annualized
            sharpe_ratio = (portfolio_returns.mean() / portfolio_returns.std() * np.sqrt(252)) if portfolio_returns.std() > 0 else 0
            max_drawdown = ((portfolio_total / portfolio_total.expanding().max()) - 1).min() * 100
            
            return {
                'total_return': total_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'portfolio_timeline': portfolio_total.to_dict(),
                'daily_returns': portfolio_returns.to_dict()
            }
            
        except Exception as e:
            print(f"Error getting portfolio performance history: {e}")
            return {}
    
    def get_watchlist_data(self) -> List[Dict]:
        """Get current data for watchlist stocks"""
        try:
            watchlist_data = []
            
            for symbol in self.watchlist:
                current_price = get_real_time_price(symbol)
                if current_price:
                    # Get basic stock data
                    stock_data = get_stock_data(symbol, period="5d")
                    
                    if not stock_data.empty:
                        prev_price = stock_data['Close'].iloc[-2] if len(stock_data) > 1 else current_price
                        change = current_price - prev_price
                        change_percent = (change / prev_price) * 100 if prev_price > 0 else 0
                        
                        # Get fundamental data
                        fundamental = get_fundamental_data(symbol)
                        basic_info = fundamental.get('basic_info', {})
                        
                        watchlist_data.append({
                            'symbol': symbol,
                            'company_name': basic_info.get('company_name', 'N/A'),
                            'current_price': current_price,
                            'change': change,
                            'change_percent': change_percent,
                            'sector': basic_info.get('sector', 'N/A'),
                            'market_cap': basic_info.get('market_cap', 0)
                        })
            
            return watchlist_data
            
        except Exception as e:
            print(f"Error getting watchlist data: {e}")
            return []
    
    def calculate_portfolio_risk(self) -> Dict:
        """Calculate portfolio risk metrics"""
        try:
            if not self.holdings:
                return {}
            
            # Prepare portfolio data for AI analysis
            portfolio_for_analysis = []
            
            for holding in self.holdings:
                symbol = holding['symbol']
                quantity = holding['quantity']
                current_price = get_real_time_price(symbol) or holding['buy_price']
                
                portfolio_for_analysis.append({
                    'symbol': symbol,
                    'quantity': quantity,
                    'current_price': current_price
                })
            
            # Get AI-powered risk analysis
            ai_risk_analysis = analyze_portfolio_risk(portfolio_for_analysis)
            
            # Calculate additional risk metrics
            portfolio_summary = self.get_portfolio_summary()
            sector_allocation = self.get_sector_allocation()
            
            # Concentration risk (top 3 holdings percentage)
            holdings_by_value = sorted(
                portfolio_summary.get('holdings_performance', []),
                key=lambda x: x['current_value'],
                reverse=True
            )
            
            top_3_percentage = 0
            total_value = portfolio_summary.get('total_value', 0)
            
            for i in range(min(3, len(holdings_by_value))):
                top_3_percentage += (holdings_by_value[i]['current_value'] / total_value * 100) if total_value > 0 else 0
            
            # Sector concentration risk
            max_sector_allocation = max(
                [sector['percentage'] for sector in sector_allocation.values()]
            ) if sector_allocation else 0
            
            risk_metrics = {
                'concentration_risk': {
                    'top_3_holdings_percentage': top_3_percentage,
                    'max_sector_allocation': max_sector_allocation,
                    'number_of_holdings': len(self.holdings),
                    'number_of_sectors': len(sector_allocation)
                },
                'diversification_score': min(100, (len(self.holdings) * 10) + (len(sector_allocation) * 5)),
                'ai_analysis': ai_risk_analysis
            }
            
            return risk_metrics
            
        except Exception as e:
            print(f"Error calculating portfolio risk: {e}")
            return {}
    
    def get_portfolio_recommendations(self) -> Dict:
        """Get AI-powered portfolio recommendations"""
        try:
            if not self.holdings:
                return {'message': 'No holdings in portfolio for analysis'}
            
            # Get current portfolio analysis
            portfolio_summary = self.get_portfolio_summary()
            sector_allocation = self.get_sector_allocation()
            risk_metrics = self.calculate_portfolio_risk()
            
            recommendations = {
                'rebalancing': [],
                'additions': [],
                'reductions': [],
                'risk_mitigation': []
            }
            
            # Rebalancing recommendations
            if sector_allocation:
                for sector, allocation in sector_allocation.items():
                    if allocation['percentage'] > 40:
                        recommendations['rebalancing'].append({
                            'type': 'Reduce sector concentration',
                            'description': f"Consider reducing {sector} allocation from {allocation['percentage']:.1f}%",
                            'priority': 'High' if allocation['percentage'] > 50 else 'Medium'
                        })
            
            # Performance-based recommendations
            holdings_performance = portfolio_summary.get('holdings_performance', [])
            
            for holding in holdings_performance:
                if holding['pnl_percent'] < -20:
                    recommendations['reductions'].append({
                        'symbol': holding['symbol'],
                        'description': f"Consider reviewing {holding['symbol']} (down {abs(holding['pnl_percent']):.1f}%)",
                        'current_loss': holding['pnl_percent']
                    })
            
            # Diversification recommendations
            if len(self.holdings) < 5:
                recommendations['additions'].append({
                    'type': 'Increase diversification',
                    'description': 'Consider adding more stocks to reduce concentration risk',
                    'priority': 'Medium'
                })
            
            # Risk mitigation from AI analysis
            ai_analysis = risk_metrics.get('ai_analysis', {})
            if ai_analysis and 'recommendations' in ai_analysis:
                recommendations['risk_mitigation'] = ai_analysis['recommendations']
            
            return recommendations
            
        except Exception as e:
            print(f"Error getting portfolio recommendations: {e}")
            return {}
    
    def export_portfolio_data(self) -> Dict:
        """Export complete portfolio data"""
        try:
            return {
                'portfolio_summary': self.get_portfolio_summary(),
                'sector_allocation': self.get_sector_allocation(),
                'performance_history': self.get_portfolio_performance_history(),
                'watchlist': self.get_watchlist_data(),
                'risk_analysis': self.calculate_portfolio_risk(),
                'recommendations': self.get_portfolio_recommendations(),
                'export_date': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error exporting portfolio data: {e}")
            return {}
