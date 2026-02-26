"""
AMATN Configuration Module
Centralized configuration management with environment variables and Firebase integration
"""
import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, auth
import ccxt

# Load environment variables
load_dotenv()

@dataclass
class ExchangeConfig:
    """Configuration for cryptocurrency exchanges"""
    exchange_id: str
    api_key: str
    secret: str
    enable_rate_limit: bool = True
    timeout: int = 30000
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'exchange_id': self.exchange_id,
            'api_key': self.api_key,
            'secret': self.secret,
            'enable_rate_limit': self.enable_rate_limit,
            'timeout': self.timeout
        }

@dataclass
class FirebaseConfig:
    """Firebase configuration"""
    credentials_path: str
    project_id: str
    database_url: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate Firebase configuration"""
        if not os.path.exists(self.credentials_path):
            logging.error(f"Firebase credentials file not found: {self.credentials_path}")
            return False
        return True

class AMATNConfig:
    """Main configuration manager for AMATN"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._firebase_app = None
        self._firestore_client = None
        
        # Load configuration from environment
        self._load_configuration()
        
    def _load_configuration(self) -> None:
        """Load and validate all configuration parameters"""
        try:
            # Firebase configuration
            self.firebase_config = FirebaseConfig(
                credentials_path=os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json'),
                project_id=os.getenv('FIREBASE_PROJECT_ID', ''),
                database_url=os.getenv('FIREBASE_DATABASE_URL')
            )
            
            # Exchange configurations
            self.exchanges: Dict[str, ExchangeConfig] = {}
            exchange_ids = os.getenv('ENABLED_EXCHANGES', 'binance,coinbasepro,kraken').split(',')
            
            for exchange_id in exchange_ids:
                api_key_var = f"{exchange_id.upper()}_API_KEY"
                secret_var = f"{exchange_id.upper()}_SECRET"
                
                api_key = os.getenv(api_key_var, '')
                secret = os.getenv(secret_var, '')
                
                if api_key and secret:
                    self.exchanges[exchange_id] = ExchangeConfig(
                        exchange_id=exchange_id,
                        api_key=api_key,
                        secret=secret
                    )
            
            # Trading parameters
            self.max_position_size = float(os.getenv('MAX_POSITION_SIZE', '0.1'))
            self.max_daily_loss = float(os.getenv('MAX_DAILY_LOSS', '0.02'))
            self.risk_free_rate = float(os.getenv('RISK_FREE_RATE', '0.02'))
            
            # Data collection parameters
            self.ohlcv_timeframe = os.getenv('OHLCV_TIMEFRAME', '1h')
            self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
            self.retry_delay = int(os.getenv('RETRY_DELAY', '5'))
            
            # Strategy parameters
            self.strategy_eval_period = int(os.getenv('STRATEGY_EVAL_PERIOD', '24'))
            self.min_backtest_period = int(os.getenv('MIN_BACKTEST_PERIOD', '720'))
            
            self.logger.info("Configuration loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
            
    def initialize_firebase(self) -> None:
        """Initialize Firebase connection with error handling"""
        try:
            if not self.firebase_config.validate():
                raise FileNotFoundError("Firebase credentials file not found")
            
            if not firebase_admin._apps:
                cred = credentials.Certificate(self.firebase_config.credentials_path)
                self._firebase_app = firebase_admin.initialize_app(
                    cred,
                    {
                        'projectId': self.firebase_config.project_id,
                        'databaseURL': self.firebase_config.database_url
                    }
                )
                self.logger.info("Firebase initialized successfully")
            else:
                self._firebase_app = firebase_admin.get_app()
                self.logger.info("Firebase already initialized")
                
        except Exception as e:
            self.logger.error(f"Firebase initialization failed: {e}")
            raise
            
    @property
    def firestore_client(self) -> firestore.Client:
        """Get Firestore client with lazy initialization"""
        if self._firestore_client is None:
            if self._firebase_app is None:
                self.initialize_firebase()
            self._firestore_client = firestore.client(self._firebase_app)
        return self._firestore_client
    
    def validate_exchange_config(self, exchange_id: str) -> bool:
        """Validate exchange configuration"""
        if exchange_id not in self.exchanges:
            self.logger.warning(f"Exchange {exchange_id} not configured")
            return False
        
        config = self.exchanges[exchange_id]
        if not config.api_key or not config.secret:
            self.logger.warning(f"Incomplete credentials for {exchange_id}")
            return False
            
        return True

# Global configuration instance
config = AMATNConfig()