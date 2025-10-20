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

# # -------------------------------------------
# # Page config
# st.set_page_config(
#     page_title="AI Menu Assistant Pro | Restaurant Intelligence",
#     page_icon="🤖",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # ADD MISSING CSS STYLES
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
#     .upload-container {
#         background: white;
#         padding: 2rem;
#         border-radius: 15px;
#         box-shadow: 0 4px 6px rgba(0,0,0,0.1);
#         margin: 2rem 0;
#     }
#     .chat-container {
#         background: white;
#         padding: 2rem;
#         border-radius: 15px;
#         box-shadow: 0 4px 6px rgba(0,0,0,0.1);
#         margin-bottom: 2rem;
#     }
#     .chat-content {
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


# def add_to_cart(item_name: str, price: float):
#     """Add item to cart"""
#     for item in st.session_state.cart:
#         if item['name'] == item_name:
#             item['qty'] += 1
#             item['subtotal'] = item['qty'] * item['price']
#             st.success(f"✅ Added another {item_name}!")
#             return
    
#     st.session_state.cart.append({
#         "name": item_name,
#         "qty": 1,
#         "price": price,
#         "subtotal": price
#     })
#     st.success(f"✅ Added {item_name} to cart!")

# def remove_from_cart(index: int):
#     """Remove item from cart"""
#     if 0 <= index < len(st.session_state.cart):
#         item = st.session_state.cart.pop(index)
#         st.success(f"🗑️ Removed {item['name']} from cart")

# def update_cart_quantity(index: int, new_qty: int):
#     """Update item quantity in cart"""
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
#     """Clear all items from cart"""
#     st.session_state.cart = []
#     st.success("🗑️ Cart cleared!")


# # Initialize Order Manager and Payment Handler
# if st.session_state.order_manager is None:
#     try:
#         st.session_state.order_manager = OrderManager()
#     except Exception as e:
#         st.error(f"⚠️ Order system not available: {e}")

# if st.session_state.payment_handler is None:
#     try:
#         st.session_state.payment_handler = PaymentHandler()
#     except Exception as e:
#         st.error(f"⚠️ Payment system not available: {e}")


# # Sidebar
# with st.sidebar:
#     st.markdown("# ⚙️ Control Center")
#     st.markdown("---")
    
#     st.markdown("### 🪧 Restaurant Branding")
#     restaurant_name = st.text_input(
#         "Restaurant Name",
#         "Demo Restaurant",
#         help="Your restaurant's name"
#     )
    
#     restaurant_tagline = st.text_input(
#         "Tagline",
#         "Delicious food, AI service",
#         help="Your restaurant's motto"
#     )
    
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
    
#     st.markdown("### 🔧 System Specifications")
#     st.markdown("""
#     **AI Model:** Llama 3.3 70B  
#     **Provider:** Groq ⚡  
#     **Embeddings:** HuggingFace  
#     **Vector DB:** FAISS  
#     **Status:** 🟢 Online  
#     """)
    
#     st.markdown("---")
    
#     st.markdown("### 📊 Portfolio Stats")
#     st.markdown("""
#     **Speed:** <1s response  
#     **Accuracy:** 95%+  
#     **Languages:** Multi-lingual  
#     **Scalable:** Yes  
#     """)
    
#     st.markdown("---")
    
#     st.markdown("""
#     <div style='text-align: center; padding: 2rem 0; font-size: 0.9rem;'>
#         <p style='margin: 0.5rem 0; font-weight: 700; color: #667eea;'>⚡ Powered by</p>
#         <p style='margin: 0.3rem 0; color: #6b7280;'>Groq AI • LangChain • FAISS</p>
#         <p style='margin: 1.5rem 0 0.5rem 0; font-weight: 800; font-size: 1.1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>Made by Shahbaz</p>
#         <p style='margin: 0.3rem 0; font-size: 0.8rem; color: #9ca3af;'>Full-Stack AI Developer</p>
#     </div>
#     """, unsafe_allow_html=True)

#     st.markdown("---")
    
#     # Cart summary in sidebar
#     if len(st.session_state.cart) > 0:
#         st.markdown("### 🛒 Cart")
#         cart_total = get_cart_total()
#         items_count = sum(item['qty'] for item in st.session_state.cart)
        
#         st.metric("Items", items_count)
#         st.metric("Total", f"Rs {int(cart_total)}")
        
