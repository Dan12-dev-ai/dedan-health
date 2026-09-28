"""
DEDAN Health 2.0 - Billing API Endpoints
RESTful billing endpoints with security, audit logs, and RBAC
"""

from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

from pricing_models import (
    Subscription, SubscriptionRequest, SubscriptionResponse,
    PaymentMethodRequest, PaymentMethodResponse, InvoiceResponse,
    PricingTier, SubscriptionStatus, get_pricing_tiers, get_ethiopia_banks
)
from billing_system import BillingSystem
from database_security import DatabaseManager, security_manager

logger = logging.getLogger(__name__)
security = HTTPBearer()
router = APIRouter(prefix="/billing", tags=["billing"])

# Dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Get current authenticated user"""
    try:
        # Verify JWT token
        payload = security_manager.decode_jwt(credentials.credentials)
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

async def check_billing_permission(user: Dict[str, Any]):
    """Check if user has billing permission"""
    if user.get('role') not in ['admin', 'clinic_staff', 'owner']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for billing operations"
        )

# Initialize billing system
billing_system = BillingSystem()

@router.get("/pricing-tiers")
async def get_pricing_tiers_endpoint():
    """Get all available pricing tiers"""
    try:
        tiers = get_pricing_tiers()
        return {
            "status": "success",
            "data": tiers,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get pricing tiers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pricing tiers"
        )

@router.get("/ethiopia-banks")
async def get_ethiopia_banks_endpoint():
    """Get Ethiopia bank configuration for payments"""
    try:
        banks = get_ethiopia_banks()
        return {
            "status": "success",
            "data": banks,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get Ethiopia banks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bank information"
        )

@router.post("/start-trial", response_model=SubscriptionResponse)
async def start_trial(
    request: SubscriptionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: None = Depends(check_billing_permission)
):
    """Start a 14-day free trial"""
    try:
        subscription = await billing_system.create_subscription(
            clinic_id=current_user['clinic_id'],
            request=request,
            user_id=current_user['user_id'],
            ip_address="api_request",
            user_agent="api_client"
        )
        
        return {
            "status": "success",
            "data": subscription,
            "message": "14-day free trial started successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start trial: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start trial"
        )

@router.get("/current-subscription", response_model=SubscriptionResponse)
async def get_current_subscription(
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: None = Depends(check_billing_permission)
):
    """Get current subscription details"""
    try:
        async with billing_system.db_manager.get_connection() as conn:
            subscription = await conn.execute("""
                SELECT * FROM subscriptions 
                WHERE clinic_id = $1 AND status IN ('trial', 'active')
                ORDER BY created_at DESC LIMIT 1
            """, current_user['clinic_id']).fetchone()
            
            if not subscription:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No active subscription found"
                )
            
            subscription_response = await billing_system._get_subscription_details(
                conn, subscription['id']
            )
            
            return {
                "status": "success",
                "data": subscription_response,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription"
        )

@router.post("/upgrade-subscription", response_model=SubscriptionResponse)
async def upgrade_subscription(
    request: SubscriptionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: None = Depends(check_billing_permission)
):
    """Upgrade subscription from trial to paid plan"""
    try:
        # Get current subscription
        async with billing_system.db_manager.get_connection() as conn:
            current_sub = await conn.execute("""
                SELECT * FROM subscriptions 
                WHERE clinic_id = $1 AND status = 'trial'
                ORDER BY created_at DESC LIMIT 1
            """, current_user['clinic_id']).fetchone()
            
            if not current_sub:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No active trial found"
                )
            
            # Create new subscription
            new_subscription = await billing_system.create_subscription(
                clinic_id=current_user['clinic_id'],
                request=request,
                user_id=current_user['user_id'],
                ip_address="api_request",
                user_agent="api_client"
            )
            
            # Cancel old trial
            await conn.execute("""
                UPDATE subscriptions 
                SET status = 'cancelled', cancelled_at = $1 
                WHERE id = $2
            """, datetime.utcnow(), current_sub['id'])
            
            return {
                "status": "success",
                "data": new_subscription,
                "message": "Subscription upgraded successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upgrade subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upgrade subscription"
        )

