"""
WhatsApp Integration using Green API
BEST for Pakistan - $15/month unlimited messages
"""

import requests
import time
from typing import Dict, Optional, List
from rag_engine import RestaurantRAG


class WhatsAppBot:
    """
    WhatsApp Bot using Green API
    Easy setup, affordable, reliable
    """
    
    def __init__(self, 
                 instance_id: str,
                 api_token: str,
                 rag_engine: RestaurantRAG):
        """
        Initialize WhatsApp bot
        
        Args:
            instance_id: Your Green API instance ID
            api_token: Your Green API token
            rag_engine: The RestaurantRAG engine
        """
        self.instance_id = instance_id
        self.api_token = api_token
        self.rag_engine = rag_engine
        self.base_url = f"https://api.green-api.com/waInstance{instance_id}"
        
        print(f"✅ WhatsApp bot initialized for instance: {instance_id}")
    
    def send_message(self, phone_number: str, message: str) -> bool:
        """
        Send WhatsApp message
        
        Args:
            phone_number: Recipient number (format: 923001234567)
            message: Message text
            
        Returns:
            True if sent successfully
        """
        url = f"{self.base_url}/sendMessage/{self.api_token}"
        
        payload = {
            "chatId": f"{phone_number}@c.us",
            "message": message
        }
        
        try:
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                print(f"✅ Message sent to {phone_number}")
                return True
            else:
                print(f"❌ Failed to send: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False
    
    def get_notifications(self) -> List[Dict]:
        """
        Get incoming messages
        
        Returns:
            List of message notifications
        """
        url = f"{self.base_url}/receiveNotification/{self.api_token}"
        
        try:
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                return [data] if data else []
            else:
                print(f"❌ Failed to get notifications: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting notifications: {e}")
            return []
    
    def delete_notification(self, receipt_id: int) -> bool:
        """Delete processed notification"""
        url = f"{self.base_url}/deleteNotification/{self.api_token}/{receipt_id}"
        
        try:
            response = requests.delete(url)
            return response.status_code == 200
        except:
            return False
    
    def process_message(self, notification: Dict) -> Optional[str]:
        """
        Process incoming message and generate response
        
        Args:
            notification: Message notification from Green API
            
        Returns:
            Response message or None
        """
        try:
            # Extract message details
            msg_type = notification.get('typeWebhook')
            
            if msg_type != 'incomingMessageReceived':
                return None
            
            message_data = notification.get('messageData', {})
            sender_data = notification.get('senderData', {})
            
            # Get sender info
            sender_number = sender_data.get('sender', '').replace('@c.us', '')
            sender_name = sender_data.get('senderName', 'Customer')
            
            # Get message text
            text_data = message_data.get('textMessageData', {})
            message_text = text_data.get('textMessage', '')
            
            if not message_text:
                return None
            
            print(f"📱 Message from {sender_name} ({sender_number}): {message_text}")
            
            # Handle special commands
            if message_text.lower() in ['/start', 'hi', 'hello', 'menu']:
                response = self._get_welcome_message()
            elif message_text.lower() == '/help':
                response = self._get_help_message()
            else:
                # Query the menu using RAG
                try:
                    result = self.rag_engine.query(message_text)
                    response = result['answer']
                except Exception as e:
                    response = "Sorry, I couldn't process that. Please try asking about specific menu items or prices."
                    print(f"❌ RAG error: {e}")
            
            return response
            
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            return "Sorry, I encountered an error. Please try again."
    
    def _get_welcome_message(self) -> str:
        """Welcome message"""
        return """👋 Welcome to our restaurant!

I'm your AI menu assistant. I can help you with:

🍽️ Menu items and descriptions
💰 Prices and special offers
🌱 Dietary options (vegan, halal, etc.)
🌶️ Spice levels
📋 Recommendations

Just ask me anything! For example:
• "What vegan options do you have?"
• "Show me items under 500 PKR"
• "What's your spiciest dish?"

Type /help for more info."""
    
    def _get_help_message(self) -> str:
        """Help message"""
        return """ℹ️ How to use this bot:

Just type your question naturally! Examples:

💰 Price queries:
• "Items under 500 rupees"
• "What's the price of biryani?"

🍽️ Menu questions:
• "What chicken dishes do you have?"
• "Do you have vegetarian options?"

🌶️ Preferences:
• "Something not too spicy"
• "Your most popular dish"

I'm here 24/7 to help! 🤖"""
    
    def start_polling(self, interval: int = 5):
        """
        Start polling for new messages
        
        Args:
            interval: Seconds between polls (default: 5)
        """
        print(f"🤖 WhatsApp bot started! Polling every {interval} seconds...")
        print("📱 Send a message to your WhatsApp number to test!")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Get new notifications
                notifications = self.get_notifications()
                
                for notification in notifications:
                    receipt_id = notification.get('receiptId')
                    
                    # Process message
                    response = self.process_message(notification)
                    
                    if response:
                        # Get sender number
                        sender_data = notification.get('senderData', {})
                        sender_number = sender_data.get('sender', '').replace('@c.us', '')
                        
                        # Send response
                        self.send_message(sender_number, response)
                    
                    # Delete processed notification
                    if receipt_id:
                        self.delete_notification(receipt_id)
                
                # Wait before next poll
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
        except Exception as e:
            print(f"\n❌ Bot error: {e}")


# Flask webhook server (for production)
def create_webhook_server(whatsapp_bot: WhatsAppBot):
    """
    Create Flask server for webhooks (better than polling)
    Use this for production!
    """
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    
    @app.route('/webhook', methods=['POST'])
    def webhook():
        """Handle incoming webhooks from Green API"""
        try:
            notification = request.json
            
            # Process message
            response = whatsapp_bot.process_message(notification)
            
            if response:
                # Get sender
                sender_data = notification.get('senderData', {})
                sender_number = sender_data.get('sender', '').replace('@c.us', '')
                
                # Send response
                whatsapp_bot.send_message(sender_number, response)
            
            return jsonify({"status": "success"}), 200
            
        except Exception as e:
            print(f"❌ Webhook error: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        return jsonify({"status": "healthy"}), 200
    
    return app


# Example usage
if __name__ == "__main__":
    print("""
    🚀 GREEN API WHATSAPP BOT SETUP
    
    Step 1: Sign up at green-api.com
    Step 2: Create an instance ($15/month)
    Step 3: Get your Instance ID and Token
    Step 4: Scan QR code with WhatsApp
    Step 5: Run this script!
    
    ═══════════════════════════════════════
    """)
    
    # TODO: Replace with your credentials
    INSTANCE_ID = "YOUR_INSTANCE_ID"
    API_TOKEN = "YOUR_API_TOKEN"
    
    if INSTANCE_ID == "YOUR_INSTANCE_ID":
        print("❌ Please set your Green API credentials first!")
        print("\nGet them at: https://green-api.com")
    else:
        # Initialize RAG engine (you'll need to process menu first)
        from rag_engine import RestaurantRAG
        
        print("Initializing RAG engine...")
        rag = RestaurantRAG(
            api_key="your_groq_key",
            model="llama-3.3-70b-versatile",
            provider="groq"
        )
        
        # Process menu
        print("Processing menu...")
        rag.process_menu("path/to/your/menu.pdf")
        
        # Start bot
        bot = WhatsAppBot(
            instance_id=INSTANCE_ID,
            api_token=API_TOKEN,
            rag_engine=rag
        )
        
        # Start polling
        bot.start_polling(interval=5)