# import streamlit as st
# import os
# from pathlib import Path
# from order_manager import OrderManager
# from payment_handler import PaymentHandler, PaymentMethod
# from config import config
# import requests
# import tempfile
# from rag_engine import RestaurantRAG
# import time


# # Default session state
# default_session_state = {
#     "cart": [],
#     "show_cart": False,
#     "show_checkout": False,
#     "messages": [],
#     "pending_question": None,
#     "menu_processed": False,
#     "rag_engine": None,
#     "order_manager": None,
#     "payment_handler": None,
#     "current_order": None,
# }

# for key, value in default_session_state.items():
#     if key not in st.session_state:
#         st.session_state[key] = value

# # Page config
# st.set_page_config(
#     page_title="AI Menu Assistant Pro",
#     page_icon="🤖",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # CSS Styles
# st.markdown("""
# <style>
#     .hero-container {
#         text-align: center;
#         padding: 2rem 1rem;
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         border-radius: 20px;
#         margin-bottom: 2rem;
#     }
#     .hero-title {
#         font-size: 3rem;
#         font-weight: 900;
#         color: white;
#         margin-bottom: 0.5rem;
#     }
#     .hero-subtitle {
#         font-size: 1.5rem;
#         color: rgba(255,255,255,0.9);
#         margin-bottom: 0.5rem;
#     }
#     .hero-caption {
#         font-size: 1rem;
#         color: rgba(255,255,255,0.8);
#     }
#     .stats-container {
#         background: white;
#         padding: 2rem;
#         border-radius: 15px;
#         box-shadow: 0 4px 6px rgba(0,0,0,0.1);
#         margin-bottom: 2rem;
#     }
#     .stat-box {
#         text-align: center;
#         padding: 1rem;
#     }
#     .stat-number {
#         font-size: 2rem;
#         font-weight: bold;
#         color: #667eea;
#         display: block;
#     }
#     .stat-label {
#         font-size: 0.9rem;
#         color: #666;
#         display: block;
#     }
#     .feature-card {
#         background: white;
#         padding: 2rem;
#         border-radius: 15px;
#         box-shadow: 0 4px 6px rgba(0,0,0,0.1);
#         height: 100%;
#     }
#     .feature-icon {
#         font-size: 3rem;
#         margin-bottom: 1rem;
#     }
#     .feature-title {
#         font-size: 1.3rem;
#         font-weight: bold;
#         margin-bottom: 0.5rem;
#         color: #333;
#     }
#     .feature-desc {
#         color: #666;
#         line-height: 1.6;
#     }
#     .premium-badge {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         color: white;
#         padding: 0.2rem 0.5rem;
#         border-radius: 5px;
#         font-size: 0.7rem;
#         margin-left: 0.5rem;
#     }
#     .chat-container, .chat-content {
#         background: white;
#         padding: 2rem;
#         border-radius: 15px;
#         box-shadow: 0 4px 6px rgba(0,0,0,0.1);
#         margin-bottom: 2rem;
#     }
# </style>
# """, unsafe_allow_html=True)

# # Get API key
# try:
#     GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
#     API_KEY_SET = True
# except:
#     GROQ_API_KEY = None
#     API_KEY_SET = False


# # Cart Functions
# def add_to_cart(item_name: str, price: float):
#     """Add item to cart"""
#     for item in st.session_state.cart:
#         if item['name'] == item_name:
#             item['qty'] += 1
#             item['subtotal'] = item['qty'] * item['price']
#             st.toast(f"✅ Added another {item_name}!")
#             return
    
#     st.session_state.cart.append({
#         "name": item_name,
#         "qty": 1,
#         "price": price,
#         "subtotal": price
#     })
#     st.toast(f"✅ Added {item_name} to cart!")

# def remove_from_cart(index: int):
#     """Remove item from cart"""
#     if 0 <= index < len(st.session_state.cart):
#         item = st.session_state.cart.pop(index)
#         st.success(f"🗑️ Removed {item['name']}")

# def update_cart_quantity(index: int, new_qty: int):
#     """Update item quantity"""
#     if 0 <= index < len(st.session_state.cart):
#         if new_qty <= 0:
#             remove_from_cart(index)
#         else:
#             item = st.session_state.cart[index]
#             item['qty'] = new_qty
#             item['subtotal'] = new_qty * item['price']

# def get_cart_total() -> float:
#     """Calculate cart total"""
#     return sum(item['subtotal'] for item in st.session_state.cart)