@router.post("/payment-methods", response_model=PaymentMethodResponse)
async def add_payment_method(
    request: PaymentMethodRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: None = Depends(check_billing_permission)
):
    """Add payment method for clinic"""
    try:
        payment_method = await billing_system.add_payment_method(
            clinic_id=current_user['clinic_id'],
            request=request,
            user_id=current_user['user_id'],
            ip_address="api_request",
            user_agent="api_client"
        )
        
        return {
            "status": "success",
            "data": payment_method,
            "message": "Payment method added successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add payment method: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add payment method"
        )

@router.get("/payment-methods", response_model=List[PaymentMethodResponse])
async def get_payment_methods(
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: None = Depends(check_billing_permission)
):
    """Get all payment methods for clinic"""
    try:
        async with billing_system.db_manager.get_connection() as conn:
            payment_methods = await conn.execute("""
                SELECT * FROM payment_methods 
                WHERE clinic_id = $1 
                ORDER BY created_at DESC
            """, current_user['clinic_id']).fetchall()
            
            methods = []
            for pm in payment_methods:
                method_response = await billing_system._get_payment_method_details(
                    conn, pm['id']
                )
                methods.append(method_response)
            
            return {
                "status": "success",
                "data": methods,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get payment methods: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment methods"
        )

@router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(
    amount: float,
    currency: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: None = Depends(check_billing_permission)
):
    """Create invoice for current subscription"""
    try:
        # Get current subscription
        async with billing_system.db_manager.get_connection() as conn:
            subscription = await conn.execute("""
                SELECT * FROM subscriptions 
                WHERE clinic_id = $1 AND status = 'active'
                ORDER BY created_at DESC LIMIT 1
            """, current_user['clinic_id']).fetchone()
            
            if not subscription:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No active subscription found"
                )
            
            # Create invoice
            invoice = await billing_system.create_invoice(
                subscription_id=subscription['id'],
                amount=amount,
                currency=currency,
                due_date=datetime.utcnow() + timedelta(days=30),
                user_id=current_user['user_id']
            )
            
            return {
                "status": "success",
                "data": invoice,
                "message": "Invoice created successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create invoice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create invoice"
        )

@router.get("/invoices", response_model=List[InvoiceResponse])
async def get_invoices(
    limit: int = 10,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: None = Depends(check_billing_permission)
):
    """Get invoices for clinic"""
    try:
        async with billing_system.db_manager.get_connection() as conn:
            invoices = await conn.execute("""
                SELECT i.* FROM invoices i
                JOIN subscriptions s ON i.subscription_id = s.id
                WHERE s.clinic_id = $1
                ORDER BY i.created_at DESC
                LIMIT $2 OFFSET $3
            """, current_user['clinic_id'], limit, offset).fetchall()
            
            invoice_responses = []
            for invoice in invoices:
                invoice_response = await billing_system._get_invoice_details(
                    conn, invoice['id']
                )
                invoice_responses.append(invoice_response)
            
            return {
                "status": "success",
                "data": invoice_responses,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get invoices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invoices"
        )

@router.post("/process-payment")
async def process_payment(
    invoice_id: str,
    payment_method_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: None = Depends(check_billing_permission)
):
    """Process payment for invoice"""
    try:
        result = await billing_system.process_payment(
            invoice_id=invoice_id,
            payment_method_id=payment_method_id,
            user_id=current_user['user_id'],
            ip_address="api_request"
        )
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process payment"
        )

@router.post("/webhook/stripe")
async def stripe_webhook(request: Dict[str, Any]):
    """Handle Stripe webhook events"""
    try:
        result = await billing_system.handle_webhook(request, "stripe")
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to handle Stripe webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )

@router.post("/webhook/paypal")
async def paypal_webhook(request: Dict[str, Any]):
    """Handle PayPal webhook events"""
    try:
        result = await billing_system.handle_webhook(request, "paypal")
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to handle PayPal webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )

@router.get("/usage-stats")
async def get_usage_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: None = Depends(check_billing_permission)
):
    """Get usage statistics for current billing period"""
    try:
        # Get current subscription
        async with billing_system.db_manager.get_connection() as conn:
            subscription = await conn.execute("""
                SELECT * FROM subscriptions 
                WHERE clinic_id = $1 AND status IN ('trial', 'active')
                ORDER BY created_at DESC LIMIT 1
            """, current_user['clinic_id']).fetchone()
            
            if not subscription:
                return {
                    "status": "success",
                    "data": {
                        "triages_used": 0,
                        "triages_limit": 100,
                        "api_calls_used": 0,
                        "api_calls_limit": 1000,
                        "storage_used": 0,
                        "storage_limit": 1,
                        "period_start": datetime.utcnow().isoformat(),
                        "period_end": datetime.utcnow().isoformat()
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Get usage statistics (mock implementation)
            # In production, this would query actual usage data
            usage_stats = {
                "triages_used": 245,
                "triages_limit": subscription['tier'] == 'starter' ? 1000 : (subscription['tier'] == 'professional' ? 10000 : -1),
                "api_calls_used": 1234,
                "api_calls_limit": subscription['tier'] == 'starter' ? 5000 : (subscription['tier'] == 'professional' ? 50000 : -1),
                "storage_used": 2.3,
                "storage_limit": subscription['tier'] == 'starter' ? 10 : (subscription['tier'] == 'professional' ? 50 : -1),
                "period_start": subscription['started_at'],
                "period_end": subscription['current_period_ends_at']
            }
            
            return {
                "status": "success",
                "data": usage_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics"
        )

@router.post("/cancel-subscription")
async def cancel_subscription(
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: None = Depends(check_billing_permission)
):
    """Cancel current subscription"""
    try:
        async with billing_system.db_manager.get_connection() as conn:
            subscription = await conn.execute("""
                SELECT * FROM subscriptions 
                WHERE clinic_id = $1 AND status IN ('trial', 'active')
                ORDER BY created_at DESC LIMIT 1
            """, current_user['clinic_id']).fetchone()
            
            if not subscription:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No active subscription found"
                )
            
            # Cancel subscription
            await conn.execute("""
                UPDATE subscriptions 
                SET status = 'cancelled', cancelled_at = $1 
                WHERE id = $2
            """, datetime.utcnow(), subscription['id'])
            
            # Log audit trail
            await billing_system._log_billing_action(
                clinic_id=current_user['clinic_id'],
                user_id=current_user['user_id'],
                action="cancelled",
                resource_type="subscription",
                resource_id=subscription['id'],
                old_values={"status": subscription['status']},
                new_values={"status": "cancelled"},
                ip_address="api_request",
                user_agent="api_client"
            )
            
            return {
                "status": "success",
                "message": "Subscription cancelled successfully",
                "data": {
                    "cancelled_at": datetime.utcnow().isoformat(),
                    "access_until": subscription['current_period_ends_at']
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )

@router.get("/billing-history")
async def get_billing_history(
    limit: int = 50,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: None = Depends(check_billing_permission)
):
    """Get billing history for clinic"""
    try:
        async with billing_system.db_manager.get_connection() as conn:
            # Get audit logs
            audit_logs = await conn.execute("""
                SELECT * FROM billing_audit_logs
                WHERE clinic_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """, current_user['clinic_id'], limit, offset).fetchall()
            
            # Get payments
            payments = await conn.execute("""
                SELECT p.*, i.invoice_number, i.amount, i.currency
                FROM payments p
                JOIN invoices i ON p.invoice_id = i.id
                JOIN subscriptions s ON i.subscription_id = s.id
                WHERE s.clinic_id = $1
                ORDER BY p.created_at DESC
                LIMIT $2 OFFSET $3
            """, current_user['clinic_id'], limit, offset).fetchall()
            
            return {
                "status": "success",
                "data": {
                    "audit_logs": [dict(log) for log in audit_logs],
                    "payments": [dict(payment) for payment in payments]
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get billing history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve billing history"
        )