#         col1, col2 = st.columns(2)
#         with col1:
#             if st.button("👁️ View", use_container_width=True):
#                 st.session_state.show_cart = True
#                 st.session_state.show_checkout = False
#                 st.rerun()
#         with col2:
#             if st.button("💳 Checkout", use_container_width=True, type="primary"):
#                 st.session_state.show_checkout = True
#                 st.session_state.show_cart = False
#                 st.rerun()
#     else:
#         st.info("🛒 Cart is empty")


# # API Key Check
# if not API_KEY_SET:
#     st.error("""
#     ⚠️ **API Key Not Configured**
    
#     The owner needs to add the Groq API key in Streamlit secrets.
    
#     **Setup Instructions:**
#     1. Go to Streamlit Dashboard
#     2. Navigate to App Settings → Secrets
#     3. Add: `GROQ_API_KEY = "your_groq_key_here"`
#     """)
#     st.stop()

# # Hero Section
# st.markdown(f"""
# <div class='hero-container'>
#     <div class='hero-title'>{restaurant_name}</div>
#     <div class='hero-subtitle'>{restaurant_tagline}</div>
#     <div class='hero-caption'>🤖 AI-Powered Menu Intelligence • ⚡ Instant Answers • 🌍 24/7 Available</div>
# </div>
# """, unsafe_allow_html=True)

# st.write("##")
# st.write("##")

# # Stats Bar (only visible if menu processed)
# if st.session_state.menu_processed:
#     items_count = len(st.session_state.rag_engine.menu_items) if st.session_state.rag_engine.menu_items else 0
    
#     st.markdown(f"""
#     <div class='stats-container'>
#         <div style='display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap; gap: 1rem; position: relative;'>
#             <div class='stat-box'>
#                 <span class='stat-number'>{items_count}</span>
#                 <span class='stat-label'>Menu Items</span>
#             </div>
#             <div class='stat-box'>
#                 <span class='stat-number'>{len(st.session_state.messages)}</span>
#                 <span class='stat-label'>Conversations</span>
#             </div>
#             <div class='stat-box'>
#                 <span class='stat-number'>24/7</span>
#                 <span class='stat-label'>Available</span>
#             </div>
#             <div class='stat-box'>
#                 <span class='stat-number'>⚡</span>
#                 <span class='stat-label'>Lightning Fast</span>
#             </div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)


# # ============================================
# # MAIN CONTENT AREA - FIXED CONDITIONAL FLOW
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
#         # Order summary
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
        
#         # Customer details form
#         st.markdown("### 📝 Delivery Details")
        
#         col1, col2 = st.columns(2)
#         with col1:
#             customer_name = st.text_input(
#                 "Full Name *",
#                 placeholder="Ahmed Khan"
#             )
#         with col2:
#             customer_phone = st.text_input(
#                 "Phone Number *",
#                 placeholder="+92 300 1234567"
#             )
        
#         delivery_address = st.text_area(
#             "Delivery Address *",
#             placeholder="House #123, Street 4, DHA Phase 2, Karachi"
#         )
        
#         special_instructions = st.text_area(
#             "Special Instructions (Optional)",
#             placeholder="Extra spicy, no onions, ring the bell twice"
#         )
        
#         st.markdown("---")
        
#         # Payment method selection
#         st.markdown("### 💰 Payment Method")
        
#         payment_method = st.radio(
#             "Choose payment method:",
#             ["💵 Cash on Delivery", "💳 Mock Payment (Demo)", "📱 JazzCash (Coming Soon)"],
#             label_visibility="collapsed"
#         )
        
#         st.markdown("---")
        
#         # Place order button
#         col1, col2 = st.columns([1, 1])
        
#         with col1:
#             if st.button("← Back to Cart", use_container_width=True):
#                 st.session_state.show_checkout = False
#                 st.session_state.show_cart = True
#                 st.rerun()
        
#         with col2:
#             if st.button("🚀 Place Order", use_container_width=True, type="primary"):
#                 # Validate inputs
#                 if not customer_name or not customer_phone or not delivery_address:
#                     st.error("⚠️ Please fill in all required fields!")
#                 elif not st.session_state.order_manager:
#                     st.error("⚠️ Order system not available. Please try again later.")
#                 else:
#                     try:
#                         with st.spinner("Creating your order..."):
#                             # Create order
#                             order = st.session_state.order_manager.create_order(
#                                 customer_phone=customer_phone,
#                                 customer_name=customer_name,
#                                 items=st.session_state.cart,
#                                 delivery_address=delivery_address,
#                                 special_instructions=special_instructions if special_instructions else None,
#                                 delivery_type="DELIVERY"
#                             )
                            
