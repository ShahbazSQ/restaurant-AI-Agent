"""
Order Management System
Handles complete order lifecycle from creation to delivery
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
from database import get_database


class OrderManager:
    """
    Complete Order Management System
    
    Features:
    - Order creation & validation
    - Status tracking
    - ETA calculation
    - Order history
    - Reorder functionality
    """
    
    # Order status flow
    ORDER_STATUSES = [
        "PENDING_PAYMENT",  # Waiting for payment
        "PAID",             # Payment confirmed
        "CONFIRMED",        # Order confirmed by restaurant
        "COOKING",          # Being prepared
        "READY",            # Ready for pickup/delivery
        "DISPATCHED",       # Out for delivery
        "DELIVERED",        # Completed
        "CANCELLED"         # Cancelled
    ]
    
    def __init__(self):
        """Initialize order manager"""
        self.db = get_database()
        print("✅ Order Manager initialized")
    
    def create_order(
        self,
        customer_phone: str,
        customer_name: str,
        items: List[Dict],
        delivery_address: Optional[str] = None,
        special_instructions: Optional[str] = None,
        delivery_type: str = "DELIVERY"  # or "PICKUP"
    ) -> Dict:
        """
        Create new order
        
        Args:
            customer_phone: Customer phone number
            customer_name: Customer name
            items: List of {name, qty, price, subtotal}
            delivery_address: Delivery address
            special_instructions: Special requests
            delivery_type: DELIVERY or PICKUP
            
        Returns:
            Complete order object
        """
        try:
            # Generate unique order ID
            order_id = self._generate_order_id()
            
            # Calculate totals
            subtotal = sum(item['subtotal'] for item in items)
            delivery_fee = 50 if delivery_type == "DELIVERY" else 0
            tax = subtotal * 0.05  # 5% tax
            total = subtotal + delivery_fee + tax
            
            # Calculate ETA
            estimated_time = self._calculate_eta(items, delivery_type)
            
            # Create order object
            order = {
                "order_id": order_id,
                "customer_phone": customer_phone,
                "customer_name": customer_name,
                "items": items,
                "subtotal": round(subtotal, 2),
                "delivery_fee": delivery_fee,
                "tax": round(tax, 2),
                "total": round(total, 2),
                "status": "PENDING_PAYMENT",
                "payment_status": "PENDING",
                "delivery_type": delivery_type,
                "delivery_address": delivery_address,
                "special_instructions": special_instructions,
                "estimated_delivery": estimated_time,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            # Save to database
            self.db.create_order(order)
            
            # Log analytics
            self.db.log_event("order_created", {
                "order_id": order_id,
                "total": total,
                "items_count": len(items)
            })
            
            print(f"✅ Order created: {order_id}")
            return order
            
        except Exception as e:
            print(f"❌ Error creating order: {e}")
            raise
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID"""
        # Format: ORD-YYYYMMDD-XXXX
        date_part = datetime.now().strftime("%Y%m%d")
        unique_part = str(uuid.uuid4())[:4].upper()
        return f"ORD-{date_part}-{unique_part}"
    
    def _calculate_eta(self, items: List[Dict], delivery_type: str) -> datetime:
        """
        Calculate estimated delivery time
        
        Factors:
        - Number of items
        - Item complexity (some items take longer)
        - Delivery vs pickup
        - Current time (peak hours)
        """
        # Base preparation time
        base_time = 15  # minutes
        
        # Add time per item
        item_time = len(items) * 3
        
        # Add delivery time
        delivery_time = 15 if delivery_type == "DELIVERY" else 0
        
        # Peak hour adjustment (lunch: 12-2, dinner: 7-9)
        current_hour = datetime.now().hour
        if current_hour in [12, 13, 19, 20]:
            base_time += 10  # Extra 10 mins during peak
        
        # Total time
        total_minutes = base_time + item_time + delivery_time
        
        # Cap at 60 minutes max
        total_minutes = min(total_minutes, 60)
        
        # Calculate ETA
        eta = datetime.now() + timedelta(minutes=total_minutes)
        
        return eta
    
    def update_status(
        self,
        order_id: str,
        new_status: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update order status
        
        Args:
            order_id: Order ID
            new_status: New status from ORDER_STATUSES
            notes: Optional notes
            
        Returns:
            Success boolean
        """
        try:
            # Validate status
            if new_status not in self.ORDER_STATUSES:
                raise ValueError(f"Invalid status: {new_status}")
            
            # Get current order
            order = self.db.get_order(order_id)
            if not order:
                raise ValueError(f"Order not found: {order_id}")
            
            # Update in database
            update_data = {"notes": notes} if notes else {}
            success = self.db.update_order_status(order_id, new_status, **update_data)
            
            if success:
                # Log event
                self.db.log_event("order_status_changed", {
                    "order_id": order_id,
                    "old_status": order.get('status'),
                    "new_status": new_status
                })
                
                print(f"✅ Order {order_id} → {new_status}")
            
            return success
            
        except Exception as e:
            print(f"❌ Error updating status: {e}")
            return False
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """Get order details"""
        return self.db.get_order(order_id)
    
    def get_customer_orders(
        self,
        customer_phone: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get customer's order history"""
        return self.db.get_customer_orders(customer_phone, limit)
    
    def get_active_orders(self) -> List[Dict]:
        """Get all active orders"""
        return self.db.get_active_orders()
    
    def cancel_order(
        self,
        order_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Cancel order
        
        Args:
            order_id: Order ID
            reason: Cancellation reason
            
        Returns:
            Success boolean
        """
        try:
            order = self.db.get_order(order_id)
            
            if not order:
                return False
            
            # Can only cancel if not yet delivered
            if order['status'] in ["DELIVERED", "CANCELLED"]:
                print(f"⚠️ Cannot cancel order in status: {order['status']}")
                return False
            
            # Update status
            success = self.db.update_order_status(
                order_id,
                "CANCELLED",
                cancellation_reason=reason,
                cancelled_at=datetime.now()
            )
            
            if success:
                # Log event
                self.db.log_event("order_cancelled", {
                    "order_id": order_id,
                    "reason": reason
                })
                
                print(f"✅ Order cancelled: {order_id}")
            
            return success
            
        except Exception as e:
            print(f"❌ Error cancelling order: {e}")
            return False
    
    def reorder(self, previous_order_id: str, customer_phone: str) -> Optional[Dict]:
        """
        Reorder from previous order
        
        Args:
            previous_order_id: Previous order ID
            customer_phone: Customer phone (for verification)
            
        Returns:
            New order object
        """
        try:
            # Get previous order
            old_order = self.db.get_order(previous_order_id)
            
            if not old_order:
                raise ValueError("Previous order not found")
            
            # Verify customer
            if old_order['customer_phone'] != customer_phone:
                raise ValueError("Order does not belong to this customer")
            
            # Create new order with same items
            new_order = self.create_order(
                customer_phone=old_order['customer_phone'],
                customer_name=old_order['customer_name'],
                items=old_order['items'],
                delivery_address=old_order.get('delivery_address'),
                delivery_type=old_order.get('delivery_type', 'DELIVERY')
            )
            
            print(f"✅ Reordered from {previous_order_id} → {new_order['order_id']}")
            return new_order
            
        except Exception as e:
            print(f"❌ Error reordering: {e}")
            return None
    
    def get_order_timeline(self, order_id: str) -> List[Dict]:
        """
        Get order status timeline
        
        Returns:
            List of status events with timestamps
        """
        try:
            order = self.db.get_order(order_id)
            
            if not order:
                return []
            
            timeline = []
            
            # Map statuses to timeline events
            status_map = {
                "created_at": ("Order Placed", "PENDING_PAYMENT"),
                "paid_at": ("Payment Confirmed", "PAID"),
                "confirmed_at": ("Order Confirmed", "CONFIRMED"),
                "cooking_at": ("Preparing Food", "COOKING"),
                "ready_at": ("Ready", "READY"),
                "dispatched_at": ("Out for Delivery", "DISPATCHED"),
                "delivered_at": ("Delivered", "DELIVERED"),
                "cancelled_at": ("Cancelled", "CANCELLED")
            }
            
            for time_field, (label, status) in status_map.items():
                if time_field in order and order[time_field]:
                    timeline.append({
                        "label": label,
                        "status": status,
                        "timestamp": order[time_field],
                        "completed": True
                    })
            
            # Sort by timestamp
            timeline.sort(key=lambda x: x['timestamp'])
            
            return timeline
            
        except Exception as e:
            print(f"❌ Error getting timeline: {e}")
            return []
    
    def get_order_summary(self, order_id: str) -> str:
        """
        Get human-readable order summary
        
        Returns:
            Formatted order summary text
        """
        try:
            order = self.db.get_order(order_id)
            
            if not order:
                return "Order not found"
            
            # Format items
            items_text = "\n".join([
                f"• {item['qty']}x {item['name']} @ Rs {int(item['price'])} = Rs {int(item['subtotal'])}"
                for item in order['items']
            ])
            
            # Format totals
            summary = f"""
📋 **Order #{order['order_id']}**

**Items:**
{items_text}

**Subtotal:** Rs {int(order['subtotal'])}
**Delivery:** Rs {int(order['delivery_fee'])}
**Tax (5%):** Rs {int(order['tax'])}
**Total:** Rs {int(order['total'])}

**Status:** {order['status']}
**Type:** {order['delivery_type']}
"""
            
            if order.get('delivery_address'):
                summary += f"**Address:** {order['delivery_address']}\n"
            
            if order.get('special_instructions'):
                summary += f"**Notes:** {order['special_instructions']}\n"
            
            if order.get('estimated_delivery'):
                eta = order['estimated_delivery']
                summary += f"\n⏰ **ETA:** {eta.strftime('%I:%M %p')}"
            
            return summary.strip()
            
        except Exception as e:
            print(f"❌ Error generating summary: {e}")
            return "Error loading order summary"
    
    def validate_order_items(self, items: List[Dict]) -> tuple[bool, str]:
        """
        Validate order items
        
        Returns:
            (is_valid, error_message)
        """
        if not items:
            return False, "No items in order"
        
        for item in items:
            # Check required fields
            required = ['name', 'qty', 'price', 'subtotal']
            if not all(field in item for field in required):
                return False, f"Missing fields in item: {item.get('name', 'Unknown')}"
            
            # Validate quantities
            if item['qty'] <= 0:
                return False, f"Invalid quantity for {item['name']}"
            
            # Validate prices
            if item['price'] <= 0:
                return False, f"Invalid price for {item['name']}"
            
            # Validate subtotal
            expected_subtotal = item['qty'] * item['price']
            if abs(item['subtotal'] - expected_subtotal) > 0.01:
                return False, f"Subtotal mismatch for {item['name']}"
        
        return True, "Valid"


# Example usage
if __name__ == "__main__":
    print("🧪 Testing Order Manager...\n")
    
    try:
        # Initialize
        om = OrderManager()
        
        # Create test order
        test_items = [
            {"name": "Chicken Biryani", "qty": 2, "price": 650, "subtotal": 1300},
            {"name": "Coke", "qty": 2, "price": 80, "subtotal": 160}
        ]
        
        order = om.create_order(
            customer_phone="+923001234567",
            customer_name="Ahmed Khan",
            items=test_items,
            delivery_address="123 Main St, Karachi",
            delivery_type="DELIVERY"
        )
        
        print(f"\n✅ Order created:")
        print(om.get_order_summary(order['order_id']))
        
        # Update status
        print("\n🔄 Updating status...")
        om.update_status(order['order_id'], "PAID")
        om.update_status(order['order_id'], "COOKING")
        
        # Get timeline
        print("\n📅 Order timeline:")
        timeline = om.get_order_timeline(order['order_id'])
        for event in timeline:
            print(f"  {event['label']}: {event['timestamp']}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")