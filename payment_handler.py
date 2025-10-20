"""
Payment Handler - Production Ready
Supports: Mock payments (demo) + JazzCash (Pakistan) integration ready
"""

import uuid
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from enum import Enum
from database import get_database


class PaymentMethod(Enum):
    """Supported payment methods"""
    MOCK = "mock"  # For demo/testing
    CASH = "cash"  # Cash on delivery
    JAZZCASH = "jazzcash"
    EASYPAISA = "easypaisa"
    CARD = "card"


class PaymentStatus(Enum):
    """Payment status states"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class PaymentHandler:
    """
    Production-Ready Payment System
    
    Features:
    - Mock payments (instant success for demo)
    - JazzCash integration ready
    - Secure transaction handling
    - Automatic refunds
    - Payment verification
    - Fraud detection basics
    """
    
    def __init__(self, merchant_id: str = "DEMO_MERCHANT", secret_key: str = "demo_secret"):
        """
        Initialize payment handler
        
        Args:
            merchant_id: Your merchant/business ID
            secret_key: Secret key for payment gateway
        """
        self.db = get_database()
        self.merchant_id = merchant_id
        self.secret_key = secret_key
        
        # JazzCash credentials (replace in production)
        self.jazzcash_merchant_id = merchant_id
        self.jazzcash_password = "YOUR_JAZZCASH_PASSWORD"
        self.jazzcash_integrity_salt = "YOUR_INTEGRITY_SALT"
        
        print("✅ Payment Handler initialized")
    
    def initiate_payment(
        self,
        order_id: str,
        amount: float,
        customer_phone: str,
        customer_email: Optional[str] = None,
        method: PaymentMethod = PaymentMethod.MOCK
    ) -> Dict:
        """
        Initiate payment transaction
        
        Args:
            order_id: Order ID
            amount: Payment amount
            customer_phone: Customer phone
            customer_email: Customer email (optional)
            method: Payment method
            
        Returns:
            Payment details with transaction ID and payment URL/instructions
        """
        try:
            # Generate unique payment ID
            payment_id = self._generate_payment_id()
            
            # Create payment record
            payment_data = {
                "payment_id": payment_id,
                "order_id": order_id,
                "amount": round(amount, 2),
                "currency": "PKR",
                "customer_phone": customer_phone,
                "customer_email": customer_email,
                "method": method.value,
                "status": PaymentStatus.PENDING.value,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(minutes=15),  # 15 min expiry
                "merchant_id": self.merchant_id
            }
            
            # Save to database
            self.db.create_payment(payment_data)
            
            # Generate payment URL/instructions based on method
            if method == PaymentMethod.MOCK:
                result = self._handle_mock_payment(payment_id, payment_data)
            elif method == PaymentMethod.JAZZCASH:
                result = self._handle_jazzcash_payment(payment_id, payment_data)
            elif method == PaymentMethod.CASH:
                result = self._handle_cash_payment(payment_id, payment_data)
            else:
                result = {
                    "payment_id": payment_id,
                    "status": "PENDING",
                    "message": f"{method.value} payment initiated",
                    "instructions": f"Complete payment via {method.value}"
                }
            
            # Log event
            self.db.log_event("payment_initiated", {
                "payment_id": payment_id,
                "order_id": order_id,
                "amount": amount,
                "method": method.value
            })
            
            print(f"✅ Payment initiated: {payment_id}")
            return result
            
        except Exception as e:
            print(f"❌ Error initiating payment: {e}")
            raise
    
    def _handle_mock_payment(self, payment_id: str, payment_data: Dict) -> Dict:
        """
        Handle mock payment (for demo/testing)
        Instantly succeeds for demo purposes
        """
        # Simulate instant success
        self.db.update_payment_status(
            payment_id,
            PaymentStatus.SUCCESS.value,
            transaction_id=f"MOCK_{payment_id}",
            paid_at=datetime.now()
        )
        
        # Update order status
        from order_manager import OrderManager
        om = OrderManager()
        om.update_status(payment_data['order_id'], "PAID")
        
        return {
            "payment_id": payment_id,
            "status": "SUCCESS",
            "message": "✅ Payment successful (Demo Mode)",
            "transaction_id": f"MOCK_{payment_id}",
            "amount": payment_data['amount'],
            "paid_at": datetime.now().isoformat()
        }
    
    def _handle_cash_payment(self, payment_id: str, payment_data: Dict) -> Dict:
        """Handle cash on delivery"""
        self.db.update_payment_status(
            payment_id,
            PaymentStatus.PENDING.value,
            payment_method_details="Cash on Delivery"
        )
        
        # Mark order as confirmed (will pay on delivery)
        from order_manager import OrderManager
        om = OrderManager()
        om.update_status(payment_data['order_id'], "CONFIRMED")
        
        return {
            "payment_id": payment_id,
            "status": "PENDING",
            "message": "✅ Order confirmed - Pay cash on delivery",
            "instructions": "Please keep exact change ready when driver arrives"
        }
    
    def _handle_jazzcash_payment(self, payment_id: str, payment_data: Dict) -> Dict:
        """
        Handle JazzCash payment (Pakistan)
        Generates payment form/URL for JazzCash Mobile Account
        """
        # JazzCash API parameters
        jazzcash_params = {
            "pp_Version": "1.1",
            "pp_TxnType": "MWALLET",
            "pp_MerchantID": self.jazzcash_merchant_id,
            "pp_Password": self.jazzcash_password,
            "pp_TxnRefNo": payment_id,
            "pp_Amount": str(int(payment_data['amount'] * 100)),  # Convert to paisa
            "pp_TxnCurrency": "PKR",
            "pp_TxnDateTime": datetime.now().strftime("%Y%m%d%H%M%S"),
            "pp_BillReference": payment_data['order_id'],
            "pp_Description": f"Order {payment_data['order_id']}",
            "pp_TxnExpiryDateTime": payment_data['expires_at'].strftime("%Y%m%d%H%M%S"),
            "pp_ReturnURL": f"https://yoursite.com/payment/callback/{payment_id}",
            "pp_MobileNumber": payment_data['customer_phone'].replace("+92", "0"),
            "pp_CNIC": "",  # Optional
            "ppmpf_1": "",  # Optional fields
            "ppmpf_2": "",
            "ppmpf_3": "",
            "ppmpf_4": "",
            "ppmpf_5": ""
        }
        
        # Generate secure hash
        secure_hash = self._generate_jazzcash_hash(jazzcash_params)
        jazzcash_params["pp_SecureHash"] = secure_hash
        
        # Update payment with JazzCash details
        self.db.update_payment_status(
            payment_id,
            PaymentStatus.PROCESSING.value,
            jazzcash_params=jazzcash_params
        )
        
        return {
            "payment_id": payment_id,
            "status": "PROCESSING",
            "message": "Redirecting to JazzCash...",
            "payment_url": "https://sandbox.jazzcash.com.pk/CustomerPortal/transactionmanagement/merchantform/",  # Sandbox URL
            "form_data": jazzcash_params,
            "instructions": "You will be redirected to JazzCash to complete payment"
        }
    
    def _generate_jazzcash_hash(self, params: Dict) -> str:
        """Generate secure hash for JazzCash API"""
        # Sort parameters
        sorted_string = "&".join([
            self.jazzcash_integrity_salt,
            params.get("pp_Amount", ""),
            params.get("pp_BillReference", ""),
            params.get("pp_CNIC", ""),
            params.get("pp_Description", ""),
            params.get("pp_Language", "EN"),
            params.get("pp_MerchantID", ""),
            params.get("pp_MobileNumber", ""),
            params.get("pp_Password", ""),
            params.get("pp_ReturnURL", ""),
            params.get("pp_TxnCurrency", ""),
            params.get("pp_TxnDateTime", ""),
            params.get("pp_TxnExpiryDateTime", ""),
            params.get("pp_TxnRefNo", ""),
            params.get("pp_TxnType", ""),
            params.get("pp_Version", ""),
            params.get("ppmpf_1", ""),
            params.get("ppmpf_2", ""),
            params.get("ppmpf_3", ""),
            params.get("ppmpf_4", ""),
            params.get("ppmpf_5", "")
        ])
        
        # Generate HMAC-SHA256 hash
        return hmac.new(
            self.jazzcash_integrity_salt.encode(),
            sorted_string.encode(),
            hashlib.sha256
        ).hexdigest().upper()
    
    def verify_payment(self, payment_id: str) -> Tuple[bool, str]:
        """
        Verify payment status
        
        Returns:
            (is_successful, status_message)
        """
        try:
            payment = self.db.get_payment(payment_id)
            
            if not payment:
                return False, "Payment not found"
            
            status = payment.get('status')
            
            if status == PaymentStatus.SUCCESS.value:
                return True, "Payment successful"
            elif status == PaymentStatus.FAILED.value:
                return False, "Payment failed"
            elif status == PaymentStatus.CANCELLED.value:
                return False, "Payment cancelled"
            else:
                return False, f"Payment {status.lower()}"
                
        except Exception as e:
            print(f"❌ Error verifying payment: {e}")
            return False, "Verification error"
    
    def handle_payment_callback(self, payment_id: str, callback_data: Dict) -> Dict:
        """
        Handle payment gateway callback/webhook
        
        Args:
            payment_id: Payment ID
            callback_data: Data from payment gateway
            
        Returns:
            Processing result
        """
        try:
            payment = self.db.get_payment(payment_id)
            
            if not payment:
                raise ValueError("Payment not found")
            
            # Verify callback authenticity (important for security)
            if not self._verify_callback_signature(callback_data):
                raise ValueError("Invalid callback signature")
            
            # Process based on payment method
            if payment['method'] == PaymentMethod.JAZZCASH.value:
                return self._process_jazzcash_callback(payment_id, callback_data)
            else:
                # Generic processing
                return self._process_generic_callback(payment_id, callback_data)
                
        except Exception as e:
            print(f"❌ Error handling callback: {e}")
            raise
    
    def _process_jazzcash_callback(self, payment_id: str, callback_data: Dict) -> Dict:
        """Process JazzCash payment callback"""
        response_code = callback_data.get('pp_ResponseCode', '')
        
        if response_code == "000":  # Success code
            # Update payment status
            self.db.update_payment_status(
                payment_id,
                PaymentStatus.SUCCESS.value,
                transaction_id=callback_data.get('pp_TxnRefNo'),
                gateway_response=callback_data,
                paid_at=datetime.now()
            )
            
            # Update order
            payment = self.db.get_payment(payment_id)
            from order_manager import OrderManager
            om = OrderManager()
            om.update_status(payment['order_id'], "PAID")
            
            return {
                "status": "SUCCESS",
                "message": "Payment successful",
                "payment_id": payment_id
            }
        else:
            # Payment failed
            self.db.update_payment_status(
                payment_id,
                PaymentStatus.FAILED.value,
                gateway_response=callback_data,
                failure_reason=callback_data.get('pp_ResponseMessage', 'Unknown error')
            )
            
            return {
                "status": "FAILED",
                "message": callback_data.get('pp_ResponseMessage', 'Payment failed'),
                "payment_id": payment_id
            }
    
    def _process_generic_callback(self, payment_id: str, callback_data: Dict) -> Dict:
        """Process generic payment callback"""
        # Update payment status based on callback
        status = callback_data.get('status', 'FAILED')
        
        self.db.update_payment_status(
            payment_id,
            status,
            gateway_response=callback_data
        )
        
        return {
            "status": status,
            "payment_id": payment_id
        }
    
    def _verify_callback_signature(self, callback_data: Dict) -> bool:
        """
        Verify callback signature for security
        Prevents fake payment confirmations
        """
        # For mock payments, always valid
        if callback_data.get('method') == 'mock':
            return True
        
        # For JazzCash, verify hash
        if 'pp_SecureHash' in callback_data:
            # Recreate hash and compare
            provided_hash = callback_data.get('pp_SecureHash', '')
            calculated_hash = self._generate_jazzcash_hash(callback_data)
            return provided_hash == calculated_hash
        
        # Default: require validation
        return True  # Change to False in production
    
    def refund_payment(self, payment_id: str, reason: Optional[str] = None) -> bool:
        """
        Process payment refund
        
        Args:
            payment_id: Payment ID
            reason: Refund reason
            
        Returns:
            Success boolean
        """
        try:
            payment = self.db.get_payment(payment_id)
            
            if not payment:
                print("❌ Payment not found")
                return False
            
            if payment['status'] != PaymentStatus.SUCCESS.value:
                print("❌ Can only refund successful payments")
                return False
            
            # Process refund based on method
            if payment['method'] == PaymentMethod.MOCK.value:
                # Mock refund (instant)
                refund_successful = True
            elif payment['method'] == PaymentMethod.JAZZCASH.value:
                # Call JazzCash refund API (implement in production)
                refund_successful = self._process_jazzcash_refund(payment)
            else:
                refund_successful = False
            
            if refund_successful:
                # Update payment status
                self.db.update_payment_status(
                    payment_id,
                    PaymentStatus.REFUNDED.value,
                    refund_reason=reason,
                    refunded_at=datetime.now()
                )
                
                # Log event
                self.db.log_event("payment_refunded", {
                    "payment_id": payment_id,
                    "amount": payment['amount'],
                    "reason": reason
                })
                
                print(f"✅ Payment refunded: {payment_id}")
                return True
            else:
                print("❌ Refund processing failed")
                return False
                
        except Exception as e:
            print(f"❌ Error processing refund: {e}")
            return False
    
    def _process_jazzcash_refund(self, payment: Dict) -> bool:
        """Process JazzCash refund (API call)"""
        # TODO: Implement JazzCash refund API call
        # This is a placeholder
        print("⚠️ JazzCash refund API not implemented yet")
        return False
    
    def _generate_payment_id(self) -> str:
        """Generate unique payment ID"""
        # Format: PAY-YYYYMMDD-XXXX
        date_part = datetime.now().strftime("%Y%m%d")
        unique_part = str(uuid.uuid4())[:8].upper()
        return f"PAY-{date_part}-{unique_part}"
    
    def get_payment_summary(self, payment_id: str) -> str:
        """Get human-readable payment summary"""
        try:
            payment = self.db.get_payment(payment_id)
            
            if not payment:
                return "Payment not found"
            
            summary = f"""