#                             st.session_state.current_order = order
                            
#                             # Process payment
#                             if "Cash on Delivery" in payment_method:
#                                 method = PaymentMethod.CASH
#                             elif "Mock Payment" in payment_method:
#                                 method = PaymentMethod.MOCK
#                             else:
#                                 method = PaymentMethod.JAZZCASH
                            
#                             payment_result = st.session_state.payment_handler.initiate_payment(
#                                 order_id=order['order_id'],
#                                 amount=order['total'],
#                                 customer_phone=customer_phone,
#                                 method=method
#                             )
                            
#                             if payment_result['status'] == 'SUCCESS':
#                                 st.balloons()
#                                 st.success("✅ Order placed successfully!")
                                
#                                 # Show order confirmation
#                                 st.markdown("---")
#                                 st.markdown("### 🎉 Order Confirmed!")
                                
#                                 st.info(f"""
# **Order ID:** {order['order_id']}

# **Total:** Rs {int(order['total'])}

# **Payment:** {payment_result['method']}

# **Status:** {payment_result['message']}

# **Estimated Delivery:** {order['estimated_delivery'].strftime('%I:%M %p')}

# We've sent a confirmation to your phone!
#                                 """)
                                
#                                 # Clear cart
#                                 st.session_state.cart = []
                                
#                                 # Option to track order
#                                 if st.button("📦 Track My Order"):
#                                     st.session_state.show_checkout = False
#                                     st.rerun()
                                
#                                 if st.button("🏠 Back to Menu"):
#                                     st.session_state.show_checkout = False
#                                     st.rerun()
                            
#                             else:
#                                 st.error(f"❌ Payment failed: {payment_result['message']}")
                    
#                     except Exception as e:
#                         st.error(f"❌ Error placing order: {str(e)}")
#                         st.info("💡 Please try again or contact support.")
    
#     st.markdown('</div>', unsafe_allow_html=True)

# # CART VIEW
# elif st.session_state.show_cart:
#     st.markdown('<div class="chat-content">', unsafe_allow_html=True)
    
#     st.markdown("### 🛒 Shopping Cart")
    
#     if len(st.session_state.cart) == 0:
#         st.info("Your cart is empty. Add items by clicking the 🛒 button on menu items!")
        
#         if st.button("← Back to Menu"):
#             st.session_state.show_cart = False
#             st.rerun()
#     else:
#         # Display cart items
#         for idx, item in enumerate(st.session_state.cart):
#             col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
            
#             with col1:
#                 st.write(f"**{item['name']}**")
#                 st.caption(f"Rs {int(item['price'])} each")
            
#             with col2:
#                 # Quantity selector
#                 new_qty = st.number_input(
#                     "Qty",
#                     min_value=0,
#                     value=item['qty'],
#                     key=f"qty_{idx}",
#                     label_visibility="collapsed"
#                 )
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
        
#         # Cart summary
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
        
#         # Actions
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

# # MENU UPLOAD VIEW (if menu not processed yet)
# elif not st.session_state.menu_processed:
#     # Features Section
#     col1, col2, col3 = st.columns(3)
    
#     with col1:
#         st.markdown("""
#         <div class='feature-card'>
#             <div class='feature-icon'>💬</div>
#             <div class='feature-title'>Intelligent Chat</div>
#             <div class='feature-desc'>
#                 Natural conversations powered by Llama 3.3 70B. 
#                 Understands context, preferences, dietary restrictions, 
#                 and provides personalized recommendations.
#             </div>
#         </div>
#         """, unsafe_allow_html=True)
    
#     with col2:
#         st.markdown("""
#         <div class='feature-card'>
#             <div class='feature-icon'>📱</div>
#             <div class='feature-title'>WhatsApp Ready<span class='premium-badge'>PRO</span></div>
#             <div class='feature-desc'>
#                 Seamlessly integrate with WhatsApp Business API. 
#                 Meet customers where they are and automate 
#                 responses 24/7.
#             </div>
#         </div>
#         """, unsafe_allow_html=True)
    
#     with col3:
#         st.markdown("""
#         <div class='feature-card'>
#             <div class='feature-icon'>⚡</div>
#             <div class='feature-title'>Lightning Fast</div>
#             <div class='feature-desc'>
#                 Powered by Groq's inference engine with FAISS 
#                 vector search. Sub-second responses with 
#                 pinpoint accuracy.
#             </div>
#         </div>
#         """, unsafe_allow_html=True)
    