# def clear_cart():
#     """Clear cart"""
#     st.session_state.cart = []
#     st.success("🗑️ Cart cleared!")


# # Initialize managers
# if st.session_state.order_manager is None:
#     try:
#         st.session_state.order_manager = OrderManager()
#     except Exception as e:
#         st.warning(f"⚠️ Order system unavailable: {e}")

# if st.session_state.payment_handler is None:
#     try:
#         st.session_state.payment_handler = PaymentHandler()
#     except Exception as e:
#         st.warning(f"⚠️ Payment system unavailable: {e}")


# # Sidebar
# with st.sidebar:
#     st.markdown("# ⚙️ Control Center")
#     st.markdown("---")
    
#     restaurant_name = st.text_input("Restaurant Name", "Demo Restaurant")
#     restaurant_tagline = st.text_input("Tagline", "Delicious food, AI service")
    
#     st.markdown("---")
    
#     if st.session_state.menu_processed:
#         st.success("✅ **System Online**")
#         items_count = len(st.session_state.rag_engine.menu_items) if st.session_state.rag_engine.menu_items else 0
        
#         col1, col2 = st.columns(2)
#         with col1:
#             st.metric("📋 Items", items_count)
#         with col2:
#             st.metric("💬 Chats", len(st.session_state.messages))
        
#         if st.button("🔄 Reset Chat", use_container_width=True):
#             if st.session_state.rag_engine:
#                 st.session_state.rag_engine.reset_conversation()
#             st.session_state.messages = []
#             st.rerun()
#     else:
#         st.info("⏳ **Ready to Launch**")
    
#     st.markdown("---")
    
#     # Cart summary
#     if len(st.session_state.cart) > 0:
#         st.markdown("### 🛒 Cart")
#         cart_total = get_cart_total()
#         items_count = sum(item['qty'] for item in st.session_state.cart)
        
#         st.metric("Items", items_count)
#         st.metric("Total", f"Rs {int(cart_total)}")
        
#         col1, col2 = st.columns(2)
#         with col1:
#             if st.button("👁️ View", use_container_width=True, key="sidebar_view_cart"):
#                 st.session_state.show_cart = True
#                 st.session_state.show_checkout = False
#                 st.rerun()
#         with col2:
#             if st.button("💳 Checkout", use_container_width=True, type="primary", key="sidebar_checkout"):
#                 st.session_state.show_checkout = True
#                 st.session_state.show_cart = False
#                 st.rerun()
#     else:
#         st.info("🛒 Cart is empty")
    
#     st.markdown("---")
#     st.markdown("""
#     <div style='text-align: center; padding: 1rem 0;'>
#         <p style='font-weight: 700; color: #667eea;'>⚡ Powered by</p>
#         <p style='color: #6b7280;'>Groq AI • LangChain • FAISS</p>
#         <p style='font-weight: 800; font-size: 1.1rem; margin-top: 1rem;'>Made by Shahbaz</p>
#         <p style='font-size: 0.8rem; color: #9ca3af;'>Full-Stack AI Developer</p>
#     </div>
#     """, unsafe_allow_html=True)


# # Check API key
# if not API_KEY_SET:
#     st.error("⚠️ **API Key Not Configured** - Add GROQ_API_KEY in Streamlit secrets")
#     st.stop()


# # Hero Section
# st.markdown(f"""
# <div class='hero-container'>
#     <div class='hero-title'>{restaurant_name}</div>
#     <div class='hero-subtitle'>{restaurant_tagline}</div>
#     <div class='hero-caption'>🤖 AI-Powered Menu • ⚡ Instant Answers • 🌍 24/7 Available</div>
# </div>
# """, unsafe_allow_html=True)

# st.write("##")


# # ============================================
# # MAIN CONTENT ROUTING
# # ============================================

# # CHECKOUT VIEW
# if st.session_state.show_checkout:
#     st.markdown('<div class="chat-content">', unsafe_allow_html=True)
#     st.markdown("### 💳 Checkout")
    
#     if len(st.session_state.cart) == 0:
#         st.warning("Your cart is empty!")
#         if st.button("← Back to Menu"):
#             st.session_state.show_checkout = False
#             st.rerun()
#     else:
#         with st.expander("📋 Order Summary", expanded=True):
#             for item in st.session_state.cart:
#                 st.write(f"{item['qty']}x {item['name']} - Rs {int(item['subtotal'])}")
            
#             st.markdown("---")
#             subtotal = get_cart_total()
#             delivery_fee = 50
#             tax = subtotal * 0.05
#             total = subtotal + delivery_fee + tax
            