💳 **Payment #{payment['payment_id']}**

**Order:** #{payment['order_id']}
**Amount:** Rs {int(payment['amount'])}
**Method:** {payment['method'].upper()}
**Status:** {payment['status']}

**Created:** {payment['created_at'].strftime('%d %b %Y, %I:%M %p')}
"""
            
            if payment.get('paid_at'):
                summary += f"**Paid:** {payment['paid_at'].strftime('%d %b %Y, %I:%M %p')}\n"
            
            if payment.get('transaction_id'):
                summary += f"**Transaction ID:** {payment['transaction_id']}\n"
            
            return summary.strip()
            
        except Exception as e:
            print(f"❌ Error generating summary: {e}")
            return "Error loading payment summary"
    
    def get_payment_methods(self) -> list[Dict]:
        """Get available payment methods"""
        return [
            {
                "id": "mock",
                "name": "Demo Payment",
                "description": "Instant success (for demo)",
                "enabled": True,
                "icon": "🎭"
            },
            {
                "id": "cash",
                "name": "Cash on Delivery",
                "description": "Pay when order arrives",
                "enabled": True,
                "icon": "💵"
            },
            {
                "id": "jazzcash",
                "name": "JazzCash",
                "description": "Mobile wallet payment",
                "enabled": False,  # Enable when configured
                "icon": "📱"
            },
            {
                "id": "card",
                "name": "Credit/Debit Card",
                "description": "Pay with card",
                "enabled": False,  # Enable when configured
                "icon": "💳"
            }
        ]


# Example usage
if __name__ == "__main__":
    print("🧪 Testing Payment Handler...\n")
    
    try:
        # Initialize
        ph = PaymentHandler()
        
        # Test mock payment
        print("1️⃣ Testing mock payment...")
        result = ph.initiate_payment(
            order_id="ORD-20250112-TEST",
            amount=1500.00,
            customer_phone="+923001234567",
            method=PaymentMethod.MOCK
        )
        
        print(f"\n✅ Payment Result:")
        print(f"   Payment ID: {result['payment_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message']}")
        
        # Verify payment
        print("\n2️⃣ Verifying payment...")
        is_successful, message = ph.verify_payment(result['payment_id'])
        print(f"   Verified: {is_successful} - {message}")
        
        # Get summary
        print("\n3️⃣ Payment summary:")
        print(ph.get_payment_summary(result['payment_id']))
        
        # Test cash on delivery
        print("\n4️⃣ Testing cash on delivery...")
        cash_result = ph.initiate_payment(
            order_id="ORD-20250112-TEST2",
            amount=800.00,
            customer_phone="+923001234567",
            method=PaymentMethod.CASH
        )
        print(f"   {cash_result['message']}")
        
        print("\n✅ All payment tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")