#     # Upload Section
#     st.write("##")
#     st.write("##")
#     st.write("##")
#     col1, col2 = st.columns([3, 2])
    
#     with col1:
#         st.markdown("### 📤 Upload Your Restaurant Menu")
#         st.markdown("Drag and drop your PDF menu or click to browse. The AI will analyze and learn your entire menu in seconds.")
        
#         uploaded_file = st.file_uploader(
#             "Drop your PDF here or click to browse",
#             type=['pdf'],
#             help="Standard PDF format, any language supported",
#             label_visibility="collapsed"
#         )
        
#         if uploaded_file:
#             st.success(f"✅ **{uploaded_file.name}** is ready to process!")
#             st.info(f"📄 File size: {uploaded_file.size / 1024:.1f} KB")
    
#     with col2:
#         st.markdown("### 🚀 Quick Start Guide")
#         st.markdown("""
#         **Get started in 3 simple steps:**
        
#         **1️⃣ Upload**  
#         Drop your menu PDF file
        
#         **2️⃣ Process**  
#         Click the launch button
        
#         **3️⃣ Chat**  
#         Start asking questions!
        
#         **Total time: ~30 seconds**
#         """)
    
#     st.markdown("<br>", unsafe_allow_html=True)
    
#     # Launch Button
#     if uploaded_file:
#         col1, col2, col3 = st.columns([1, 2, 1])
#         with col2:
#             if st.button("🚀 LAUNCH AI ASSISTANT", type="primary", use_container_width=True):
#                 with st.spinner("🧠 Training AI on your menu... This will take about 30 seconds"):
#                     try:
#                         # Progress bar for visual feedback
#                         progress_bar = st.progress(0)
#                         status_text = st.empty()
                        
#                         # Save temp file
#                         status_text.text("💾 Saving menu file...")
#                         progress_bar.progress(20)
#                         with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
#                             tmp.write(uploaded_file.getvalue())
#                             tmp_path = tmp.name
                        
#                         # Initialize RAG engine
#                         status_text.text("🔧 Initializing AI engine...")
#                         progress_bar.progress(40)
#                         st.session_state.rag_engine = RestaurantRAG(
#                             api_key=GROQ_API_KEY,
#                             model="llama-3.3-70b-versatile",
#                             provider="groq"
#                         )
                        
#                         # Process menu
#                         status_text.text("📖 Learning your menu...")
#                         progress_bar.progress(60)
#                         st.session_state.rag_engine.process_menu(tmp_path)
                        
#                         # Cleanup
#                         status_text.text("✨ Finalizing setup...")
#                         progress_bar.progress(90)
#                         os.unlink(tmp_path)
                        
#                         progress_bar.progress(100)
#                         status_text.text("✅ Complete!")
                        
#                         st.session_state.menu_processed = True
#                         time.sleep(0.5)
#                         st.success("🎉 **AI Assistant is now live and ready to help!**")
#                         st.balloons()
#                         time.sleep(1)
#                         st.rerun()
                        
#                     except Exception as e:
#                         st.error(f"❌ **Error:** {str(e)}")
#                         st.info("💡 **Tip:** Make sure your PDF is not corrupted and contains readable text.")
#     else:
#         st.markdown("""
#         <div style='text-align: center; padding: 2.5rem 1.5rem; color: black;'>
#             <p style='font-size: 1.2rem; margin-bottom: 0.5rem; font-weight: 600;'>👆 Upload a menu PDF to get started</p>
#             <p style='font-size: 0.95rem;'>Don't have one? Check the sample_menus/ folder</p>
#         </div>
#         """, unsafe_allow_html=True)

# # CHAT INTERFACE (default view when menu is processed)
# elif st.session_state.menu_processed and st.session_state.rag_engine:
    
#     st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
#     st.markdown("### 💭 Try These Popular Questions")
#     st.markdown("<p style='color: #6b7280; margin-bottom: 1.5rem;'>Click any question to get instant answers</p>", unsafe_allow_html=True)

#     cols = st.columns(4)
#     samples = [
#         ("🌱", "What vegan options do you have?"),
#         ("💰", "Show me items under 500 PKR"),
#         ("🌶️", "What's your spiciest dish?"),
#         ("🗃", "List all chicken items")
#     ]