#             st.write(f"**Subtotal:** Rs {int(subtotal)}")
#             st.write(f"**Delivery Fee:** Rs {int(delivery_fee)}")
#             st.write(f"**Tax (5%):** Rs {int(tax)}")
#             st.markdown(f"### **Total: Rs {int(total)}**")
        
#         st.markdown("---")
#         st.markdown("### 📝 Delivery Details")
        
#         col1, col2 = st.columns(2)
#         with col1:
#             customer_name = st.text_input("Full Name *", placeholder="Ahmed Khan")
#         with col2:
#             customer_phone = st.text_input("Phone *", placeholder="+92 300 1234567")
        
#         delivery_address = st.text_area("Address *", placeholder="House #123, Street 4, DHA Phase 2")
#         special_instructions = st.text_area("Special Instructions", placeholder="Extra spicy, no onions")
        
#         st.markdown("---")
#         st.markdown("### 💰 Payment Method")
#         payment_method = st.radio("Choose:", ["💵 Cash on Delivery", "💳 Mock Payment", "📱 JazzCash"], label_visibility="collapsed")
        
#         st.markdown("---")
#         col1, col2 = st.columns(2)
#         with col1:
#             if st.button("← Back to Cart", use_container_width=True):
#                 st.session_state.show_checkout = False
#                 st.session_state.show_cart = True
#                 st.rerun()
#         with col2:
#             if st.button("🚀 Place Order", use_container_width=True, type="primary"):
#                 if not customer_name or not customer_phone or not delivery_address:
#                     st.error("⚠️ Please fill all required fields!")
#                 elif not st.session_state.order_manager:
#                     st.error("⚠️ Order system unavailable")
#                 else:
#                     try:
#                         with st.spinner("Creating order..."):
#                             order = st.session_state.order_manager.create_order(
#                                 customer_phone=customer_phone,
#                                 customer_name=customer_name,
#                                 items=st.session_state.cart,
#                                 delivery_address=delivery_address,
#                                 special_instructions=special_instructions,
#                                 delivery_type="DELIVERY"
#                             )
                            
#                             method = PaymentMethod.CASH if "Cash" in payment_method else PaymentMethod.MOCK
#                             payment_result = st.session_state.payment_handler.initiate_payment(
#                                 order_id=order['order_id'],
#                                 amount=order['total'],
#                                 customer_phone=customer_phone,
#                                 method=method
#                             )
                            
#                             if payment_result['status'] == 'SUCCESS':
#                                 st.balloons()
#                                 st.success("✅ Order placed successfully!")
#                                 st.info(f"""
# **Order ID:** {order['order_id']}  
# **Total:** Rs {int(order['total'])}  
# **Payment:** {payment_result['method']}  
# **Status:** {payment_result['message']}  
# **Estimated Delivery:** {order['estimated_delivery'].strftime('%I:%M %p')}
#                                 """)
#                                 st.session_state.cart = []
                                
#                                 if st.button("🏠 Back to Menu"):
#                                     st.session_state.show_checkout = False
#                                     st.rerun()
#                             else:
#                                 st.error(f"❌ Payment failed: {payment_result['message']}")
#                     except Exception as e:
#                         st.error(f"❌ Error: {str(e)}")
    
#     st.markdown('</div>', unsafe_allow_html=True)

# # CART VIEW
# elif st.session_state.show_cart:
#     st.markdown('<div class="chat-content">', unsafe_allow_html=True)
#     st.markdown("### 🛒 Shopping Cart")
    
#     if len(st.session_state.cart) == 0:
#         st.info("Your cart is empty!")
#         if st.button("← Back to Menu"):
#             st.session_state.show_cart = False
#             st.rerun()
#     else:
#         for idx, item in enumerate(st.session_state.cart):
#             col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
            
#             with col1:
#                 st.write(f"**{item['name']}**")
#                 st.caption(f"Rs {int(item['price'])} each")
#             with col2:
#                 new_qty = st.number_input("Qty", min_value=0, value=item['qty'], key=f"qty_{idx}", label_visibility="collapsed")
#                 if new_qty != item['qty']:
#                     update_cart_quantity(idx, new_qty)
#                     st.rerun()
#             with col3:
#                 st.write(f"Rs {int(item['subtotal'])}")
#             with col4:
#                 if st.button("🗑️", key=f"remove_{idx}"):
#                     remove_from_cart(idx)
#                     st.rerun()
        
#         st.markdown("---")
        
