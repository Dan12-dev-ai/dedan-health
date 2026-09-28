"""
DEDAN Health 2.0 - WhatsApp Pricing Flow
Text-based pricing interface for Ethiopia and low-bandwidth regions
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from twilio.twilio_messaging_api_client import twilio_client
from fastapi import HTTPException

from pricing_models import (
    PricingTier, SubscriptionStatus, PRICING_CONFIG,
    ETHIOPIA_BANK_CONFIG, get_pricing_tiers
)
from billing_system import BillingSystem

logger = logging.getLogger(__name__)

class WhatsAppPricingFlow:
    """WhatsApp-based pricing flow for Ethiopia and low-bandwidth regions"""
    
    def __init__(self):
        self.billing_system = BillingSystem()
        self.twilio_client = twilio_client
        self.active_sessions = {}  # Track pricing conversations
        
    async def handle_pricing_request(
        self, 
        from_number: str, 
        message: str,
        clinic_id: str = None
    ) -> str:
        """Handle WhatsApp pricing request"""
        
        session = self._get_or_create_session(from_number, clinic_id)
        
        # Process message based on current state
        if session['state'] == 'initial':
            return await self._handle_initial_pricing(session, message)
        elif session['state'] == 'tier_selection':
            return await self._handle_tier_selection(session, message)
        elif session['state'] == 'payment_method':
            return await self._handle_payment_method(session, message)
        elif session['state'] == 'confirmation':
            return await self._handle_confirmation(session, message)
        elif session['state'] == 'bank_transfer':
            return await self._handle_bank_transfer(session, message)
        else:
            return await self._handle_unknown_state(session, message)
    
    def _get_or_create_session(self, phone_number: str, clinic_id: str = None) -> Dict[str, Any]:
        """Get or create pricing conversation session"""
        
        if phone_number not in self.active_sessions:
            self.active_sessions[phone_number] = {
                'phone_number': phone_number,
                'clinic_id': clinic_id,
                'state': 'initial',
                'selected_tier': None,
                'payment_method': None,
                'created_at': datetime.utcnow(),
                'last_activity': datetime.utcnow()
            }
        
        session = self.active_sessions[phone_number]
        session['last_activity'] = datetime.utcnow()
        return session
    
    async def _handle_initial_pricing(self, session: Dict[str, Any], message: str) -> str:
        """Handle initial pricing request"""
        
        # Check if user is asking about pricing
        pricing_keywords = ['price', 'pricing', 'cost', 'plan', 'trial', 'subscribe']
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in pricing_keywords):
            # Show pricing options
            response = await self._generate_pricing_menu()
            session['state'] = 'tier_selection'
            return response
        else:
            # Provide help message
            return (
                "🏥 DEDAN Health Pricing Help\n\n"
                "Reply 'pricing' to see our plans and start your 14-day free trial.\n\n"
                "Available commands:\n"
                "• 'pricing' - View plans and pricing\n"
                "• 'trial' - Start 14-day free trial\n"
                "• 'help' - Show this help message"
            )
    
    async def _generate_pricing_menu(self) -> str:
        """Generate WhatsApp pricing menu"""
        
        response = (
            "🏥 DEDAN Health - Choose Your Plan\n\n"
            "Start with a 14-day FREE trial!\n\n"
        )
        
        # Get pricing tiers
        tiers = get_pricing_tiers()
        
        for i, tier in enumerate(tiers, 1):
            price_range = tier.price_range
            price_text = f"${price_range.min}-{price_range.max}" if price_range.min != price_range.max else f"${price_range.min}"
            
            response += (
                f"{i}. {tier.name}\n"
                f"   💰 {price_text} USD/month\n"
                f"   ✨ {len(tier.features)} features included\n"
                f"   🎯 14-day free trial\n\n"
            )
        
        response += (
            "Reply with number (1-3) to select plan:\n"
            "Example: '2' for Professional Clinic\n\n"
            "🇪🇹 Ethiopia payment options:\n"
            "• Bank transfer (CBE, Awash, Dashen)\n"
            "• Mobile wallet (Telebirr)\n"
            "• International card\n\n"
            "Reply 'help' for more information."
        )
        
        return response
    
    async def _handle_tier_selection(self, session: Dict[str, Any], message: str) -> str:
        """Handle tier selection"""
        
        try:
            # Parse tier selection
            selection = int(message.strip())
            
            if selection < 1 or selection > 3:
                return "❌ Invalid selection. Please reply with 1, 2, or 3."
            
            # Get selected tier
            tiers = get_pricing_tiers()
            selected_tier = tiers[selection - 1]
            
            session['selected_tier'] = selected_tier.tier
            session['state'] = 'payment_method'
            
            # Generate payment method menu
            return await self._generate_payment_method_menu(selected_tier)
            
        except ValueError:
            return "❌ Invalid format. Please reply with a number (1-3)."
    
    async def _generate_payment_method_menu(self, tier) -> str:
        """Generate payment method menu"""
        
        price_range = tier.price_range
        price_text = f"${price_range.min}-{price_range.max}" if price_range.min != price_range.max else f"${price_range.min}"
        
        response = (
            f"🎉 Great choice! {tier.name}\n\n"
            f"💰 Price: {price_text} USD/month\n"
            f"🎯 14-day FREE trial included\n\n"
            f"Choose payment method for after trial:\n\n"
            f"1. 💳 Credit/Debit Card (International)\n"
            f"   • Secure payment via Stripe\n"
            f"   • Visa, Mastercard, Amex\n\n"
            f"2. 🏦 Bank Transfer (Ethiopia)\n"
            f"   • Commercial Bank of Ethiopia\n"
            f"   • Awash Bank\n"
            f"   • Dashen Bank\n\n"
            f"3. 📱 Mobile Wallet (Ethiopia)\n"
            f"   • Telebirr\n"
            f"   • Other mobile money services\n\n"
            f"Reply with number (1-3) to select payment method.\n"
            f"Or reply 'start' to begin your free trial now!"
        )
        
        return response
    
    async def _handle_payment_method(self, session: Dict[str, Any], message: str) -> str:
        """Handle payment method selection"""
        
        message_lower = message.lower().strip()
        
        if message_lower == 'start':
            # Start trial immediately
            return await self._start_trial_immediately(session)
        
        try:
            # Parse payment method selection
            selection = int(message_lower)
            
            if selection < 1 or selection > 3:
                return "❌ Invalid selection. Please reply with 1, 2, or 3, or 'start' to begin trial."
            
            # Map selection to payment method
            payment_methods = {
                1: 'credit_card',
                2: 'bank_transfer',
                3: 'mobile_wallet'
            }
            
            session['payment_method'] = payment_methods[selection]
            
            if selection == 1:
                # Credit card - provide payment link
                session['state'] = 'confirmation'
                return await self._generate_card_payment_confirmation(session)
            elif selection == 2:
                # Bank transfer - show bank details
                session['state'] = 'bank_transfer'
                return await self._generate_bank_transfer_details(session)
            elif selection == 3:
                # Mobile wallet - show wallet options
                session['state'] = 'confirmation'
                return await self._generate_mobile_wallet_confirmation(session)
            
        except ValueError:
            return "❌ Invalid format. Please reply with a number (1-3) or 'start'."
    
    async def _start_trial_immediately(self, session: Dict[str, Any]) -> str:
        """Start trial immediately without payment method selection"""
        
        try:
            # Start trial via billing system
            if not session['clinic_id']:
                return "❌ Clinic ID required. Please contact support."
            
            trial_data = await self.billing_system.create_subscription(
                clinic_id=session['clinic_id'],
                subscription_request={
                    'tier': session['selected_tier'],
                    'billing_cycle': 'monthly'
                },
                user_id='whatsapp_user',
                ip_address='whatsapp',
                user_agent='WhatsApp'
            )
            
            session['state'] = 'trial_started'
            
            return (
                f"🎉 TRIAL STARTED SUCCESSFULLY!\n\n"
                f"✅ Your 14-day free trial has begun!\n"
                f"📅 Trial ends: {trial_data.trial_ends_at.strftime('%B %d, %Y')}\n"
                f"🏥 Plan: {trial_data.tier.title()}\n\n"
                f"You can now use all DEDAN Health features:\n"
                f"• AI-powered triage\n"
                f"• Safety guard system\n"
                f"• Risk prediction\n"
                f"• Chronic care coaching\n\n"
                f"Reply 'features' to see all available features\n"
                f"Reply 'status' to check your trial status\n"
                f"Reply 'help' for more commands"
            )
            
        except Exception as e:
            logger.error(f"Failed to start trial: {e}")
            return "❌ Failed to start trial. Please contact support or try again."
    
    async def _generate_card_payment_confirmation(self, session: Dict[str, Any]) -> str:
        """Generate credit card payment confirmation"""
        
        # Generate payment link (in production, this would be a secure Stripe link)
        payment_link = f"https://dedan.health/pay/whatsapp/{session['phone_number']}"
        
        return (
            f"💳 Credit/Debit Card Payment\n\n"
            f"To complete your subscription setup:\n\n"
            f"🔗 Click payment link: {payment_link}\n\n"
            f"💳 Or visit: dedan.health/billing\n"
            f"📱 Enter your phone number: {session['phone_number']}\n\n"
            f"Your 14-day free trial starts immediately!\n"
            f"Card will only be charged after trial ends.\n\n"
            f"Reply 'started' once you've completed payment setup\n"
            f"Reply 'cancel' to choose different payment method"
        )
    
    async def _generate_bank_transfer_details(self, session: Dict[str, Any]) -> str:
        """Generate Ethiopia bank transfer details"""
        
        # Generate reference code
        reference_code = f"DEDAN-{datetime.utcnow().strftime('%Y%m%d')}-{session['phone_number'][-4:]}"
        session['reference_code'] = reference_code
        
        response = (
            f"🏦 Ethiopia Bank Transfer\n\n"
            f"Reference Code: {reference_code}\n\n"
            f"Choose your bank:\n\n"
        )
        
        # Add bank options
        banks = ETHIOPIA_BANK_CONFIG
        for i, (bank_key, bank_info) in enumerate(banks.items(), 1):
            response += (
                f"{i}. {bank_info['name']}\n"
                f"   Account: {bank_info['account_number']}\n"
                f"   Name: {bank_info['account_name']}\n"
                f"   Branch: {bank_info['branch']}\n\n"
            )
        
        response += (
            f"📝 Transfer Instructions:\n"
            f"1. Transfer amount to any bank above\n"
            f"2. Include reference code: {reference_code}\n"
            f"3. Reply 'paid {reference_code}' when done\n"
            f"4. We'll verify and activate your trial\n\n"
            f"Your 14-day free trial starts immediately!\n\n"
            f"Reply 'cancel' to choose different payment method"
        )
        
        return response
    
    async def _generate_mobile_wallet_confirmation(self, session: Dict[str, Any]) -> str:
        """Generate mobile wallet confirmation"""
        
        response = (
            f"📱 Mobile Wallet Payment\n\n"
            f"Available Ethiopia mobile wallets:\n\n"
            f"1. 📱 Telebirr\n"
            f"   • Phone: 251911234567\n"
            f"   • Business: DEDAN Health\n"
            f"   • Reference: {session['phone_number']}\n\n"
            f"2. 💰 CBE Birr\n"
            f"   • Phone: 251911234568\n"
            f"   • Business: DEDAN Health\n"
            f"   • Reference: {session['phone_number']}\n\n"
            f"3. 🏦 Awash Wallet\n"
            f"   • Phone: 251911234569\n"
            f"   • Business: DEDAN Health\n"
            f"   • Reference: {session['phone_number']}\n\n"
            f"📝 Payment Instructions:\n"
            f"1. Send payment to any wallet above\n"
            f"2. Use your phone number as reference\n"
            f"3. Reply 'paid' when transaction complete\n"
            f"4. We'll verify and activate your trial\n\n"
            f"Your 14-day free trial starts immediately!\n\n"
            f"Reply 'cancel' to choose different payment method"
        )
        
        return response
    
    async def _handle_confirmation(self, session: Dict[str, Any], message: str) -> str:
        """Handle payment confirmation"""
        
        message_lower = message.lower().strip()
        
        if message_lower == 'started':
            session['state'] = 'trial_started'
            return (
                f"✅ Payment setup completed!\n\n"
                f"🎉 Your 14-day free trial is active!\n"
                f"📅 Trial ends: {(datetime.utcnow() + timedelta(days=14)).strftime('%B %d, %Y')}\n\n"
                f"You can now use all DEDAN Health features.\n\n"
                f"Reply 'features' to see available features\n"
                f"Reply 'status' to check trial status\n"
                f"Reply 'help' for more commands"
            )
        
        elif message_lower == 'cancel':
            session['state'] = 'payment_method'
            return await self._generate_payment_method_menu(
                get_pricing_tiers()[0]  # Return to payment method selection
            )
        
        elif message_lower == 'paid':
            return await self._handle_payment_verification(session)
        
        else:
            return (
                f"⏳ Waiting for payment confirmation...\n\n"
                f"Reply 'started' once payment is complete\n"
                f"Reply 'cancel' to choose different payment method"
            )
    
    async def _handle_bank_transfer(self, session: Dict[str, Any], message: str) -> str:
        """Handle bank transfer payment"""
        
        message_lower = message.lower().strip()
        
        if message_lower == 'cancel':
            session['state'] = 'payment_method'
            return await self._generate_payment_method_menu(
                get_pricing_tiers()[0]
            )
        
        elif message_lower.startswith('paid'):
            # Extract reference code
            parts = message_lower.split()
            if len(parts) >= 2 and parts[1] in session.get('reference_code', ''):
                return await self._verify_bank_transfer(session, parts[1])
            else:
                return (
                    f"❌ Invalid reference code.\n\n"
                    f"Please reply: 'paid {session.get('reference_code', 'XXXX')}'\n"
                    f"Or reply 'cancel' to choose different payment method"
                )
        
        else:
            return (
                f"🏦 Bank Transfer Instructions:\n\n"
                f"1. Complete transfer to any listed bank\n"
                f"2. Use reference code: {session.get('reference_code', 'XXXX')}\n"
                f"3. Reply 'paid {session.get('reference_code', 'XXXX')}' when done\n\n"
                f"Reply 'cancel' to choose different payment method"
            )
    
    async def _handle_payment_verification(self, session: Dict[str, Any]) -> str:
        """Handle payment verification"""
        
        # In production, this would verify the actual payment
        # For now, we'll simulate verification
        
        session['state'] = 'trial_started'
        
        return (
            f"✅ Payment verification initiated!\n\n"
            f"🔍 We're verifying your payment...\n"
            f"⏱️ This usually takes 5-10 minutes\n\n"
            f"🎉 Your 14-day free trial starts immediately!\n"
            f"📅 Trial ends: {(datetime.utcnow() + timedelta(days=14)).strftime('%B %d, %Y')}\n\n"
            f"You'll receive a confirmation when verification is complete.\n\n"
            f"Reply 'status' to check verification status\n"
            f"Reply 'features' to see available features"
        )
    
    async def _verify_bank_transfer(self, session: Dict[str, Any], reference_code: str) -> str:
        """Verify bank transfer payment"""
        
        if reference_code != session.get('reference_code'):
            return f"❌ Reference code mismatch. Please check and try again."
        
        # Start verification process
        session['state'] = 'verification_pending'
        
        return (
            f"✅ Bank transfer verification started!\n\n"
            f"🔍 Reference: {reference_code}\n"
            f"⏱️ Verification typically takes 1-2 business hours\n\n"
            f"🎉 Your 14-day free trial starts immediately!\n"
            f"📅 Trial ends: {(datetime.utcnow() + timedelta(days=14)).strftime('%B %d, %Y')}\n\n"
            f"We'll notify you when verification is complete.\n\n"
            f"Reply 'status' to check verification status\n"
            f"Reply 'features' to see available features"
        )
    
    async def _handle_unknown_state(self, session: Dict[str, Any], message: str) -> str:
        """Handle unknown state"""
        
        # Reset to initial state
        session['state'] = 'initial'
        
        return (
            "🔄 Session reset. Let's start over.\n\n"
            "Reply 'pricing' to see our plans and start your 14-day free trial.\n\n"
            "Available commands:\n"
            "• 'pricing' - View plans and pricing\n"
            "• 'trial' - Start 14-day free trial\n"
            "• 'help' - Show help message"
        )
    
    async def handle_help_request(self, phone_number: str) -> str:
        """Handle help request"""
        
        return (
            "🏥 DEDAN Health - Help Center\n\n"
            "📋 Available Commands:\n\n"
            "• 'pricing' - View plans and start free trial\n"
            "• 'trial' - Start 14-day free trial\n"
            "• 'status' - Check subscription status\n"
            "• 'features' - See available features\n"
            "• 'support' - Contact customer support\n"
            "• 'cancel' - Cancel current process\n\n"
            "💬 Pricing Flow:\n"
            "1. Reply 'pricing' to see plans\n"
            "2. Select plan (1-3)\n"
            "3. Choose payment method\n"
            "4. Start free trial immediately\n\n"
            "🇪🇹 Ethiopia Support:\n"
            "• Bank transfer available\n"
            "• Mobile wallet supported\n"
            "• Local customer service\n\n"
            "Reply 'pricing' to get started!"
        )
    
    async def handle_status_request(self, phone_number: str) -> str:
        """Handle status request"""
        
        session = self.active_sessions.get(phone_number)
        
        if not session:
            return (
                "❌ No active session found.\n\n"
                "Reply 'pricing' to start your free trial."
            )
        
        if session['state'] == 'trial_started':
            trial_end = datetime.utcnow() + timedelta(days=14)
            days_left = (trial_end - datetime.utcnow()).days
            
            return (
                f"📊 Your DEDAN Health Status\n\n"
                f"🎯 Status: Free Trial Active\n"
                f"📅 Trial ends: {trial_end.strftime('%B %d, %Y')}\n"
                f"⏰ Days remaining: {days_left}\n"
                f"🏥 Plan: {session['selected_tier'].title() if session['selected_tier'] else 'Professional'}\n\n"
                f"✨ All features are currently active!\n\n"
                f"Reply 'features' to see what you can do\n"
                f"Reply 'pricing' to upgrade before trial ends"
            )
        
        elif session['state'] == 'verification_pending':
            return (
                f"📊 Your DEDAN Health Status\n\n"
                f"🔍 Status: Payment Verification\n"
                f"⏱️ We're verifying your payment\n"
                f"🎉 Free trial is active during verification\n\n"
                f"Reply 'status' again to check progress\n"
                f"Reply 'support' for immediate assistance"
            )
        
        else:
            return (
                f"📊 Your DEDAN Health Status\n\n"
                f"⏳ Status: Setup in Progress\n"
                f"🔄 Current step: {session['state'].replace('_', ' ').title()}\n\n"
                f"Continue with the current process or reply 'cancel' to start over."
            )
    
    async def handle_features_request(self, phone_number: str) -> str:
        """Handle features request"""
        
        session = self.active_sessions.get(phone_number)
        
        if not session or session['state'] != 'trial_started':
            return (
                "🎯 Start your free trial to unlock all features!\n\n"
                "Reply 'pricing' to begin your 14-day free trial."
            )
        
        tier = session['selected_tier'] or 'professional'
        
        features = {
            'starter': [
                '🤖 Basic AI triage',
                '🛡️ Safety guard system',
                '💬 WhatsApp/SMS access',
                '🏥 Clinic console (2 staff)',
                '📊 Basic analytics',
                '📧 Email support'
            ],
            'professional': [
                '✨ All Starter features',
                '🔮 Risk prediction AI',
                '💊 Chronic care coaching',
                '📈 Advanced analytics',
                '🌍 Multi-language support',
                '⚡ Priority support',
                '📱 Mobile app access'
            ],
            'enterprise': [
                '✨ All Professional features',
                '🖼️ Image analysis AI',
                '🧠 Explainability AI',
                '⚖️ Bias monitoring',
                '🏢 Multi-clinic hub',
                '🔌 API access',
                '🎨 White-label options',
                '👨‍💼 Dedicated support'
            ]
        }
        
        tier_features = features.get(tier, features['professional'])
        
        response = (
            f"✨ Your DEDAN Health Features\n\n"
            f"🏥 Plan: {tier.title()}\n\n"
        )
        
        for i, feature in enumerate(tier_features, 1):
            response += f"{i}. {feature}\n"
        
        response += (
            f"\n🎯 Ready to use these features!\n"
            f"Reply 'triage' to start AI triage\n"
            f"Reply 'dashboard' to access clinic console\n"
            f"Reply 'help' for more commands"
        )
        
        return response
    
    def cleanup_old_sessions(self):
        """Clean up sessions older than 24 hours"""
        
        current_time = datetime.utcnow()
        expired_sessions = [
            phone for phone, session in self.active_sessions.items()
            if (current_time - session['last_activity']).total_seconds() > 86400  # 24 hours
        ]
        
        for phone in expired_sessions:
            del self.active_sessions[phone]
        
        logger.info(f"Cleaned up {len(expired_sessions)} expired WhatsApp sessions")

# Global WhatsApp pricing flow instance
whatsapp_pricing_flow = WhatsAppPricingFlow()
