"""
MongoDB Database Manager
Production-ready with connection pooling and error handling
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from datetime import datetime
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
load_dotenv()


class Database:
    """
    MongoDB Database Manager
    
    Features:
    - Connection pooling
    - Auto-retry
    - Error handling
    - Index management
    """
    
    def __init__(self, connection_string: str = None):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB URI (default: from env or localhost)
        """
        # Get connection string
        if not connection_string:
            connection_string = os.getenv(
                'MONGODB_URI',
                'mongodb://localhost:27017/'  # Local fallback
            )
        
        try:
            # Create client with production settings
            self.client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=5000,  # 5 sec timeout
                maxPoolSize=50,  # Connection pool
                retryWrites=True
            )
            
            # Test connection
            self.client.admin.command('ping')
            print("✅ MongoDB connected successfully!")
            
            # Select database
            self.db = self.client['restaurant_commerce']
            
            # Collections
            self.orders = self.db['orders']
            self.customers = self.db['customers']
            self.payments = self.db['payments']
            self.analytics = self.db['analytics']
            
            # Create indexes for performance
            self._create_indexes()
            
        except ConnectionFailure as e:
            print(f"❌ MongoDB connection failed: {e}")
            print("💡 Make sure MongoDB is running or update MONGODB_URI")
            raise
    
    def _create_indexes(self):
        """Create database indexes for fast queries"""
        try:
            # Order indexes
            self.orders.create_index("order_id", unique=True)
            self.orders.create_index("customer_phone")
            self.orders.create_index("status")
            self.orders.create_index("created_at")
            
            # Customer indexes
            self.customers.create_index("phone", unique=True)
            self.customers.create_index("customer_id", unique=True)
            
            # Payment indexes
            self.payments.create_index("payment_id", unique=True)
            self.payments.create_index("order_id")
            
            print("✅ Database indexes created")
        except Exception as e:
            print(f"⚠️ Index creation warning: {e}")
    
    # ==================== ORDERS ====================
    
    def create_order(self, order_data: Dict) -> str:
        """
        Create new order
        
        Args:
            order_data: Order information
            
        Returns:
            order_id
        """
        try:
            # Add timestamp
            order_data['created_at'] = datetime.now()
            order_data['updated_at'] = datetime.now()
            
            # Insert
            result = self.orders.insert_one(order_data)
            
            print(f"✅ Order created: {order_data['order_id']}")
            return order_data['order_id']
            
        except Exception as e:
            print(f"❌ Error creating order: {e}")
            raise
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """Get order by ID"""
        try:
            order = self.orders.find_one({"order_id": order_id})
            return order
        except Exception as e:
            print(f"❌ Error fetching order: {e}")
            return None
    
    def update_order_status(self, order_id: str, new_status: str, **kwargs) -> bool:
        """
        Update order status
        
        Args:
            order_id: Order ID
            new_status: New status
            **kwargs: Additional fields to update
        """
        try:
            update_data = {
                "status": new_status,
                "updated_at": datetime.now(),
                f"{new_status.lower()}_at": datetime.now()
            }
            
            # Add any additional fields
            update_data.update(kwargs)
            
            result = self.orders.update_one(
                {"order_id": order_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                print(f"✅ Order {order_id} status: {new_status}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Error updating order: {e}")
            return False
    
    def get_customer_orders(self, customer_phone: str, limit: int = 10) -> List[Dict]:
        """Get customer's order history"""
        try:
            orders = list(
                self.orders.find({"customer_phone": customer_phone})
                .sort("created_at", -1)
                .limit(limit)
            )
            return orders
        except Exception as e:
            print(f"❌ Error fetching customer orders: {e}")
            return []
    
    def get_active_orders(self) -> List[Dict]:
        """Get all active orders (not delivered/cancelled)"""
        try:
            active_statuses = [
                "PENDING_PAYMENT", "PAID", "CONFIRMED",
                "COOKING", "READY", "DISPATCHED"
            ]
            
            orders = list(
                self.orders.find({"status": {"$in": active_statuses}})
                .sort("created_at", -1)
            )
            return orders
        except Exception as e:
            print(f"❌ Error fetching active orders: {e}")
            return []
    
    # ==================== CUSTOMERS ====================
    
    def create_customer(self, customer_data: Dict) -> str:
        """Create or update customer profile"""
        try:
            customer_data['created_at'] = datetime.now()
            customer_data['updated_at'] = datetime.now()
            
            # Upsert (update if exists, insert if not)
            result = self.customers.update_one(
                {"phone": customer_data['phone']},
                {"$set": customer_data},
                upsert=True
            )
            
            print(f"✅ Customer profile updated: {customer_data['phone']}")
            return customer_data['phone']
            
        except Exception as e:
            print(f"❌ Error creating customer: {e}")
            raise
    
    def get_customer(self, phone: str) -> Optional[Dict]:
        """Get customer by phone"""
        try:
            customer = self.customers.find_one({"phone": phone})
            return customer
        except Exception as e:
            print(f"❌ Error fetching customer: {e}")
            return None
    
    def update_customer_preferences(self, phone: str, preferences: Dict) -> bool:
        """Update customer preferences"""
        try:
            result = self.customers.update_one(
                {"phone": phone},
                {
                    "$set": {
                        "preferences": preferences,
                        "updated_at": datetime.now()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Error updating preferences: {e}")
            return False
    
    # ==================== PAYMENTS ====================
    
    def create_payment(self, payment_data: Dict) -> str:
        """Record payment transaction"""
        try:
            payment_data['created_at'] = datetime.now()
            
            result = self.payments.insert_one(payment_data)
            
            print(f"✅ Payment recorded: {payment_data['payment_id']}")
            return payment_data['payment_id']
            
        except Exception as e:
            print(f"❌ Error recording payment: {e}")
            raise
    
    def update_payment_status(self, payment_id: str, status: str, **kwargs) -> bool:
        """Update payment status"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.now()
            }
            update_data.update(kwargs)
            
            result = self.payments.update_one(
                {"payment_id": payment_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"❌ Error updating payment: {e}")
            return False
    
    def get_payment(self, payment_id: str) -> Optional[Dict]:
        """Get payment by ID"""
        try:
            payment = self.payments.find_one({"payment_id": payment_id})
            return payment
        except Exception as e:
            print(f"❌ Error fetching payment: {e}")
            return None
    
    # ==================== ANALYTICS ====================
    
    def log_event(self, event_type: str, event_data: Dict):
        """Log analytics event"""
        try:
            event = {
                "event_type": event_type,
                "data": event_data,
                "timestamp": datetime.now()
            }
            
            self.analytics.insert_one(event)
        except Exception as e:
            print(f"⚠️ Analytics logging failed: {e}")
    
    def get_analytics(self, days: int = 7) -> Dict:
        """Get analytics summary"""
        try:
            from datetime import timedelta
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Total orders
            total_orders = self.orders.count_documents({
                "created_at": {"$gte": start_date}
            })
            
            # Total revenue
            revenue_pipeline = [
                {"$match": {
                    "status": {"$in": ["PAID", "CONFIRMED", "COOKING", "READY", "DISPATCHED", "DELIVERED"]},
                    "created_at": {"$gte": start_date}
                }},
                {"$group": {
                    "_id": None,
                    "total": {"$sum": "$total"}
                }}
            ]
            
            revenue_result = list(self.orders.aggregate(revenue_pipeline))
            total_revenue = revenue_result[0]['total'] if revenue_result else 0
            
            # Unique customers
            unique_customers = len(
                self.orders.distinct("customer_phone", {
                    "created_at": {"$gte": start_date}
                })
            )
            
            # Popular items
            items_pipeline = [
                {"$match": {"created_at": {"$gte": start_date}}},
                {"$unwind": "$items"},
                {"$group": {
                    "_id": "$items.name",
                    "count": {"$sum": "$items.qty"}
                }},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            
            popular_items = list(self.orders.aggregate(items_pipeline))
            
            return {
                "period_days": days,
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "unique_customers": unique_customers,
                "popular_items": popular_items,
                "avg_order_value": total_revenue / total_orders if total_orders > 0 else 0
            }
            
        except Exception as e:
            print(f"❌ Error fetching analytics: {e}")
            return {}
    
    # ==================== UTILITIES ====================
    
    def health_check(self) -> bool:
        """Check if database connection is healthy"""
        try:
            self.client.admin.command('ping')
            return True
        except:
            return False
    
    def close(self):
        """Close database connection"""
        try:
            self.client.close()
            print("✅ MongoDB connection closed")
        except Exception as e:
            print(f"⚠️ Error closing connection: {e}")


# Singleton instance
_db_instance = None

def get_database() -> Database:
    """Get database instance (singleton pattern)"""
    global _db_instance
    
    if _db_instance is None:
        _db_instance = Database()
    
    return _db_instance


# Example usage
if __name__ == "__main__":
    print("🧪 Testing Database Connection...\n")
    
    try:
        # Initialize
        db = Database()
        
        # Health check
        if db.health_check():
            print("✅ Database is healthy!\n")
        
        # Test order creation
        test_order = {
            "order_id": "TEST001",
            "customer_phone": "+923001234567",
            "items": [
                {"name": "Chicken Biryani", "qty": 2, "price": 650}
            ],
            "total": 1300,
            "status": "PENDING_PAYMENT"
        }
        
        db.create_order(test_order)
        print(f"✅ Test order created: {test_order['order_id']}\n")
        
        # Fetch it back
        fetched = db.get_order("TEST001")
        print(f"✅ Fetched order: {fetched['order_id']}\n")
        
        # Update status
        db.update_order_status("TEST001", "PAID")
        print("✅ Order status updated\n")
        
        # Get analytics
        analytics = db.get_analytics(days=30)
        print(f"📊 Analytics: {analytics}\n")
        
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        db.close()