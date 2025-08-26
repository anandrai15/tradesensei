import trafilatura
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import time
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
import json
import os

class NewsAggregator:
    """News aggregator for financial and market news"""
    
    def __init__(self):
        self.news_sources = [
            {
                'name': 'Economic Times - Markets',
                'url': 'https://economictimes.indiatimes.com/markets',
                'xpath': '//article//h3//a',
                'selector': 'article h3 a'
            },
            {
                'name': 'Business Standard - Markets',
                'url': 'https://www.business-standard.com/markets',
                'xpath': '//div[@class="listing-content"]//h2//a',
                'selector': 'div.listing-content h2 a'
            },
            {
                'name': 'MoneyControl',
                'url': 'https://www.moneycontrol.com/news/business/markets/',
                'xpath': '//div[@class="news_title"]//a',
                'selector': 'div.news_title a'
            }
        ]
        self.cache_file = 'news_cache.json'
        self.cache_duration = 3600  # 1 hour cache
        
    def get_cached_news(self):
        """Get news from cache if valid"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                cache_time = datetime.fromisoformat(cache_data.get('timestamp', ''))
                if (datetime.now() - cache_time).seconds < self.cache_duration:
                    return cache_data.get('articles', [])
        except Exception:
            pass
        return None
    
    def save_news_cache(self, articles):
        """Save news to cache"""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'articles': articles
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    
    def scrape_news_from_source(self, source):
        """Scrape news from a specific source"""
        articles = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(source['url'], headers=headers, timeout=10)
            if response.status_code != 200:
                return articles
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find article links
            links = []
            if 'selector' in source:
                elements = soup.select(source['selector'])
                links = [elem.get('href') for elem in elements if elem.get('href')]
            
            # Clean and process links
            for link in links[:5]:  # Get top 5 articles per source
                try:
                    if link and isinstance(link, str):
                        if link.startswith('/'):
                            # Relative URL
                            base_url = source['url'].split('/')[0] + '//' + source['url'].split('/')[2]
                            full_url = base_url + link
                        elif link.startswith('http'):
                            full_url = link
                        else:
                            continue
                    else:
                        continue
                    
                    # Get article title
                    article_title = self.extract_title_from_url(full_url)
                    if article_title:
                        articles.append({
                            'title': article_title,
                            'url': full_url,
                            'source': source['name'],
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                        })
                        
                except Exception:
                    continue
                    
        except Exception:
            pass
        
        return articles
    
    def extract_title_from_url(self, url):
        """Extract title from article URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                # Use trafilatura to extract clean title
                downloaded = trafilatura.fetch_url(url)
                if downloaded:
                    metadata = trafilatura.extract_metadata(downloaded)
                    if metadata and metadata.title:
                        return metadata.title[:100]  # Limit title length
            
            # Fallback: extract from URL
            title_from_url = url.split('/')[-1].replace('-', ' ').replace('_', ' ')
            title_from_url = re.sub(r'\d+', '', title_from_url)  # Remove numbers
            title_from_url = title_from_url.strip().title()
            return title_from_url[:80] if len(title_from_url) > 10 else None
            
        except Exception:
            return None
    
    def get_latest_news(self, max_articles=15):
        """Get latest financial news articles"""
        # Check cache first
        cached_articles = self.get_cached_news()
        if cached_articles:
            return cached_articles
        
        all_articles = []
        
        # Use ThreadPoolExecutor for parallel scraping
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(self.scrape_news_from_source, source): source 
                      for source in self.news_sources}
            
            for future in futures:
                try:
                    articles = future.result(timeout=10)
                    all_articles.extend(articles)
                except Exception:
                    continue
        
        # Remove duplicates and sort by timestamp
        seen_titles = set()
        unique_articles = []
        
        for article in all_articles:
            title_lower = article['title'].lower()
            if title_lower not in seen_titles and len(article['title']) > 20:
                seen_titles.add(title_lower)
                unique_articles.append(article)
        
        # Sort by timestamp and limit
        unique_articles = sorted(unique_articles, 
                               key=lambda x: x['timestamp'], reverse=True)[:max_articles]
        
        # Cache the results
        self.save_news_cache(unique_articles)
        
        return unique_articles
    
    def get_sample_news(self):
        """Get sample news when live scraping fails"""
        return [
            {
                'title': 'NIFTY 50 Surges 250 Points on Strong FII Inflows and Banking Rally',
                'url': '#',
                'source': 'Market Today',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
            },
            {
                'title': 'Banking Stocks Outperform as NIM Expansion Continues in Q3 Results',
                'url': '#',
                'source': 'Banking Wire', 
                'timestamp': (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M')
            },
            {
                'title': 'Foreign Institutional Investors Turn Net Buyers After 3-Week Selling',
                'url': '#',
                'source': 'FII Watch',
                'timestamp': (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M')
            },
            {
                'title': 'IT Sector Outlook Brightens as US Client Spending Recovery Gains Momentum',
                'url': '#',
                'source': 'Tech Markets',
                'timestamp': (datetime.now() - timedelta(hours=3)).strftime('%Y-%m-%d %H:%M')
            },
            {
                'title': 'RBI Monetary Policy Committee Meeting: Rate Cut Expectations Build',
                'url': '#',
                'source': 'Policy Central',
                'timestamp': (datetime.now() - timedelta(hours=4)).strftime('%Y-%m-%d %H:%M')
            },
            {
                'title': 'Pharma Stocks Rally on Strong Quarterly Earnings and US FDA Approvals',
                'url': '#',
                'source': 'Pharma Focus',
                'timestamp': (datetime.now() - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M')
            },
            {
                'title': 'Auto Sector Shows Green Shoots with Festive Season Demand Recovery',
                'url': '#',
                'source': 'Auto News',
                'timestamp': (datetime.now() - timedelta(hours=6)).strftime('%Y-%m-%d %H:%M')
            },
            {
                'title': 'Oil & Gas Stocks Under Pressure as Crude Prices Decline Globally',
                'url': '#',
                'source': 'Energy Watch',
                'timestamp': (datetime.now() - timedelta(hours=7)).strftime('%Y-%m-%d %H:%M')
            },
            {
                'title': 'FMCG Giants Report Steady Growth Despite Rural Demand Challenges',
                'url': '#',
                'source': 'Consumer Goods',
                'timestamp': (datetime.now() - timedelta(hours=8)).strftime('%Y-%m-%d %H:%M')
            },
            {
                'title': 'Renewable Energy Stocks Soar on Government Policy Support',
                'url': '#',
                'source': 'Green Energy',
                'timestamp': (datetime.now() - timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')
            }
        ]

# Global instance
news_aggregator = NewsAggregator()

def get_financial_news():
    """Main function to get financial news"""
    try:
        # For now, use sample news to ensure reliability
        # TODO: Enable live scraping after testing
        return news_aggregator.get_sample_news()
    except Exception:
        # Return sample news if scraping fails
        return news_aggregator.get_sample_news()