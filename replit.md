# TRADESENSEI - AI Trading Agent

## Overview

TRADESENSEI is a luxury-branded, comprehensive AI-powered trading analysis platform specifically designed for Indian stock markets (NSE/BSE). The application provides real-time market data, fundamental and technical analysis, portfolio tracking, stock screening, AI-driven insights, and automated reporting capabilities. Built with Streamlit as the frontend framework, it integrates multiple data sources and AI services to deliver actionable trading intelligence with a premium user experience featuring a sleek black background with white text for optimal readability and professional appearance.

## User Preferences

Preferred communication style: Simple, everyday language.
Technical Requirements: Must use ONLY free and open-source tools (no paid APIs or services).

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit with multi-page application structure
- **Branding**: TRADESENSEI master trading platform with martial arts (🥋) iconography
- **Color Palette**: Sleek black background (#000000) with white text (#FFFFFF) for premium professional appearance
- **Layout**: Wide layout with sidebar navigation and responsive design
- **Visualization**: Plotly for interactive charts (candlestick, volume, gauges, pie charts) with matplotlib for specialized histograms
- **Styling**: Custom CSS for enhanced UI/UX with gradient backgrounds, luxury metric cards, and themed components
- **Pages**: Modular page structure with 5 main sections (Market Dashboard, Stock Screener, Portfolio Tracker, AI Analysis, Reports & Settings)
- **Visual Elements**: Gradient headers, bordered metric containers, luxury button styling with hover effects

### Backend Architecture
- **Data Processing**: Pandas and NumPy for data manipulation and numerical computations
- **Market Data Provider**: Yahoo Finance (yfinance) as primary data source for Indian stocks
- **Stock Universe**: Predefined list of major Indian stocks (NIFTY 50 and additional blue-chip stocks)
- **Caching Strategy**: Time-based caching system for market data with 1-hour expiry
- **Concurrent Processing**: ThreadPoolExecutor for parallel stock data fetching
- **File Storage**: JSON-based persistence for portfolio data, settings, and user preferences

### AI Integration (Free & Open Source)
- **AI Provider**: Statistical analysis and machine learning algorithms (scikit-learn) for market insights
- **AI Capabilities**: 
  - Market sentiment analysis using technical indicators and statistical models
  - Stock probability analysis using rule-based scoring systems
  - Daily market summaries with statistical commentary
  - Portfolio risk analysis using quantitative methods
  - Automated stock recommendations based on technical and fundamental scoring

### Data Management
- **Market Data**: Real-time and historical stock prices, volumes, and market indices
- **Fundamental Analysis**: Financial ratios, valuation metrics, profitability indicators
- **Technical Analysis**: Moving averages, RSI, MACD, Bollinger Bands, breakout detection
- **Portfolio Management**: Holdings tracking, performance calculation, sector allocation
- **Screening Engine**: Multi-criteria stock filtering with pre-built and custom strategies

### Automation & Scheduling (Free & Open Source)
- **Job Scheduler**: Schedule library for automated tasks
- **Notification System**: File-based notification system with HTML reports and JSON logs
- **Automated Reports**: Daily market summaries, portfolio updates, and alert notifications saved locally
- **Market Timing**: IST-based scheduling aligned with Indian market hours (9:15 AM - 3:30 PM)

### Data Processing Patterns
- **Modular Utilities**: Separate modules for market data, fundamentals, AI analysis, portfolio management, and notifications
- **Error Handling**: Comprehensive exception handling with fallback mechanisms
- **Data Validation**: Input validation and data quality checks throughout the pipeline
- **Performance Optimization**: Caching, parallel processing, and efficient data structures
- **Advanced Analytics**: NIFTY breakout analysis with matplotlib histograms for 6-8 day range visualization
- **Technical Indicators**: RSI, Supertrend, and quarterly earnings screening capabilities

## External Dependencies

### Financial Data Services
- **Yahoo Finance API**: Primary source for Indian stock market data (NSE/BSE)
- **Real-time Data**: Live price feeds and market status information

### AI and Machine Learning (Free & Open Source)
- **Scikit-learn**: Statistical models and machine learning algorithms for market analysis
- **NumPy/Pandas**: Mathematical computations and data processing
- **Rule-based Systems**: Custom algorithms for sentiment analysis and stock scoring

### Communication Services (Free & Open Source)
- **File-based Notifications**: HTML reports and JSON logs stored locally
  - Reports directory for viewing market summaries
  - Notifications directory for alert messages
  - No external API dependencies required

### Python Libraries
- **Web Framework**: Streamlit for the user interface
- **Data Processing**: pandas, numpy for data manipulation
- **Visualization**: plotly for interactive charts and graphs
- **Financial Data**: yfinance for market data retrieval
- **HTTP Requests**: requests for API calls
- **Scheduling**: schedule library for automated tasks
- **Threading**: concurrent.futures for parallel processing
- **Date/Time**: datetime for temporal operations

### Environment Configuration
- **API Keys**: OpenAI, Twilio credentials via environment variables
- **Email Configuration**: SMTP settings for notification delivery
- **Phone Numbers**: Recipient contact information for alerts
- **File Storage**: Local JSON files for data persistence

### Market-Specific Integrations
- **NSE/BSE Data**: Indian stock exchange data through Yahoo Finance
- **Currency**: INR-based pricing and calculations
- **Market Hours**: Indian Standard Time (IST) scheduling
- **Stock Symbols**: .NS suffix handling for NSE-listed securities