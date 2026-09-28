"""
DEDAN Health 2.0 - Pricing Models and Billing System
World-class pricing with 14-day free trial, Ethiopia bank + global payments
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
import json
import uuid
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class PricingTier(str, Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    FREEMIUM = "freemium"

class SubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    EXPIRED = "expired"

class PaymentMethod(str, Enum):
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    MOBILE_WALLET = "mobile_wallet"
    ONLINE_BANKING = "online_banking"

class Currency(str, Enum):
    USD = "USD"
    ETB = "ETB"  # Ethiopian Birr
    EUR = "EUR"
    GBP = "GBP"

# Pricing Configuration
PRICING_CONFIG = {
    "clinic_tiers": {
        PricingTier.STARTER: {
            "name": "Starter Clinic",
            "price_range": {"min": 75, "max": 150, "currency": Currency.USD},
            "billing_cycle": "monthly",
            "features": [
                "Basic DEDAN triage",
                "Safety-Guard AI",
                "WhatsApp/SMS gateway",
                "Clinic Console (up to 2 staff)",
                "1,000 triages/month",
                "Email support"
            ],
            "limits": {
                "staff_users": 2,
                "triages_per_month": 1000,
                "api_calls_per_month": 5000,
                "storage_gb": 10
            }
        },
        PricingTier.PROFESSIONAL: {
            "name": "Professional Clinic",
            "price_range": {"min": 250, "max": 500, "currency": Currency.USD},
            "billing_cycle": "monthly",
            "features": [
                "All Starter features",
                "Risk-Prediction AI",
                "Chronic-Care Coach",
                "Higher usage limit (~10,000 triages/month)",
                "Priority email support",
                "Advanced analytics",
                "Multi-language support"
            ],
            "limits": {
                "staff_users": 10,
                "triages_per_month": 10000,
                "api_calls_per_month": 50000,
                "storage_gb": 50
            }
        },
        PricingTier.ENTERPRISE: {
            "name": "Enterprise Clinic",
            "price_range": {"min": 1000, "max": 3000, "currency": Currency.USD},
            "billing_cycle": "monthly",
            "features": [
                "All Professional features",
                "Image-Analysis AI",
                "Explainability AI",
                "Bias-Monitoring",
                "Multi-clinic hub",
                "API access",
                "Dedicated support",
                "Custom integrations",
                "White-label options"
            ],
            "limits": {
                "staff_users": -1,  # Unlimited
                "triages_per_month": -1,  # Unlimited
                "api_calls_per_month": -1,  # Unlimited
                "storage_gb": -1  # Unlimited
            }
        },
        PricingTier.FREEMIUM: {
            "name": "Freemium",
            "price_range": {"min": 0, "max": 0, "currency": Currency.USD},
            "billing_cycle": "monthly",
            "features": [
                "Basic triage (limited)",
                "Emergency detection",
                "WhatsApp access"
            ],
            "limits": {
                "staff_users": 1,
                "triages_per_month": 100,
                "api_calls_per_month": 1000,
                "storage_gb": 1
            }
        }
    },
    "api_pricing": {
        "triage_api": {
            "per_call_range": {"min": 0.10, "max": 0.25, "currency": Currency.USD},
            "monthly_minimums": {
                "small": 100,
                "medium": 750,  # Average of 500-1000
                "large": 3500   # Average of 2000-5000
            }
        },
        "risk_api": {
            "per_call_range": {"min": 0.15, "max": 0.40, "currency": Currency.USD},
            "monthly_minimums": {
                "small": 100,
                "medium": 750,
                "large": 3500
            }
        }
    },
    "patient_pricing": {
        "freemium": {
            "price": 0,
            "features": ["Basic triage forever", "Emergency detection"]
        },
        "pro_trial": {
            "duration_days": 14,
            "features": ["Chronic-care tracking", "Risk analytics", "Health insights"]
        },
        "pro_subscription": {
            "price_range": {"min": 2, "max": 5, "currency": Currency.USD},
            "billing_cycle": "monthly",
            "features": ["All pro trial features", "Unlimited health tracking", "Personalized insights"]
        }
    },
    "trial_config": {
        "clinic_trial_days": 14,
        "api_trial_days": 14,
        "patient_pro_trial_days": 14,
        "auto_downgrade_enabled": True,
        "trial_tier": PricingTier.PROFESSIONAL
    }
}

# Database Models
class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String, ForeignKey('clinics.id'), nullable=False)
    tier = Column(String, nullable=False)  # PricingTier
    status = Column(String, nullable=False)  # SubscriptionStatus
    price = Column(Float, nullable=False)
    currency = Column(String, nullable=False)  # Currency
    billing_cycle = Column(String, nullable=False)  # monthly, yearly
    started_at = Column(DateTime, default=datetime.utcnow)
    trial_ends_at = Column(DateTime, nullable=True)
    current_period_ends_at = Column(DateTime, nullable=False)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    clinic = relationship("Clinic", back_populates="subscriptions")
    invoices = relationship("Invoice", back_populates="subscription")
    payment_methods = relationship("PaymentMethod", back_populates="subscription")
    
    def is_trial_active(self):
        return self.status == SubscriptionStatus.TRIAL and self.trial_ends_at and datetime.utcnow() < self.trial_ends_at
    
    def is_active(self):
        return self.status == SubscriptionStatus.ACTIVE
    
    def days_until_trial_end(self):
        if not self.trial_ends_at:
            return 0
        return max(0, (self.trial_ends_at - datetime.utcnow()).days)
    
    def days_until_next_payment(self):
        return max(0, (self.current_period_ends_at - datetime.utcnow()).days)

class Invoice(Base):
    __tablename__ = 'invoices'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id = Column(String, ForeignKey('subscriptions.id'), nullable=False)
    invoice_number = Column(String, unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    status = Column(String, nullable=False)  # draft, pending, paid, failed, cancelled
    due_date = Column(DateTime, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # PDF storage
    pdf_url = Column(String, nullable=True)
    
    # Relationships
    subscription = relationship("Subscription", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice")

class Payment(Base):
    __tablename__ = 'payments'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = Column(String, ForeignKey('invoices.id'), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    method = Column(String, nullable=False)  # PaymentMethod
    status = Column(String, nullable=False)  # pending, completed, failed, refunded
    gateway_transaction_id = Column(String, nullable=True)
    gateway_response = Column(JSON, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="payments")

class PaymentMethod(Base):
    __tablename__ = 'payment_methods'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String, ForeignKey('clinics.id'), nullable=False)
    subscription_id = Column(String, ForeignKey('subscriptions.id'), nullable=True)
    method_type = Column(String, nullable=False)  # PaymentMethod
    is_default = Column(Boolean, default=False)
    
    # Card details (stored as tokens from payment gateway)
    gateway_token = Column(String, nullable=True)  # Never store raw card data
    last_four = Column(String, nullable=True)
    expiry_month = Column(Integer, nullable=True)
    expiry_year = Column(Integer, nullable=True)
    card_brand = Column(String, nullable=True)
    
    # Bank transfer details
    bank_name = Column(String, nullable=True)
    account_number_hash = Column(String, nullable=True)  # Hashed for security
    account_holder = Column(String, nullable=True)
    
    # Mobile wallet details
    wallet_provider = Column(String, nullable=True)
    wallet_phone = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    clinic = relationship("Clinic", back_populates="payment_methods")
    subscription = relationship("Subscription", back_populates="payment_methods")

class BillingAuditLog(Base):
    __tablename__ = 'billing_audit_logs'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String, ForeignKey('clinics.id'), nullable=False)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    action = Column(String, nullable=False)  # created, updated, cancelled, upgraded, downgraded
    resource_type = Column(String, nullable=False)  # subscription, payment_method, invoice
    resource_id = Column(String, nullable=False)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    clinic = relationship("Clinic")
    user = relationship("User")

# Pydantic Models for API
class SubscriptionRequest(BaseModel):
    tier: PricingTier
    billing_cycle: str = "monthly"
    payment_method_id: Optional[str] = None

class SubscriptionResponse(BaseModel):
    id: str
    tier: PricingTier
    status: SubscriptionStatus
    price: float
    currency: Currency
    trial_ends_at: Optional[datetime]
    current_period_ends_at: datetime
    days_until_trial_end: int
    days_until_next_payment: int
    features: List[str]
    limits: Dict[str, Any]

class PricingInfo(BaseModel):
    tier: PricingTier
    name: str
    price_range: Dict[str, Any]
    features: List[str]
    limits: Dict[str, Any]
    is_popular: bool = False
    trial_available: bool = True

class PaymentMethodRequest(BaseModel):
    method_type: PaymentMethod
    # For card payments (tokenized)
    gateway_token: Optional[str] = None
    # For bank transfers
    bank_name: Optional[str] = None
    account_holder: Optional[str] = None
    # For mobile wallets
    wallet_provider: Optional[str] = None
    wallet_phone: Optional[str] = None

class PaymentMethodResponse(BaseModel):
    id: str
    method_type: PaymentMethod
    is_default: bool
    display_name: str
    # Card info
    last_four: Optional[str] = None
    card_brand: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    # Bank info
    bank_name: Optional[str] = None
    # Wallet info
    wallet_provider: Optional[str] = None

class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    amount: float
    currency: Currency
    status: str
    due_date: datetime
    pdf_url: Optional[str] = None

# Ethiopia Bank Configuration
ETHIOPIA_BANK_CONFIG = {
    "commercial_bank_of_ethiopia": {
        "name": "Commercial Bank of Ethiopia",
        "account_name": "DEDAN Health PLC",
        "account_number": "1000123456789",
        "branch": "Addis Ababa Main Branch",
        "swift_code": "CBETETAA"
    },
    "awash_bank": {
        "name": "Awash Bank",
        "account_name": "DEDAN Health PLC",
        "account_number": "2000123456789",
        "branch": "Addis Ababa HQ",
        "swift_code": "AWASETAA"
    },
    "dashen_bank": {
        "name": "Dashen Bank",
        "account_name": "DEDAN Health PLC",
        "account_number": "3000123456789",
        "branch": "Bole Branch",
        "swift_code": "DSHEETAA"
    }
}

# Payment Gateway Configuration
PAYMENT_GATEWAY_CONFIG = {
    "stripe": {
        "publishable_key": "pk_test_...",  # Environment-specific
        "secret_key": "sk_test_...",       # Environment-specific
        "webhook_secret": "whsec_...",     # Environment-specific
        "supported_methods": [PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD]
    },
    "paypal": {
        "client_id": "...",                # Environment-specific
        "client_secret": "...",            # Environment-specific
        "webhook_id": "...",               # Environment-specific
        "supported_methods": [PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD, PaymentMethod.ONLINE_BANKING]
    },
    "mobile_money": {
        "ethiopia": {
            "telebirr": {
                "api_key": "...",
                "merchant_id": "...",
                "supported_methods": [PaymentMethod.MOBILE_WALLET]
            }
        }
    }
}

# Pricing Calculator
class PricingCalculator:
    """Calculate pricing based on usage and tier"""
    
    @staticmethod
    def calculate_subscription_price(tier: PricingTier, customizations: Dict[str, Any] = None) -> Dict[str, Any]:
        """Calculate subscription price with customizations"""
        tier_config = PRICING_CONFIG["clinic_tiers"][tier]
        price_range = tier_config["price_range"]
        
        base_price = price_range["min"]
        
        # Add customization costs
        if customizations:
            # Additional staff users
            extra_staff = customizations.get("extra_staff_users", 0)
            if extra_staff > 0 and tier_config["limits"]["staff_users"] != -1:
                base_price += extra_staff * 25  # $25 per additional staff
            
            # Additional storage
            extra_storage = customizations.get("extra_storage_gb", 0)
            if extra_storage > 0 and tier_config["limits"]["storage_gb"] != -1:
                base_price += extra_storage * 5  # $5 per additional GB
            
            # Additional API calls
            extra_api_calls = customizations.get("extra_api_calls", 0)
            if extra_api_calls > 0 and tier_config["limits"]["api_calls_per_month"] != -1:
                base_price += (extra_api_calls / 1000) * 0.01  # $0.01 per 1000 extra calls
        
        # Ensure price is within tier range
        max_price = price_range["max"]
        if max_price > 0:
            base_price = min(base_price, max_price)
        
        return {
            "base_price": base_price,
            "currency": price_range["currency"],
            "billing_cycle": tier_config["billing_cycle"],
            "customizations": customizations or {}
        }
    
    @staticmethod
    def calculate_api_cost(api_type: str, usage: int, tier: str = "small") -> Dict[str, Any]:
        """Calculate API usage cost"""
        api_config = PRICING_CONFIG["api_pricing"][api_type]
        per_call_range = api_config["per_call_range"]
        monthly_minimum = api_config["monthly_minimums"][tier]
        
        # Use mid-range for calculation
        per_call_price = (per_call_range["min"] + per_call_range["max"]) / 2
        usage_cost = usage * per_call_price
        
        # Apply monthly minimum
        total_cost = max(usage_cost, monthly_minimum)
        
        return {
            "usage_cost": usage_cost,
            "monthly_minimum": monthly_minimum,
            "total_cost": total_cost,
            "currency": per_call_range["currency"],
            "per_call_price": per_call_price
        }

# Trial Manager
class TrialManager:
    """Manage free trials and automatic downgrades"""
    
    @staticmethod
    def start_trial(clinic_id: str, tier: PricingTier = PricingTier.PROFESSIONAL) -> Dict[str, Any]:
        """Start a free trial for a clinic"""
        trial_days = PRICING_CONFIG["trial_config"]["clinic_trial_days"]
        trial_ends = datetime.utcnow() + timedelta(days=trial_days)
        
        return {
            "clinic_id": clinic_id,
            "tier": tier,
            "status": SubscriptionStatus.TRIAL,
            "trial_ends_at": trial_ends,
            "current_period_ends_at": trial_ends,
            "auto_downgrade_enabled": PRICING_CONFIG["trial_config"]["auto_downgrade_enabled"]
        }
    
    @staticmethod
    def check_trial_expiry(subscription: Subscription) -> bool:
        """Check if trial has expired and handle downgrade"""
        if not subscription.is_trial_active():
            return False
        
        if subscription.trial_ends_at and datetime.utcnow() >= subscription.trial_ends_at:
            if PRICING_CONFIG["trial_config"]["auto_downgrade_enabled"]:
                # Auto-downgrade to freemium
                subscription.tier = PricingTier.FREEMIUM
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.current_period_ends_at = datetime.utcnow() + timedelta(days=30)
                return True
            else:
                # Suspend subscription
                subscription.status = SubscriptionStatus.SUSPENDED
                return True
        
        return False

# Export configurations
def get_pricing_tiers() -> List[PricingInfo]:
    """Get all pricing tiers for frontend display"""
    tiers = []
    
    for tier, config in PRICING_CONFIG["clinic_tiers"].items():
        if tier == PricingTier.FREEMIUM:
            continue  # Skip freemium in pricing page
        
        pricing_info = PricingInfo(
            tier=tier,
            name=config["name"],
            price_range=config["price_range"],
            features=config["features"],
            limits=config["limits"],
            is_popular=(tier == PricingTier.PROFESSIONAL),
            trial_available=True
        )
        tiers.append(pricing_info)
    
    return tiers

def get_ethiopia_banks() -> Dict[str, Any]:
    """Get Ethiopia bank configuration for payments"""
    return ETHIOPIA_BANK_CONFIG

def get_payment_gateways() -> Dict[str, Any]:
    """Get payment gateway configuration"""
    return PAYMENT_GATEWAY_CONFIG
