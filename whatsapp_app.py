import streamlit as st
import os
import tempfile
import threading
import time
from rag_engine import RestaurantRAG
from whatsapp_handler import WhatsAppBot

# Page config
st.set_page_config(
    page_title="WhatsApp Bot Manager",
    page_icon="📱",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
        padding: 2rem;
    }
    .stButton>button {
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
    }
    h1, h2, h3 {
        color: white !important;
    }
    .status-box {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'bot_running' not in st.session_state:
    st.session_state.bot_running = False
if 'bot_thread' not in st.session_state:
    st.session_state.bot_thread = None
if 'rag_engine' not in st.session_state:
    st.session_state.rag_engine = None
if 'whatsapp_bot' not in st.session_state:
    st.session_state.whatsapp_bot = None
if 'message_log' not in st.session_state:
    st.session_state.message_log = []

# Header
st.markdown("# 📱 WhatsApp Bot Control Panel")
st.markdown("### Manage your AI-powered WhatsApp menu assistant")

st.markdown("<br>", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Setup", "💬 Live Chat", "📊 Analytics", "⚙️ Settings"])

# TAB 1: SETUP
with tab1:
    st.markdown('<div class="status-box">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🤖 AI Configuration")
        
        provider = st.selectbox("AI Provider", ["groq", "openai"])
        
        if provider == "groq":
            st.info("✅ Groq is FREE!")
            ai_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
            model = st.selectbox("Model", [
                "llama-3.3-70b-versatile",
                "llama-3.1-70b-versatile",
                "llama-3.1-8b-instant"
            ])
        else:
            ai_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
            model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o"])
        
        menu_file = st.file_uploader("Upload Menu PDF", type=['pdf'])
        
        if st.button("🔄 Process Menu", use_container_width=True):
            if not ai_key or not menu_file:
                st.error("Please provide API key and menu PDF")
            else:
                with st.spinner("Processing menu..."):
                    try:
                        # Save temp file
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                            tmp.write(menu_file.getvalue())
                            tmp_path = tmp.name
                        
                        # Initialize RAG
                        st.session_state.rag_engine = RestaurantRAG(
                            api_key=ai_key,
                            model=model,
                            provider=provider
                        )
                        
                        # Process menu
                        st.session_state.rag_engine.process_menu(tmp_path)
                        
                        os.unlink(tmp_path)
                        
                        st.success("✅ Menu processed successfully!")
                        
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    with col2:
        st.markdown("### 📱 WhatsApp Configuration")
        
        st.info("""
        **Green API Setup:**
        1. Go to green-api.com
        2. Create instance ($15/month)
        3. Get Instance ID & Token
        4. Scan QR with WhatsApp
        """)
        
        instance_id = st.text_input("Green API Instance ID", placeholder="7103...")
        api_token = st.text_input("Green API Token", type="password", placeholder="your-token")
        
        st.markdown("---")
        
        # Bot status
        if st.session_state.bot_running:
            st.success("🟢 Bot is RUNNING")
            
            if st.button("🛑 Stop Bot", use_container_width=True, type="primary"):
                st.session_state.bot_running = False
                st.rerun()
        else:
            st.warning("🔴 Bot is STOPPED")
            
            if st.button("▶️ Start Bot", use_container_width=True, type="primary"):
                if not st.session_state.rag_engine:
                    st.error("Please process menu first!")
                elif not instance_id or not api_token:
                    st.error("Please enter Green API credentials!")
                else:
                    try:
                        # Initialize WhatsApp bot
                        st.session_state.whatsapp_bot = WhatsAppBot(
                            instance_id=instance_id,
                            api_token=api_token,
                            rag_engine=st.session_state.rag_engine
                        )
                        
                        st.session_state.bot_running = True
                        st.success("✅ Bot started!")
                        st.info("📱 Send a message to your WhatsApp number to test!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Failed to start bot: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# TAB 2: LIVE CHAT
with tab2:
    st.markdown('<div class="status-box">', unsafe_allow_html=True)
    
    if not st.session_state.bot_running:
        st.warning("⚠️ Bot is not running. Start it in the Setup tab.")
    else:
        st.markdown("### 💬 Live Messages")
        st.caption("Messages will appear here in real-time")
        
        # Auto-refresh
        if st.button("🔄 Refresh Messages"):
            st.rerun()
        
        # Poll for messages
        if st.session_state.whatsapp_bot:
            try:
                notifications = st.session_state.whatsapp_bot.get_notifications()
                
                for notif in notifications:
                    receipt_id = notif.get('receiptId')
                    
                    # Process and respond
                    response = st.session_state.whatsapp_bot.process_message(notif)
                    
                    if response:
                        sender_data = notif.get('senderData', {})
                        sender = sender_data.get('senderName', 'Unknown')
                        message_data = notif.get('messageData', {})
                        text_data = message_data.get('textMessageData', {})
                        question = text_data.get('textMessage', '')
                        
                        # Log message
                        st.session_state.message_log.append({
                            'sender': sender,
                            'question': question,
                            'response': response,
                            'time': time.strftime('%H:%M:%S')
                        })
                        
                        # Send response
                        sender_number = sender_data.get('sender', '').replace('@c.us', '')
                        st.session_state.whatsapp_bot.send_message(sender_number, response)
                    
                    # Delete notification
                    if receipt_id:
                        st.session_state.whatsapp_bot.delete_notification(receipt_id)
            
            except Exception as e:
                st.error(f"Error polling messages: {e}")
        
        # Display message log
        st.markdown("---")
        st.markdown("### 📜 Message History")
        
        for msg in reversed(st.session_state.message_log[-10:]):
            with st.expander(f"👤 {msg['sender']} - {msg['time']}"):
                st.markdown(f"**Question:** {msg['question']}")
                st.markdown(f"**Response:** {msg['response']}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# TAB 3: ANALYTICS
with tab3:
    st.markdown('<div class="status-box">', unsafe_allow_html=True)
    
    st.markdown("### 📊 Bot Analytics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Messages", len(st.session_state.message_log))
    
    with col2:
        unique_users = len(set(msg['sender'] for msg in st.session_state.message_log))
        st.metric("Unique Users", unique_users)
    
    with col3:
        if st.session_state.bot_running:
            st.metric("Status", "🟢 Running")
        else:
            st.metric("Status", "🔴 Stopped")
    
    st.markdown("---")
    
    if st.session_state.message_log:
        st.markdown("### 💬 Recent Conversations")
        
        for msg in reversed(st.session_state.message_log[-5:]):
            st.markdown(f"""
            **{msg['sender']}** at {msg['time']}
            - Q: {msg['question'][:100]}...
            - A: {msg['response'][:100]}...
            """)
    else:
        st.info("No messages yet. Start the bot and send a message!")
    
    st.markdown('</div>', unsafe_allow_html=True)

# TAB 4: SETTINGS
with tab4:
    st.markdown('<div class="status-box">', unsafe_allow_html=True)
    
    st.markdown("### ⚙️ Bot Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Welcome Message")
        welcome_msg = st.text_area(
            "Custom welcome message",
            value="👋 Welcome! I'm your AI menu assistant. Ask me anything about our menu!",
            height=150
        )
        
        st.markdown("#### Auto-Responses")
        auto_reply = st.checkbox("Enable auto-replies", value=True)
        greeting_reply = st.checkbox("Reply to greetings", value=True)
    
    with col2:
        st.markdown("#### Response Settings")
        max_response_length = st.slider("Max response length", 100, 500, 300)
        response_delay = st.slider("Response delay (seconds)", 0, 5, 1)
        
        st.markdown("#### Notifications")
        email_notifications = st.checkbox("Email notifications", value=False)
        if email_notifications:
            notification_email = st.text_input("Email address")
    
    if st.button("💾 Save Settings", use_container_width=True):
        st.success("✅ Settings saved!")
    
    st.markdown("---")
    
    st.markdown("### 🔗 Useful Links")
    st.markdown("""
    - [Green API Dashboard](https://green-api.com/en/personal-area)
    - [Green API Docs](https://green-api.com/en/docs/)
    - [API Status](https://green-api.com/en/status/)
    - [Support](https://green-api.com/en/support/)
    """)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: white;'>
    <p>📱 WhatsApp Bot Manager | Powered by Green API & Groq</p>
    <p>Made with ❤️ for restaurants</p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh for live updates
if st.session_state.bot_running:
    time.sleep(5)
    st.rerun()