#         subtotal = get_cart_total()
#         delivery_fee = 50
#         tax = subtotal * 0.05
#         total = subtotal + delivery_fee + tax
        
#         col1, col2 = st.columns([3, 1])
#         with col1:
#             st.write("**Subtotal:**")
#             st.write("**Delivery Fee:**")
#             st.write("**Tax (5%):**")
#             st.markdown("**Total:**")
#         with col2:
#             st.write(f"Rs {int(subtotal)}")
#             st.write(f"Rs {int(delivery_fee)}")
#             st.write(f"Rs {int(tax)}")
#             st.markdown(f"**Rs {int(total)}**")
        
#         st.markdown("---")
        
#         col1, col2, col3 = st.columns(3)
#         with col1:
#             if st.button("← Continue Shopping", use_container_width=True):
#                 st.session_state.show_cart = False
#                 st.rerun()
#         with col2:
#             if st.button("🗑️ Clear Cart", use_container_width=True):
#                 clear_cart()
#                 st.rerun()
#         with col3:
#             if st.button("💳 Proceed to Checkout", use_container_width=True, type="primary"):
#                 st.session_state.show_checkout = True
#                 st.session_state.show_cart = False
#                 st.rerun()
    
#     st.markdown('</div>', unsafe_allow_html=True)

# # UPLOAD VIEW
# elif not st.session_state.menu_processed:
#     col1, col2, col3 = st.columns(3)
    
#     with col1:
#         st.markdown("""
#         <div class='feature-card'>
#             <div class='feature-icon'>💬</div>
#             <div class='feature-title'>Intelligent Chat</div>
#             <div class='feature-desc'>Natural conversations powered by Llama 3.3 70B</div>
#         </div>
#         """, unsafe_allow_html=True)
#     with col2:
#         st.markdown("""
#         <div class='feature-card'>
#             <div class='feature-icon'>📱</div>
#             <div class='feature-title'>WhatsApp Ready<span class='premium-badge'>PRO</span></div>
#             <div class='feature-desc'>Integrate with WhatsApp Business API</div>
#         </div>
#         """, unsafe_allow_html=True)
#     with col3:
#         st.markdown("""
#         <div class='feature-card'>
#             <div class='feature-icon'>⚡</div>
#             <div class='feature-title'>Lightning Fast</div>
#             <div class='feature-desc'>Powered by Groq's inference engine</div>
#         </div>
#         """, unsafe_allow_html=True)
    
#     st.write("##")
#     col1, col2 = st.columns([3, 2])
    
#     with col1:
#         st.markdown("### 📤 Upload Your Restaurant Menu")
#         uploaded_file = st.file_uploader("Drop PDF here", type=['pdf'], label_visibility="collapsed")
        
#         if uploaded_file:
#             st.success(f"✅ {uploaded_file.name} ready!")
    
#     with col2:
#         st.markdown("### 🚀 Quick Start")
#         st.markdown("**1️⃣ Upload** PDF\n\n**2️⃣ Process** menu\n\n**3️⃣ Chat** away!")
    
#     if uploaded_file:
#         col1, col2, col3 = st.columns([1, 2, 1])
#         with col2:
#             if st.button("🚀 LAUNCH AI ASSISTANT", type="primary", use_container_width=True):
#                 with st.spinner("🧠 Training AI..."):
#                     try:
#                         progress_bar = st.progress(0)
                        
#                         with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
#                             tmp.write(uploaded_file.getvalue())
#                             tmp_path = tmp.name
#                         progress_bar.progress(40)
                        
#                         st.session_state.rag_engine = RestaurantRAG(
#                             api_key=GROQ_API_KEY,
#                             model="llama-3.3-70b-versatile",
#                             provider="groq"
#                         )
#                         progress_bar.progress(60)
                        
#                         st.session_state.rag_engine.process_menu(tmp_path)
#                         progress_bar.progress(90)
                        
#                         os.unlink(tmp_path)
#                         progress_bar.progress(100)
                        
#                         st.session_state.menu_processed = True
#                         st.success("🎉 AI Assistant is live!")
#                         st.balloons()
#                         time.sleep(1)
#                         st.rerun()
#                     except Exception as e:
#                         st.error(f"❌ Error: {str(e)}")

# # CHAT INTERFACE
# elif st.session_state.menu_processed and st.session_state.rag_engine:
#     st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
#     st.markdown("### 💭 Try These Questions")
#     cols = st.columns(4)
#     samples = [
#         ("🌱", "What vegan options do you have?"),
#         ("💰", "Show me items under 500 PKR"),
#         ("🌶️", "What's your spiciest dish?"),
#         ("🗃", "List all chicken items")
#     ]

