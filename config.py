"""
Configuration Management
Centralized config for all components
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration"""
    
    # ==================== APP SETTINGS ====================
    APP_NAME = "Restaurant E-Commerce"
    VERSION = "1.0.0"
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # ==================== DATABASE ====================
    # MongoDB Connection
    # For local: mongodb://localhost:27017/
    # For Atlas: mongodb+srv://username:password@cluster.mongodb.net/
    MONGODB_URI = os.getenv(
        'MONGODB_URI',
        'mongodb://localhost:27017/'  # Default to local
    )
    DATABASE_NAME = "restaurant_commerce"
    
    # ==================== AI API KEYS ====================
    # NEW: Google Gemini (Primary - FREE TIER AVAILABLE!)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    
    # Legacy: Groq AI (kept for backward compatibility)
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    
    # AI Provider Selection ('gemini' or 'groq')
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini').lower()
    
    # Model Configuration
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'models/gemini-2.5-flash')  # or 'models/gemini-1.5-pro-latest'
    GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
    
    # Agentic Features
    ENABLE_AGENTIC_MODE = os.getenv('ENABLE_AGENTIC_MODE', 'True').lower() == 'true'
    ENABLE_AUTO_ADD_TO_CART = os.getenv('ENABLE_AUTO_ADD_TO_CART', 'True').lower() == 'true'
    ENABLE_MEAL_PLANNING = os.getenv('ENABLE_MEAL_PLANNING', 'True').lower() == 'true'
    
    # API Key for webhook authentication
    API_KEY = os.getenv('API_KEY', 'change_this_in_production_xyz123')
    
    # ==================== PAYMENT GATEWAYS ====================
    # JazzCash Configuration
    JAZZCASH_MERCHANT_ID = os.getenv('JAZZCASH_MERCHANT_ID', 'MC12345')
    JAZZCASH_PASSWORD = os.getenv('JAZZCASH_PASSWORD', 'your_password')
    JAZZCASH_INTEGRITY_SALT = os.getenv('JAZZCASH_INTEGRITY_SALT', 'your_salt')
    JAZZCASH_RETURN_URL = os.getenv('JAZZCASH_RETURN_URL', 'http://localhost:8501/payment/callback')
    
    # Payment Gateway URLs
    JAZZCASH_SANDBOX_URL = "https://sandbox.jazzcash.com.pk/CustomerPortal/transactionmanagement/merchantform/"
    JAZZCASH_PRODUCTION_URL = "https://payments.jazzcash.com.pk/CustomerPortal/transactionmanagement/merchantform/"
    
    # Use sandbox or production
    USE_PAYMENT_SANDBOX = os.getenv('USE_PAYMENT_SANDBOX', 'True').lower() == 'true'
    
    # ==================== SERVER SETTINGS ====================
    # Flask webhook server
    WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', '0.0.0.0')
    WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', 5000))
    
    # Streamlit UI
    STREAMLIT_PORT = int(os.getenv('STREAMLIT_PORT', 8501))
    
    # Base URLs
    API_BASE_URL = os.getenv('API_BASE_URL', f'http://localhost:{WEBHOOK_PORT}')
    APP_BASE_URL = os.getenv('APP_BASE_URL', f'http://localhost:{STREAMLIT_PORT}')
    
    # ==================== BUSINESS SETTINGS ====================
    # Restaurant Details
    RESTAURANT_NAME = os.getenv('RESTAURANT_NAME', 'Flavor Fusion Restaurant')
    RESTAURANT_PHONE = os.getenv('RESTAURANT_PHONE', '+92 300 123 4567')
    RESTAURANT_EMAIL = os.getenv('RESTAURANT_EMAIL', 'info@flavorfusion.com')
    RESTAURANT_ADDRESS = os.getenv('RESTAURANT_ADDRESS', 'Main Street, Karachi')
    
    # Pricing
    CURRENCY = "PKR"
    TAX_RATE = float(os.getenv('TAX_RATE', 0.05))  # 5%
    DELIVERY_FEE = float(os.getenv('DELIVERY_FEE', 50))  # Rs 50
    FREE_DELIVERY_THRESHOLD = float(os.getenv('FREE_DELIVERY_THRESHOLD', 1500))  # Free above Rs 1500
    
    # Order Settings
    ORDER_TIMEOUT_MINUTES = int(os.getenv('ORDER_TIMEOUT_MINUTES', 15))  # Payment timeout
    MAX_ORDER_ITEMS = int(os.getenv('MAX_ORDER_ITEMS', 50))
    MIN_ORDER_AMOUNT = float(os.getenv('MIN_ORDER_AMOUNT', 100))
    
    # ==================== FEATURES FLAGS ====================
    # Enable/disable features
    ENABLE_PAYMENTS = os.getenv('ENABLE_PAYMENTS', 'True').lower() == 'true'
    ENABLE_ANALYTICS = os.getenv('ENABLE_ANALYTICS', 'True').lower() == 'true'
    ENABLE_WHATSAPP = os.getenv('ENABLE_WHATSAPP', 'False').lower() == 'true'
    ENABLE_EMAIL_NOTIFICATIONS = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'False').lower() == 'true'
    
    # ==================== WHATSAPP (Future) ====================
    WHATSAPP_BUSINESS_PHONE = os.getenv('WHATSAPP_BUSINESS_PHONE', '')
    WHATSAPP_API_TOKEN = os.getenv('WHATSAPP_API_TOKEN', '')
    WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN', '')
    
    # ==================== SECURITY ====================
    # Rate limiting
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'True').lower() == 'true'
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 60))
    
    # Session settings
    SESSION_TIMEOUT_MINUTES = int(os.getenv('SESSION_TIMEOUT_MINUTES', 30))
    
    # ==================== LOGGING ====================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    
    # ==================== HELPERS ====================
    
    @classmethod
    def get_jazzcash_url(cls):
        """Get JazzCash URL based on environment"""
        return cls.JAZZCASH_SANDBOX_URL if cls.USE_PAYMENT_SANDBOX else cls.JAZZCASH_PRODUCTION_URL
    
    @classmethod
    def get_delivery_fee(cls, order_total: float) -> float:
        """Calculate delivery fee"""
        if order_total >= cls.FREE_DELIVERY_THRESHOLD:
            return 0
        return cls.DELIVERY_FEE
    
    @classmethod
    def calculate_tax(cls, amount: float) -> float:
        """Calculate tax amount"""
        return round(amount * cls.TAX_RATE, 2)
    
    @classmethod
    def get_ai_api_key(cls) -> str:
        """Get API key based on selected provider"""
        if cls.AI_PROVIDER == 'gemini':
            return cls.GEMINI_API_KEY
        elif cls.AI_PROVIDER == 'groq':
            return cls.GROQ_API_KEY
        return ''
    
    @classmethod
    def get_ai_model(cls) -> str:
        """Get model name based on selected provider"""
        if cls.AI_PROVIDER == 'gemini':
            return cls.GEMINI_MODEL
        elif cls.AI_PROVIDER == 'groq':
            return cls.GROQ_MODEL
        return ''
    
    @classmethod
    def is_configured(cls) -> dict:
        """Check if all critical configs are set"""
        return {
            "gemini_api": bool(cls.GEMINI_API_KEY),
            "groq_api": bool(cls.GROQ_API_KEY),
            "ai_configured": bool(cls.get_ai_api_key()),
            "mongodb": bool(cls.MONGODB_URI),
            "api_key": bool(cls.API_KEY),
            "jazzcash": bool(cls.JAZZCASH_MERCHANT_ID and cls.JAZZCASH_PASSWORD),
        }
    
    @classmethod
    def print_config(cls):
        """Print current configuration (for debugging)"""
        print("=" * 60)
        print("🔧 CONFIGURATION")
        print("=" * 60)
        print(f"App Name: {cls.APP_NAME}")
        print(f"Version: {cls.VERSION}")
        print(f"Debug: {cls.DEBUG}")
        print(f"\n📊 Database:")
        print(f"  MongoDB URI: {cls.MONGODB_URI[:30]}...")
        print(f"\n🤖 AI Configuration:")
        print(f"  Provider: {cls.AI_PROVIDER.upper()}")
        print(f"  Gemini: {'✅ Set' if cls.GEMINI_API_KEY else '❌ Missing'}")
        print(f"  Groq: {'✅ Set' if cls.GROQ_API_KEY else '❌ Missing'}")
        print(f"  Active Model: {cls.get_ai_model()}")
        print(f"  Agentic Mode: {'✅ Enabled' if cls.ENABLE_AGENTIC_MODE else '❌ Disabled'}")
        print(f"  Auto Add to Cart: {'✅' if cls.ENABLE_AUTO_ADD_TO_CART else '❌'}")
        print(f"  Meal Planning: {'✅' if cls.ENABLE_MEAL_PLANNING else '❌'}")
        print(f"\n🔑 API Keys:")
        print(f"  API Key: {'✅ Set' if cls.API_KEY else '❌ Missing'}")
        print(f"\n💳 Payment:")
        print(f"  JazzCash: {'✅ Configured' if cls.JAZZCASH_MERCHANT_ID else '❌ Not configured'}")
        print(f"  Sandbox Mode: {cls.USE_PAYMENT_SANDBOX}")
        print(f"\n🪙 Business:")
        print(f"  Restaurant: {cls.RESTAURANT_NAME}")
        print(f"  Currency: {cls.CURRENCY}")
        print(f"  Tax Rate: {cls.TAX_RATE * 100}%")
        print(f"  Delivery Fee: Rs {cls.DELIVERY_FEE}")
        print(f"\n🌐 Servers:")
        print(f"  Webhook: http://{cls.WEBHOOK_HOST}:{cls.WEBHOOK_PORT}")
        print(f"  Streamlit: http://localhost:{cls.STREAMLIT_PORT}")
        print(f"\n🎛️ Features:")
        print(f"  Payments: {'✅' if cls.ENABLE_PAYMENTS else '❌'}")
        print(f"  Analytics: {'✅' if cls.ENABLE_ANALYTICS else '❌'}")
        print(f"  WhatsApp: {'✅' if cls.ENABLE_WHATSAPP else '❌'}")
        print("=" * 60)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    USE_PAYMENT_SANDBOX = True
    MONGODB_URI = "mongodb://localhost:27017/"
    AI_PROVIDER = "gemini"  # Use Gemini in dev (FREE)


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    USE_PAYMENT_SANDBOX = False
    # Use environment variables for sensitive data
    # Never commit real credentials to git!


# Choose config based on environment
ENV = os.getenv('ENVIRONMENT', 'development').lower()

if ENV == 'production':
    config = ProductionConfig()
else:
    config = DevelopmentConfig()


# Export the active config
__all__ = ['config', 'Config']


if __name__ == '__main__':
    # Test configuration
    config.print_config()
    
    print("\n🧪 Testing helpers:")
    print(f"Delivery fee for Rs 500: Rs {config.get_delivery_fee(500)}")
    print(f"Delivery fee for Rs 2000: Rs {config.get_delivery_fee(2000)}")
    print(f"Tax on Rs 1000: Rs {config.calculate_tax(1000)}")
    print(f"Active AI API Key: {'✅ Set' if config.get_ai_api_key() else '❌ Missing'}")
    print(f"Active AI Model: {config.get_ai_model()}")
    
    print("\n✅ Configuration check:")
    checks = config.is_configured()
    for key, value in checks.items():
        print(f"  {key}: {'✅' if value else '❌'}")