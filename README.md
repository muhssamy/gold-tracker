# KSA Gold Price Tracker - Saudi Gold Investment Calculator

[![Build Status](https://github.com/muhssamy/gold-tracker/actions/workflows/docker-build-push.yml/badge.svg)](https://github.com/muhssamy/gold-tracker/actions)

A comprehensive application for tracking gold prices in Saudi Arabia (KSA) with real-time Saudi Riyal (SAR) conversion, helping Saudi investors monitor and calculate their gold investment performance.

## 🌟 Features

- **Real-time Gold Prices in Saudi Riyal (SAR)**: Track current gold prices in Saudi Arabia
- **Historical Price Lookup**: View gold prices from specific dates in SAR
- **Multi-Purchase Tracking**: Add multiple gold purchases with different dates and weights
- **Investment Performance**: Calculate profit/loss for each purchase and total investment
- **SAR Currency**: All calculations in Saudi Riyal with USD conversion display
- **Responsive Design**: Works on desktop and mobile devices
- **Offline Capability**: Caches prices to reduce API usage
- **Data Persistence**: Securely stores your purchase history

## 📊 Saudi Gold Investment Tracking

Keep track of your gold investments in Saudi Arabia with these powerful features:

- Enter purchase details (date, price per gram in SAR, weight in grams)
- See current value of each gold purchase in Saudi Riyal
- Calculate profit/loss percentage on each investment
- View total portfolio value and overall profit/loss in SAR
- Get historical Saudi gold prices with one click

## 🚀 Quick Start

### Docker (Recommended)

```bash
# Pull the latest image
docker pull ghcr.io/muhssamy/gold-tracker:latest

# Run with your GoldAPI key
docker run -d -p 8080:8080 \
  -e GOLD_API_KEY=your_api_key_here \
  -v gold_data:/app/data \
  --name gold-tracker \
  ghcr.io/muhssamy/gold-tracker:latest
```

### Using Docker Compose

Create a `.env` file with your GoldAPI key:

```
GOLD_API_KEY=your_api_key_here
```

Then run:

```bash
docker-compose -f docker-compose.example.yml up -d
```

## 🛠️ Development

### Prerequisites

- Python 3.9+
- Poetry (dependency management)
- GoldAPI.io API key

### Setup

```bash
# Clone repository
git clone https://github.com/muhssamy/gold-tracker.git
cd gold-tracker

# Install dependencies
poetry install

# Run application
export GOLD_API_KEY=your_api_key_here
poetry run python app.py
```


## 🔒 Security

- API keys are stored as environment variables, never in the codebase
- Secure session management with random secret key
- Data is stored locally in your Docker volume

## 🇸🇦 Saudi Gold Market Information

The Gold Price Tracker provides insights into the Saudi Arabian gold market:

- 24k, 22k, 21k gold price tracking in Saudi Riyal
- Real-time updates from reliable gold price sources
- Historical Saudi gold price trends
- USD to SAR conversion for international comparison

## 📄 License

MIT

## 🔗 Related Resources

- [Saudi Gold Price Information](https://www.goldprice.org/gold-price-saudi-arabia.html)
- [GoldAPI Documentation](https://www.goldapi.io/documentation)
- [Saudi Riyal Exchange Rates](https://www.sama.gov.sa/en-us/indicators/pages/saibor.aspx)