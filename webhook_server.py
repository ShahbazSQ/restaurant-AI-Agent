"""
Webhook Server - Flask API
Handles payment callbacks, webhooks, and API endpoints
Runs on Port 5000 (separate from Streamlit on 8501)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from functools import wraps
import hashlib
import hmac
from datetime import datetime
from typing import Dict
import os

from payment_handler import PaymentHandler, PaymentMethod
from order_manager import OrderManager
from database import get_database

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Initialize components
ph = PaymentHandler()
om = OrderManager()
db = get_database()

# Security: API Key for authentication
API_KEY = os.getenv('API_KEY', 'your_secret_api_key_change_in_production')


# ==================== AUTHENTICATION ====================

def require_api_key(f):
    """Decorator to require API key for endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check API key in header
        provided_key = request.headers.get('X-API-Key')
        
        if not provided_key or provided_key != API_KEY:
            return jsonify({
                "error": "Unauthorized",
                "message": "Invalid or missing API key"
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function


# ==================== HEALTH & STATUS ====================

@app.route('/', methods=['GET'])
def index():
    """API root - health check"""
    return jsonify({
        "service": "Restaurant E-Commerce API",
        "status": "online",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "payment_callback": "/webhook/payment/<payment_id>",
            "order_status": "/api/order/<order_id>",
            "create_order": "/api/order/create",
            "initiate_payment": "/api/payment/initiate"
        }
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    db_healthy = db.health_check()
    
    return jsonify({
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "timestamp": datetime.now().isoformat()
    }), 200 if db_healthy else 503


# ==================== PAYMENT WEBHOOKS ====================

@app.route('/webhook/payment/<payment_id>', methods=['POST'])
def payment_callback(payment_id):
    """
    Payment gateway callback/webhook
    Called by JazzCash/payment gateway after payment attempt
    """
    try:
        # Get callback data
        callback_data = request.form.to_dict() if request.form else request.get_json()

        if not callback_data:
            return jsonify({"error": "No callback data"}), 400

        # Log callback
        db.log_event("payment_callback_received", {
            "payment_id": payment_id,
            "data": callback_data
        })

        print(f"📥 Payment callback received: {payment_id}")

        # Process callback
        result = ph.handle_payment_callback(payment_id, callback_data)

        # Return success response
        return jsonify({
            "success": True,
            "payment_id": payment_id,
            "status": result.get('status'),
            "message": result.get('message', 'Callback processed')
        }), 200

    except Exception as e:
        print(f"❌ Error processing callback: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/order/<order_id>/timeline', methods=['GET'])
def get_order_timeline_api(order_id):
    """Get order status timeline"""
    try:
        timeline = om.get_order_timeline(order_id)
        
        # Convert datetime to ISO format
        for event in timeline:
            if 'timestamp' in event:
                event['timestamp'] = event['timestamp'].isoformat()
        
        return jsonify({
            "success": True,
            "timeline": timeline
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching timeline: {e}")
        return jsonify({"error": str(e)}), 500


# ==================== PAYMENT API ====================

@app.route('/api/payment/initiate', methods=['POST'])
@require_api_key
def initiate_payment_api():
    """
    Initiate payment
    
    Request body:
    {
        "order_id": "ORD-20250112-ABC",
        "amount": 1500,
        "customer_phone": "+923001234567",
        "method": "mock"  // mock, cash, jazzcash, card
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['order_id', 'amount', 'customer_phone', 'method']
        if not all(field in data for field in required):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Convert method string to enum
        method_map = {
            'mock': PaymentMethod.MOCK,
            'cash': PaymentMethod.CASH,
            'jazzcash': PaymentMethod.JAZZCASH,
            'card': PaymentMethod.CARD
        }
        
        payment_method = method_map.get(data['method'].lower())
        if not payment_method:
            return jsonify({"error": "Invalid payment method"}), 400
        
        # Initiate payment
        result = ph.initiate_payment(
            order_id=data['order_id'],
            amount=float(data['amount']),
            customer_phone=data['customer_phone'],
            customer_email=data.get('customer_email'),
            method=payment_method
        )
        
        # Convert datetime to ISO format
        if 'paid_at' in result and isinstance(result['paid_at'], datetime):
            result['paid_at'] = result['paid_at'].isoformat()
        
        return jsonify({
            "success": True,
            "payment": result
        }), 200
        
    except Exception as e:
        print(f"❌ Error initiating payment: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/payment/<payment_id>', methods=['GET'])
def get_payment_api(payment_id):
    """Get payment details"""
    try:
        payment = db.get_payment(payment_id)
        
        if not payment:
            return jsonify({"error": "Payment not found"}), 404
        
        # Remove MongoDB _id
        if '_id' in payment:
            del payment['_id']
        
        # Convert datetime to ISO format
        for key in payment:
            if isinstance(payment[key], datetime):
                payment[key] = payment[key].isoformat()
        
        return jsonify({
            "success": True,
            "payment": payment
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching payment: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/payment/<payment_id>/verify', methods=['GET'])
def verify_payment_api(payment_id):
    """Verify payment status"""
    try:
        is_successful, message = ph.verify_payment(payment_id)
        
        return jsonify({
            "success": True,
            "verified": is_successful,
            "message": message
        }), 200
        
    except Exception as e:
        print(f"❌ Error verifying payment: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/payment/<payment_id>/refund', methods=['POST'])
@require_api_key
def refund_payment_api(payment_id):
    """
    Refund payment
    
    Request body:
    {
        "reason": "Customer requested refund"
    }
    """
    try:
        data = request.get_json()
        reason = data.get('reason') if data else None
        
        success = ph.refund_payment(payment_id, reason)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Payment refunded successfully"
            }), 200
        else:
            return jsonify({"error": "Failed to process refund"}), 500
            
    except Exception as e:
        print(f"❌ Error processing refund: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/payment/methods', methods=['GET'])
def get_payment_methods_api():
    """Get available payment methods"""
    try:
        methods = ph.get_payment_methods()
        
        return jsonify({
            "success": True,
            "methods": methods
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching methods: {e}")
        return jsonify({"error": str(e)}), 500


# ==================== CUSTOMER API ====================

@app.route('/api/customer/<phone>/orders', methods=['GET'])
def get_customer_orders_api(phone):
    """Get customer order history"""
    try:
        limit = request.args.get('limit', 10, type=int)
        orders = om.get_customer_orders(phone, limit)
        
        # Clean and serialize
        for order in orders:
            if '_id' in order:
                del order['_id']
            for key in order:
                if isinstance(order[key], datetime):
                    order[key] = order[key].isoformat()
        
        return jsonify({
            "success": True,
            "orders": orders
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching customer orders: {e}")
        return jsonify({"error": str(e)}), 500


# ==================== ANALYTICS API ====================

@app.route('/api/analytics', methods=['GET'])
@require_api_key
def get_analytics_api():
    """
    Get analytics summary
    Query params: ?days=7
    """
    try:
        days = request.args.get('days', 7, type=int)
        analytics = db.get_analytics(days)
        
        return jsonify({
            "success": True,
            "analytics": analytics
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching analytics: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/analytics/orders/active', methods=['GET'])
@require_api_key
def get_active_orders_api():
    """Get all active orders"""
    try:
        orders = om.get_active_orders()
        
        # Clean and serialize
        for order in orders:
            if '_id' in order:
                del order['_id']
            for key in order:
                if isinstance(order[key], datetime):
                    order[key] = order[key].isoformat()
        
        return jsonify({
            "success": True,
            "count": len(orders),
            "orders": orders
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching active orders: {e}")
        return jsonify({"error": str(e)}), 500


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "Not Found",
        "message": "The requested endpoint does not exist"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred"
    }), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all uncaught exceptions"""
    print(f"❌ Unhandled exception: {error}")
    return jsonify({
        "error": "Server Error",
        "message": str(error)
    }), 500


# ==================== STARTUP ====================

def start_server(host='0.0.0.0', port=5000, debug=False):
    """Start Flask server"""
    print("=" * 60)
    print("🚀 Restaurant E-Commerce API Server")
    print("=" * 60)
    print(f"📍 Running on: http://{host}:{port}")
    print(f"🔑 API Key: {API_KEY}")
    print("\n📡 Available Endpoints:")
    print("   GET  /                     - API Info")
    print("   GET  /health               - Health Check")
    print("   POST /webhook/payment/<id> - Payment Callback")
    print("   POST /api/order/create     - Create Order")
    print("   GET  /api/order/<id>       - Get Order")
    print("   POST /api/payment/initiate - Initiate Payment")
    print("   GET  /api/analytics        - Get Analytics")
    print("\n🔒 Protected endpoints require X-API-Key header")
    print("=" * 60)
    
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    # Run server
    start_server(
        host='0.0.0.0',  # Listen on all interfaces
        port=5000,       # Port 5000 (Streamlit uses 8501)
        debug=True       # Set False in production
    )
    

@app.route('/webhook/jazzcash', methods=['POST'])
def jazzcash_webhook():
    """JazzCash specific webhook"""
    try:
        # Get JazzCash response
        response_data = request.form.to_dict()
        
        # Extract payment ID
        payment_id = response_data.get('pp_TxnRefNo')
        
        if not payment_id:
            return jsonify({"error": "Missing transaction reference"}), 400
        
        # Process callback
        result = ph.handle_payment_callback(payment_id, response_data)
        
        # JazzCash expects specific response format
        return jsonify({
            "pp_ResponseCode": "000" if result['status'] == 'SUCCESS' else "001",
            "pp_ResponseMessage": result.get('message', 'Processed')
        }), 200
        
    except Exception as e:
        print(f"❌ JazzCash webhook error: {e}")
        return jsonify({
            "pp_ResponseCode": "001",
            "pp_ResponseMessage": str(e)
        }), 500


# ==================== ORDER API ====================

@app.route('/api/order/create', methods=['POST'])
@require_api_key
def create_order_api():
    """
    Create new order via API
    
    Request body:
    {
        "customer_phone": "+923001234567",
        "customer_name": "Ahmed Khan",
        "items": [
            {"name": "Chicken Biryani", "qty": 2, "price": 650, "subtotal": 1300}
        ],
        "delivery_address": "123 Main St",
        "delivery_type": "DELIVERY"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['customer_phone', 'customer_name', 'items']
        if not all(field in data for field in required):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Validate items
        is_valid, error_msg = om.validate_order_items(data['items'])
        if not is_valid:
            return jsonify({"error": error_msg}), 400
        
        # Create order
        order = om.create_order(
            customer_phone=data['customer_phone'],
            customer_name=data['customer_name'],
            items=data['items'],
            delivery_address=data.get('delivery_address'),
            special_instructions=data.get('special_instructions'),
            delivery_type=data.get('delivery_type', 'DELIVERY')
        )
        
        return jsonify({
            "success": True,
            "order": {
                "order_id": order['order_id'],
                "total": order['total'],
                "status": order['status'],
                "estimated_delivery": order['estimated_delivery'].isoformat()
            }
        }), 201
        
    except Exception as e:
        print(f"❌ Error creating order: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/order/<order_id>', methods=['GET'])
def get_order_api(order_id):
    """Get order details"""
    try:
        order = om.get_order(order_id)
        
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        # Remove MongoDB _id for JSON serialization
        if '_id' in order:
            del order['_id']
        
        # Convert datetime to ISO format
        for key in order:
            if isinstance(order[key], datetime):
                order[key] = order[key].isoformat()
        
        return jsonify({
            "success": True,
            "order": order
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching order: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/order/<order_id>/status', methods=['PUT'])
@require_api_key
def update_order_status_api(order_id):
    """
    Update order status

    Request body:
    {
        "status": "COOKING",
        "notes": "Optional notes"
    }
    """
    try:
        data = request.get_json()

        if 'status' not in data:
            return jsonify({"error": "Missing status field"}), 400

        # Update status
        success = om.update_status(
            order_id,
            data['status'],
            notes=data.get('notes')
        )

        if success:
            return jsonify({
                "success": True,
                "message": f"Order status updated to {data['status']}"
            }), 200
        else:
            return jsonify({"error": "Failed to update status"}), 500

    except Exception as e:
        print(f"❌ Error updating order status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500