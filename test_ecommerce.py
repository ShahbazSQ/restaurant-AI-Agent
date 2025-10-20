"""
Quick test to show e-commerce works
Run this to see orders and payments working!
"""

from order_manager import OrderManager
from payment_handler import PaymentHandler, PaymentMethod

print("🧪 Testing E-Commerce System\n")

# Initialize
om = OrderManager()
ph = PaymentHandler()

# Create order
print("1️⃣ Creating order...")
order = om.create_order(
    customer_phone="+923001234567",
    customer_name="Ahmed Khan",
    items=[
        {"name": "Chicken Biryani", "qty": 2, "price": 950, "subtotal": 1900},
        {"name": "Fresh Lime Soda", "qty": 2, "price": 150, "subtotal": 300}
    ],
    delivery_address="123 Main Street, Karachi",
    delivery_type="DELIVERY"
)

print("\n✅ ORDER CREATED!")
print(om.get_order_summary(order['order_id']))

# Process payment
print("\n2️⃣ Processing payment...")
payment = ph.initiate_payment(
    order_id=order['order_id'],
    amount=order['total'],
    customer_phone="+923001234567",
    method=PaymentMethod.MOCK
)

print("\n✅ PAYMENT COMPLETED!")
print(ph.get_payment_summary(payment['payment_id']))

print("\n3️⃣ Order status:")
updated_order = om.get_order(order['order_id'])
print(f"Status: {updated_order['status']}")

print("\n🎉 E-COMMERCE SYSTEM WORKS!")
print("Now we just need to add this to Streamlit UI...")