#     for idx, (emoji, question) in enumerate(samples):
#         if cols[idx].button(f"{emoji} {question[:20]}...", use_container_width=True, key=f"q_{idx}"):
#             st.session_state.pending_question = question
#             st.rerun()

#     st.markdown("---")

#     # Display message history
#     for msg_idx, msg in enumerate(st.session_state.messages):
#         avatar = "👤" if msg["role"] == "user" else "🤖"
#         with st.chat_message(msg["role"], avatar=avatar):
#             st.write(msg["content"])
            
#             if msg["role"] == "assistant" and "items_data" in msg:
#                 st.markdown("---")
#                 st.markdown("**🛒 Add to Cart:**")
                
#                 items = msg["items_data"]
#                 cols = st.columns(min(3, len(items)))
                
#                 for item_idx, item_data in enumerate(items):
#                     with cols[item_idx]:
#                         st.markdown(f"**{item_data['name'][:20]}**")
#                         st.caption(f"Rs {int(item_data['price'])}")
                        
#                         if st.button("➕", key=f"hist_{msg_idx}_{item_idx}", use_container_width=True):
#                             add_to_cart(item_data['name'], float(item_data['price']))
#                             time.sleep(0.2)
#                             st.rerun()

#     # Handle new input
#     user_prompt = None
#     if prompt := st.chat_input("💬 Ask about the menu..."):
#         user_prompt = prompt
#     elif st.session_state.pending_question:
#         user_prompt = st.session_state.pending_question
#         st.session_state.pending_question = None

#     if user_prompt:
#         st.session_state.messages.append({"role": "user", "content": user_prompt})
        
#         with st.chat_message("user", avatar="👤"):
#             st.write(user_prompt)
        
#         with st.chat_message("assistant", avatar="🤖"):
#             with st.spinner("🤔 Thinking..."):
#                 try:
#                     response = st.session_state.rag_engine.query(user_prompt)
#                     answer = response['answer']
#                     st.write(answer)
                    
#                     items_to_show = response.get('recommendations', [])
                    
#                     if items_to_show:
#                         st.markdown("---")
#                         st.markdown("**🛒 Add to Cart:**")
                        
#                         cols = st.columns(min(3, len(items_to_show)))
                        
#                         for idx, item_data in enumerate(items_to_show[:3]):
#                             with cols[idx]:
#                                 st.markdown(f"**{item_data['name'][:20]}**")
#                                 st.caption(f"Rs {int(item_data['price'])}")
                                
#                                 # Use unique key with timestamp
#                                 if st.button("➕ Add", key=f"new_{idx}_{len(st.session_state.messages)}", use_container_width=True):
#                                     add_to_cart(item_data['name'], float(item_data['price']))
#                                     time.sleep(0.2)
#                                     st.rerun()
                    
#                     # Save message with items
#                     message_data = {"role": "assistant", "content": answer}
#                     if items_to_show:
#                         message_data["items_data"] = items_to_show[:3]
#                     st.session_state.messages.append(message_data)
                
#                 except Exception as e:
#                     st.error(f"❌ Error: {str(e)}")
    
#     st.markdown('</div>', unsafe_allow_html=True)


# # Footer
# st.markdown("---")
# st.markdown("""
# <div style='text-align: center; padding: 2rem; color: #333;'>
#     <p style='font-size: 2rem; font-weight: 900; margin-bottom: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
#         🤖 AI Menu Assistant Pro
#     </p>
#     <p style='font-size: 1.1rem; color: #666; margin-bottom: 1rem;'>
#         Transforming Restaurants with Artificial Intelligence
#     </p>
#     <p style='color: #888; margin-bottom: 1.5rem;'>
#         Powered by Groq AI • Built with LangChain • Secured by FAISS
#     </p>
#     <div style='display: inline-block; background: rgba(102, 126, 234, 0.1); padding: 1.8rem 2.8rem; border-radius: 24px;'>
#         <p style='font-size: 1.3rem; font-weight: 900; margin-bottom: 0.5rem; background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
#             Made with ❤️ by Shahbaz
#         </p>
#         <p style='color: #666;'>
#             Full-Stack AI Developer | Available for Freelance Projects
#         </p>
#     </div>
#     <p style='margin-top: 2rem; color: #888;'>
#         Open for custom AI solutions | Portfolio project showcasing RAG technology
#     </p>
# </div>
# """, unsafe_allow_html=True)