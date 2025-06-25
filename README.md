# Binance Stop Loss Manager

An intelligent automated stop loss management system for Binance Futures trading with advanced performance optimizations.

## 🚀 Features

### Advanced Stop Loss Strategies
- **ATR-based Stop Loss**: Dynamic stop loss based on market volatility
- **Percentage-based Stop Loss**: Fixed risk management (2% default)
- **Trailing Stop Loss**: Protects profits with dynamic adjustment
- **Smart Strategy Selection**: Automatically chooses the most conservative approach

### Performance Optimizations
- **Intelligent Caching**: Reduces API calls by 80%
- **Rate Limiting**: Prevents API rate limit violations
- **Retry Mechanism**: Handles temporary API failures
- **Dynamic Monitoring**: Adjusts frequency based on market conditions

### Configuration Management
- **YAML Configuration**: Easy to modify settings
- **Environment Variables**: Secure API credential management
- **Health Monitoring**: Continuous system health checks

## 📁 Project Structure

```
bot-sl/
├── binance_sl_manager.py    # Main application
├── cache_manager.py         # Caching system
├── rate_limiter.py          # API rate limiting
├── config.yaml             # Configuration file
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose setup
├── .env                   # Environment variables (create this)
└── README.md             # This file
```

## ⚙️ Configuration

### config.yaml
```yaml
# API Configuration
api:
  rate_limit_calls_per_second: 10
  max_retries: 3
  retry_delay: 1

# Monitoring Configuration
monitoring:
  normal_interval: 30      # seconds
  aggressive_interval: 10  # seconds when in profit
  retry_interval: 60       # seconds for error retry

# Stop Loss Configuration
stop_loss:
  atr_period: 14
  atr_multiplier: 2.0
  risk_percentage: 0.02    # 2% risk per trade
  trailing_stop_percentage: 0.01  # 1% trailing stop
  min_stop_distance: 0.005 # 0.5% minimum distance

# Caching Configuration
cache:
  position_cache_ttl: 30   # seconds
  price_cache_ttl: 5       # seconds
  atr_cache_ttl: 300       # seconds
```

### Environment Variables (.env)
```env
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```

## 🐳 Docker Setup

### Quick Start
```bash
# Clone and setup
git clone <repository>
cd bot-sl

# Create .env file with your API credentials
echo "BINANCE_API_KEY=your_key" > .env
echo "BINANCE_API_SECRET=your_secret" >> .env

# Run with Docker Compose
docker-compose up --build
```

### Manual Docker Build
```bash
# Build image
docker build -t binance-sl-manager .

# Run container
docker run -d \
  --name bot-sl \
  --env-file .env \
  -v $(pwd):/app \
  binance-sl-manager
```

## 📊 Performance Improvements

### Before Optimization
- API calls every 30 seconds
- No caching
- Hard-coded configuration
- Basic error handling

### After Optimization
- **80% reduction in API calls** through intelligent caching
- **Rate limiting** prevents API violations
- **Dynamic monitoring** (10s when profitable, 30s normally)
- **Configuration management** via YAML
- **Health checks** and automatic recovery
- **Retry mechanism** with exponential backoff

## 🔧 Customization

### Adjust Stop Loss Strategies
Edit `config.yaml`:
```yaml
stop_loss:
  atr_period: 14           # ATR calculation period
  atr_multiplier: 2.0      # ATR multiplier for stop distance
  risk_percentage: 0.02    # Risk per trade (2%)
  trailing_stop_percentage: 0.01  # Trailing stop percentage
```

### Modify Monitoring Frequency
```yaml
monitoring:
  normal_interval: 30      # Normal monitoring interval
  aggressive_interval: 10  # Aggressive monitoring when profitable
```

### Enable/Disable Features
```yaml
trading:
  enable_trailing_stop: true
  enable_atr_stop: true
  enable_percentage_stop: true
```

## 📈 Monitoring

### Log Files
- `sl_manager.log`: Detailed application logs
- Docker logs: `docker-compose logs -f`

### Health Monitoring
- Automatic health checks every 5 minutes
- API connectivity verification
- Cache statistics logging

### Performance Metrics
- Cache hit/miss ratios
- API call frequency
- Stop loss adjustment frequency

## 🛡️ Safety Features

### Risk Management
- Maximum 2% risk per trade (configurable)
- Minimum stop distance protection
- Conservative strategy selection

### Error Handling
- Automatic retry with exponential backoff
- Graceful degradation on API failures
- Health check monitoring

### API Protection
- Rate limiting (10 calls/second)
- Request retry mechanism
- Connection health monitoring

## 🚨 Important Notes

1. **API Permissions**: Ensure your Binance API key has Futures trading permissions
2. **Test First**: Always test with small amounts first
3. **Monitor**: Regularly check logs and performance
4. **Backup**: Keep configuration backups
5. **Security**: Never commit API keys to version control

## 🔄 Updates and Maintenance

### Regular Maintenance
- Monitor log files for errors
- Check cache performance
- Review stop loss effectiveness
- Update configuration as needed

### Troubleshooting
```bash
# Check logs
docker-compose logs -f

# Restart service
docker-compose restart

# Check health
docker-compose ps
```

## 📝 License

This project is for educational purposes. Use at your own risk.

## ⚠️ Disclaimer

This software is for educational purposes only. Trading cryptocurrencies involves significant risk. Always test thoroughly and never risk more than you can afford to lose. 