#     for idx, (emoji, question) in enumerate(samples):
#         label = f"{emoji} {question.split('?')[0].split('items')[0][:20]}..."
#         if cols[idx].button(label, use_container_width=True, key=f"q_{idx}"):
#             st.session_state.pending_question = question
#             st.rerun()

#     st.markdown("---")

#     # Display Messages
#     for idx, msg in enumerate(st.session_state.messages):
#         avatar = "👤" if msg["role"] == "user" else "🤖"
#         with st.chat_message(msg["role"], avatar=avatar):
#             st.write(msg["content"])

#     # Detect either manual chat input OR button click
#     user_prompt = None
#     if prompt := st.chat_input("💬 Ask me anything about the menu..."):
#         user_prompt = prompt
#     elif st.session_state.pending_question:
#         user_prompt = st.session_state.pending_question
#         st.session_state.pending_question = None  # reset after use

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
                    
#                     if response.get('recommendations') or response.get('popular_items'):
#                         st.markdown("---")
#                         st.markdown("**🛒 Quick Actions:**")
                        
#                         items_to_show = response.get('recommendations', []) or response.get('popular_items', [])
                        
#                         if items_to_show:
#                             cols = st.columns(min(3, len(items_to_show)))
#                             for idx, item_data in enumerate(items_to_show[:3]):
#                                 # Handle both dict and tuple formats
#                                 if isinstance(item_data, dict):
#                                     item_name = item_data.get('name')
#                                     item_price = item_data.get('price')
#                                 elif isinstance(item_data, tuple) and len(item_data) >= 3:
#                                     item_name = item_data[0]
#                                     item_price = item_data[2]
#                                 else:
#                                     continue
                                
#                                 if item_name and item_price:
#                                     with cols[idx]:
#                                         if st.button(f"🛒 Add {item_name[:15]}...", key=f"add_cart_{idx}_{len(st.session_state.messages)}", use_container_width=True):
#                                             add_to_cart(item_name, float(item_price))
#                                             time.sleep(0.5)
#                                             st.rerun()
                                        
#                     if response.get('source_documents'):
#                         with st.expander("📚 View Sources & Context"):
#                             for idx, doc in enumerate(response['source_documents'][:3]):
#                                 st.markdown(f"**📄 Source {idx+1}:**")
#                                 st.code(doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content)
#                                 st.markdown("---")
                    
#                     st.session_state.messages.append({"role": "assistant", "content": answer})
                
#                 except Exception as e:
#                     st.error(f"❌ **Error processing your question:** {str(e)}")
#                     st.info("💡 **Tip:** Try rephrasing your question or make it more specific.")
    
#     st.markdown('</div>', unsafe_allow_html=True)


# # Footer
# st.markdown("---")
# st.markdown("""
# <div style='text-align: center; padding: 3rem 2rem 2rem; color: #333;'>
#     <p style='font-size: clamp(1.5rem, 3vw, 2rem); font-weight: 900; margin-bottom: 1rem; font-family: "Space Grotesk", sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
#         🤖 AI Menu Assistant Pro
#     </p>
#     <p style='font-size: clamp(1rem, 2vw, 1.1rem); color: #666; margin-bottom: 1rem; font-weight: 600;'>
#         Transforming Restaurants with Artificial Intelligence
#     </p>
#     <p style='font-size: clamp(0.9rem, 1.8vw, 1rem); color: #888; margin-bottom: 1.5rem;'>
#         Powered by Groq AI • Built with LangChain • Secured by FAISS
#     </p>
#     <div style='display: inline-block; background: rgba(102, 126, 234, 0.1); padding: 1.8rem 2.8rem; border-radius: 24px; border: 1px solid rgba(102, 126, 234, 0.3);'>
#         <p style='font-size: clamp(1.1rem, 2.2vw, 1.3rem); font-weight: 900; margin-bottom: 0.5rem; background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-family: "Space Grotesk", sans-serif;'>
#             Made with ❤️ by Shahbaz
#         </p>
#         <p style='font-size: clamp(0.85rem, 1.8vw, 0.95rem); color: #666; margin: 0;'>
#             Full-Stack AI Developer | Available for Freelance Projects
#         </p>
#     </div>
#     <p style='margin-top: 2rem; font-size: clamp(0.8rem, 1.6vw, 0.9rem); color: #888;'>
#         Open for custom AI solutions | Portfolio project showcasing RAG technology
#     </p>
# </div>
# """, unsafe_allow_html=True)