import streamlit as st
import os
from pathlib import Path
from order_manager import OrderManager
from payment_handler import PaymentHandler, PaymentMethod
from config import config
import requests
import tempfile
from rag_engine import RestaurantRAG
import time
# from config import GEMINI_API_KEY, GEMINI_MODEL



from dotenv import load_dotenv
load_dotenv()



# Default session state
default_session_state = {
    "cart": [],
    "show_cart": False,
    "show_checkout": False,
    "messages": [],
    "pending_question": None,
    "menu_processed": False,
    "rag_engine": None,
    "order_manager": None,
    "payment_handler": None,
    "current_order": None,
}

for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Page config
st.set_page_config(
    page_title="AI Menu Assistant Pro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Styles
# ULTRA-PREMIUM CSS WITH REFINED ANIMATIONS AND RESPONSIVE DESIGN
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

/* ---------- Root Variables for Consistency ---------- */
:root {
    --primary-gradient: linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #4facfe);
    --glass-bg: rgba(255, 255, 255, 0.98);
    --glass-border: rgba(255, 255, 255, 0.3);
    --shadow-sm: 0 4px 15px rgba(0, 0, 0, 0.05);
    --shadow-md: 0 10px 40px rgba(0, 0, 0, 0.08);
    --shadow-lg: 0 20px 70px rgba(0, 0, 0, 0.12);
    --shadow-xl: 0 30px 90px rgba(0, 0, 0, 0.15);
    --transition-smooth: all 0.6s cubic-bezier(0.165, 0.84, 0.44, 1);
    --transition-fast: all 0.3s ease;
    --border-radius-sm: 12px;
    --border-radius-md: 20px;
    --border-radius-lg: 28px;
    --border-radius-xl: 36px;
}

/* ---------- Global Layout ---------- */
.main {
    background: var(--primary-gradient);
    background-size: 400% 400%;
    animation: gradientShift 20s ease infinite;
    background-attachment: fixed;
    padding: 0 !important;
    min-height: 100vh;
}

@keyframes gradientShift {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}

/* Container Wrapper for Centering */
.stApp > div:first-child {
    max-width: 100%;
    margin: 0 auto;
}
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: var(--border);
    box-shadow: var(--shadow-sm);
    padding: var(--space-lg) !important;
}

/* Sidebar Scrollbar - Always Visible & Smooth */
[data-testid="stSidebar"] ::-webkit-scrollbar {
    width: 8px;
}

[data-testid="stSidebar"] ::-webkit-scrollbar-track {
    background: rgba(226, 232, 240, 0.3);
    border-radius: 4px;
}

[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
    background: var(--primary);
    border-radius: 4px;
    transition: var(--transition);
}

[data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover {
    background: var(--primary-hover);
    box-shadow: 0 0 6px rgba(43, 58, 103, 0.3);
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    font-weight: 700;
    color: var(--primary);
    margin-bottom: var(--space-md);
}

[data-testid="stSidebar"] p {
    color: var(--text-secondary) !important;
    font-size: 0.95rem;
}

/* Sidebar Inputs */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] select,
[data-testid="stSidebar"] textarea {
    background: var(--bg-primary) !important;
    border: var(--border) !important;
    border-radius: var(--radius-sm) !important;
    padding: 0.75rem !important;
    color: var(--text-primary) !important;
    font-size: 0.95rem !important;
    transition: var(--transition) !important;
}

[data-testid="stSidebar"] input:focus,
[data-testid="stSidebar"] select:focus,
[data-testid="stSidebar"] textarea:focus {
    background: var(--bg-secondary) !important;
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px var(--primary-light) !important;
    outline: none !important;
}

/* ---------- Hero Section ---------- */
.hero-container {
    position: relative;
    overflow: hidden;
    background: var(--glass-bg);
    backdrop-filter: blur(30px);
    border-radius: var(--border-radius-xl);
    padding: 3.5rem 2.5rem;
    margin: 2rem auto;
    max-width: 1200px;
    border: 1px solid var(--glass-border);
    box-shadow: var(--shadow-xl), 0 0 0 1px rgba(255, 255, 255, 0.1);
    animation: heroFadeIn 1s ease-out;
}

@keyframes heroFadeIn {
    from { opacity: 0; transform: translateY(40px) scale(0.98); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}

.hero-container::before {
    content: '';
    position: absolute;
    inset: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle at 50% 50%, rgba(102, 126, 234, 0.06) 0%, transparent 60%);
    animation: rotateGlow 25s linear infinite;
    pointer-events: none;
}

@keyframes rotateGlow {
    to { transform: rotate(360deg); }
}

.hero-title {
    position: relative;
    z-index: 1;
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(2.5rem, 6vw, 4.5rem);
    font-weight: 900;
    line-height: 1.1;
    letter-spacing: -2px;
    margin-bottom: 1rem;
    text-align: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shimmer 4s ease-in-out infinite;
}

@keyframes shimmer {
    0%, 100% { background-position: 0% center; }
    50% { background-position: 100% center; }
}

.hero-subtitle {
    position: relative;
    z-index: 1;
    font-size: clamp(1.1rem, 2.5vw, 1.6rem);
    font-weight: 600;
    color: #4b5563;
    text-align: center;
    margin-bottom: 0.75rem;
    animation: fadeSlideIn 1s ease-out 0.2s both;
}

.hero-caption {
    position: relative;
    z-index: 1;
    text-align: center;
    color: #9ca3af;
    font-size: clamp(0.9rem, 2vw, 1.1rem);
    font-weight: 500;
    animation: fadeSlideIn 1s ease-out 0.4s both;
}

@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ---------- Stats Section ---------- */
.stats-container {
    position: relative;
    overflow: hidden;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: var(--border-radius-lg);
    padding: 2rem 1.5rem;
    margin: 0 auto 2rem;
    max-width: 1200px;
    box-shadow: 0 20px 60px rgba(102, 126, 234, 0.35), inset 0 0 0 1px rgba(255, 255, 255, 0.1);
    animation: statsSlideUp 0.8s ease-out 0.3s both;
}

@keyframes statsSlideUp {
    from { opacity: 0; transform: translateY(40px); }
    to { opacity: 1; transform: translateY(0); }
}

.stats-container::before {
    content: '';
    position: absolute;
    width: 300px;
    height: 300px;
    top: -150px;
    right: -150px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.12) 0%, transparent 70%);
    animation: statsPulse 5s ease-in-out infinite;
}

@keyframes statsPulse {
    0%, 100% { transform: scale(1); opacity: 0.3; }
    50% { transform: scale(1.3); opacity: 0.6; }
}

.stat-box {
    text-align: center;
    color: #fff;
    animation: statPopIn 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55) both;
    position: relative;
    z-index: 1;
}

.stat-box:nth-child(1) { animation-delay: 0.5s; }
.stat-box:nth-child(2) { animation-delay: 0.6s; }
.stat-box:nth-child(3) { animation-delay: 0.7s; }
.stat-box:nth-child(4) { animation-delay: 0.8s; }

@keyframes statPopIn {
    from { opacity: 0; transform: scale(0.6) translateY(30px); }
    to { opacity: 1; transform: scale(1) translateY(0); }
}

.stat-number {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(2rem, 5vw, 3rem);
    font-weight: 900;
    margin-bottom: 0.5rem;
    text-shadow: 0 3px 12px rgba(0, 0, 0, 0.25);
    display: block;
}

.stat-label {
    font-size: clamp(0.75rem, 1.5vw, 1rem);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    opacity: 0.95;
    display: block;
}

/* ---------- Feature Cards ---------- */
.feature-card {
    position: relative;
    overflow: hidden;
    height: 100%;
    background: var(--glass-bg);
    border: 2px solid transparent;
    border-radius: var(--border-radius-lg);
    padding: 2.5rem 2rem;
    box-shadow: var(--shadow-md), 0 0 0 1px rgba(255, 255, 255, 0.5);
    transition: var(--transition-smooth);
    animation: cardFloatIn 0.8s ease-out both;
}

@keyframes cardFloatIn {
    from { opacity: 0; transform: translateY(60px) scale(0.94); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}

.feature-card::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.08));
    opacity: 0;
    transition: opacity 0.6s ease;
}

.feature-card:hover {
    transform: translateY(-12px) scale(1.02);
    border-color: rgba(102, 126, 234, 0.4);
    box-shadow: 0 30px 80px rgba(102, 126, 234, 0.28), 0 0 0 1px rgba(102, 126, 234, 0.4);
}

.feature-card:hover::before { 
    opacity: 1; 
}

.feature-icon {
    position: relative;
    z-index: 1;
    font-size: clamp(2.5rem, 5vw, 3.5rem);
    margin-bottom: 1.5rem;
    display: inline-block;
    filter: drop-shadow(0 6px 18px rgba(0, 0, 0, 0.12));
    animation: iconBounce 3s ease-in-out infinite;
}

@keyframes iconBounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-12px); }
}

.feature-card:hover .feature-icon { 
    animation: iconSpin 0.7s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

@keyframes iconSpin {
    from { transform: rotate(0deg) scale(1); }
    50% { transform: rotate(180deg) scale(1.25); }
    to { transform: rotate(360deg) scale(1); }
}

.feature-title {
    position: relative;
    z-index: 1;
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(1.2rem, 2.5vw, 1.6rem);
    font-weight: 800;
    color: #1f2937;
    margin-bottom: 1rem;
    letter-spacing: -0.5px;
}

.feature-desc {
    position: relative;
    z-index: 1;
    font-size: clamp(0.95rem, 1.8vw, 1.05rem);
    color: #6b7280;
    line-height: 1.7;
}

.premium-badge {
    display: inline-block;
    background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
    color: #fff;
    padding: 0.35rem 1rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 800;
    margin-left: 0.5rem;
    box-shadow: 0 4px 14px rgba(251, 191, 36, 0.45);
    animation: badgeGlow 2.5s ease-in-out infinite;
    vertical-align: middle;
}

@keyframes badgeGlow {
    0%, 100% { box-shadow: 0 4px 14px rgba(251, 191, 36, 0.45); }
    50% { box-shadow: 0 6px 24px rgba(251, 191, 36, 0.7); }
}

/* ---------- Upload & Chat Containers ---------- */
.upload-container,
.chat-container {
    background: var(--glass-bg);
    backdrop-filter: blur(30px);
    border-radius: var(--border-radius-xl);
    box-shadow: var(--shadow-lg), 0 0 0 1px rgba(255, 255, 255, 0.5);
    margin: 0 auto 2rem;
    max-width: 1200px;
    transition: var(--transition-smooth);
}

.upload-container { 
    padding: 3rem 2.5rem; 
    animation: containerFadeIn 0.8s ease-out 0.5s both;
}

.chat-container { 
    padding: 2.5rem 2rem; 
    min-height: 500px;
    animation: containerFadeIn 0.8s ease-out 0.7s both;
}

@keyframes containerFadeIn {
    from { opacity: 0; transform: translateY(40px) scale(0.97); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}

/* Transition effect when switching from upload to chat */
.container-transition-out {
    animation: fadeOut 0.5s ease-out forwards;
}

@keyframes fadeOut {
    to { opacity: 0; transform: translateY(-30px) scale(0.98); }
}

.container-transition-in {
    animation: slideInFromBottom 0.7s ease-out forwards;
}

@keyframes slideInFromBottom {
    from { opacity: 0; transform: translateY(50px) scale(0.95); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}

/* ---------- Chat Messages ---------- */
.stChatMessage {
    background: #f9fafb !important;
    border: 1px solid #e5e7eb !important;
    border-radius: var(--border-radius-md) !important;
    padding: 1.5rem !important;
    margin-bottom: 1rem !important;
    box-shadow: var(--shadow-sm) !important;
    animation: messageSlideIn 0.5s ease-out !important;
    transition: var(--transition-fast) !important;
}

@keyframes messageSlideIn {
    from { opacity: 0; transform: translateX(-40px); }
    to { opacity: 1; transform: translateX(0); }
}

.stChatMessage:hover {
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1) !important;
    transform: translateY(-2px) !important;
}

.stChatMessage[data-testid="user-message"] {
    background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%) !important;
    border-color: #c4b5fd !important;
}

/* ---------- Buttons ---------- */
.stButton>button {
    position: relative;
    overflow: hidden;
    border: none;
    border-radius: var(--border-radius-md);
    padding: 1rem 2.5rem;
    font-weight: 700;
    font-size: clamp(0.95rem, 2vw, 1.05rem);
    color: #fff;
    letter-spacing: 0.5px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    box-shadow: 0 6px 22px rgba(102, 126, 234, 0.38), 0 2px 8px rgba(102, 126, 234, 0.22);
    transition: var(--transition-smooth);
    cursor: pointer;
}

.stButton>button::before {
    content: '';
    position: absolute;
    top: 0; 
    left: -100%;
    width: 100%; 
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.35), transparent);
    transition: left 0.7s ease;
}

.stButton>button:hover::before { 
    left: 100%; 
}

.stButton>button:hover {
    transform: translateY(-4px) scale(1.03);
    box-shadow: 0 14px 40px rgba(102, 126, 234, 0.48), 0 6px 16px rgba(102, 126, 234, 0.32);
}

.stButton>button:active { 
    transform: translateY(-1px) scale(0.98); 
}

.stButton>button[kind="primary"] {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    font-size: clamp(1.1rem, 2.5vw, 1.3rem);
    padding: 1.3rem 3rem;
    box-shadow: 0 8px 32px rgba(245, 87, 108, 0.42), 0 0 60px rgba(245, 87, 108, 0.22);
    animation: primaryPulse 3s ease-in-out infinite;
}

@keyframes primaryPulse {
    0%, 100% { 
        box-shadow: 0 8px 32px rgba(245, 87, 108, 0.42), 0 0 60px rgba(245, 87, 108, 0.22); 
    }
    50% { 
        box-shadow: 0 10px 38px rgba(245, 87, 108, 0.55), 0 0 80px rgba(245, 87, 108, 0.35); 
    }
}

.stButton>button[kind="primary"]:hover {
    box-shadow: 0 16px 55px rgba(245, 87, 108, 0.65), 0 0 100px rgba(245, 87, 108, 0.45);
}

/* ---------- Inputs ---------- */
.stTextInput>div>div>input,
.stTextArea textarea {
    background: #f9fafb;
    border: 2px solid #e5e7eb;
    border-radius: var(--border-radius-sm);
    padding: 0.95rem 1.2rem;
    font-size: clamp(0.9rem, 2vw, 1.05rem);
    transition: var(--transition-smooth);
}

.stTextInput>div>div>input:focus,
.stTextArea textarea:focus {
    background: #fff;
    border-color: #667eea;
    box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.12), 0 4px 30px rgba(102, 126, 234, 0.22);
    transform: translateY(-2px);
    outline: none;
}

/* ---------- File Uploader ---------- */
[data-testid="stFileUploadDropzone"] {
    position: relative;
    overflow: hidden;
    border: 3px dashed #667eea;
    border-radius: var(--border-radius-lg);
    padding: 3.5rem 2rem;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.06), rgba(118, 75, 162, 0.06));
    transition: var(--transition-smooth);
}

[data-testid="stFileUploadDropzone"]::before {
    content: '';
    position: absolute;
    inset: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(102, 126, 234, 0.08) 0%, transparent 70%);
    animation: uploadGlow 4s ease-in-out infinite;
    pointer-events: none;
}

@keyframes uploadGlow {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.2); opacity: 0.8; }
}

[data-testid="stFileUploadDropzone"]:hover {
    border-color: #764ba2;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.12), rgba(118, 75, 162, 0.12));
    box-shadow: 0 10px 40px rgba(102, 126, 234, 0.2);
    transform: translateY(-3px);
}

/* ---------- Expander ---------- */
.streamlit-expanderHeader {
    background: #f9fafb !important;
    border-radius: var(--border-radius-sm) !important;
    padding: 0.9rem 1.2rem !important;
    font-weight: 600 !important;
    transition: var(--transition-fast) !important;
}

.streamlit-expanderHeader:hover {
    background: #f3f4f6 !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ---------- Responsive Design ---------- */
@media screen and (max-width: 1024px) {
    .hero-container,
    .stats-container,
    .upload-container,
    .chat-container {
        margin-left: 1rem;
        margin-right: 1rem;
    }
    
    .hero-container {
        padding: 2.5rem 1.5rem;
    }
    
    .upload-container {
        padding: 2rem 1.5rem;
    }
    
    .chat-container {
        padding: 1.5rem;
    }
    
    .feature-card {
        padding: 2rem 1.5rem;
        margin-bottom: 1.5rem;
    }
}

@media screen and (max-width: 768px) {
    .hero-title {
        font-size: 2.5rem;
        letter-spacing: -1px;
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
    }
    
    .hero-caption {
        font-size: 0.95rem;
    }
    
    .stats-container {
        padding: 1.5rem 1rem;
    }
    
    .stat-number {
        font-size: 2rem;
    }
    
    .stat-label {
        font-size: 0.8rem;
    }
    
    [data-testid="stFileUploadDropzone"] {
        padding: 2.5rem 1.5rem;
    }
    
    .stButton>button {
        padding: 0.9rem 2rem;
        font-size: 0.95rem;
    }
    
    .stButton>button[kind="primary"] {
        padding: 1.1rem 2.5rem;
        font-size: 1.1rem;
    }
}

@media screen and (max-width: 480px) {
    .hero-container,
    .stats-container,
    .upload-container,
    .chat-container {
        margin-left: 0.5rem;
        margin-right: 0.5rem;
        border-radius: var(--border-radius-lg);
    }
    
    .hero-container {
        padding: 2rem 1.25rem;
    }
    
    .feature-card {
        padding: 1.5rem 1.25rem;
    }
    
    .stChatMessage {
        padding: 1.2rem !important;
    }
}

/* ---------- Prevent FOUC (Flash of Unstyled Content) ---------- */
.main > div {
    opacity: 0;
    animation: preventFOUC 0.01s 0.1s forwards;
}

@keyframes preventFOUC {
    to { opacity: 1; }
}

/* ---------- Smooth Scrolling ---------- */
html {
    scroll-behavior: smooth;
}

/* ---------- Custom Scrollbar ---------- */
::-webkit-scrollbar {
    width: 12px;
}

::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 10px;
    border: 2px solid rgba(255, 255, 255, 0.2);
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #764ba2, #f093fb);
}

/* ---------- Loading Spinner Enhancement ---------- */
.stSpinner > div {
    border-color: #667eea transparent transparent transparent !important;
}

/* ---------- Success/Error/Info Messages ---------- */
.stAlert {
    border-radius: var(--border-radius-sm) !important;
    animation: alertSlide 0.5s ease-out !important;
}

@keyframes alertSlide {
    from { opacity: 0; transform: translateY(-20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ---------- Metric Cards ---------- */
[data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 800 !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

/* ---------- Columns Gap Fix ---------- */
[data-testid="column"] {
    padding: 0 0.5rem !important;
}

/* ---------- Hide Streamlit Branding ---------- */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

</style>
""", unsafe_allow_html=True)


# Get API key
try:
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    API_KEY_SET = bool(GEMINI_API_KEY)
except:
    GEMINI_API_KEY = None
    API_KEY_SET = False


# Cart Functions
def add_to_cart(item_name: str, price: float):
    """Add item to cart"""
    for item in st.session_state.cart:
        if item['name'] == item_name:
            item['qty'] += 1
            item['subtotal'] = item['qty'] * item['price']
            st.toast(f"✅ Added another {item_name}!")
            return
    
    st.session_state.cart.append({
        "name": item_name,
        "qty": 1,
        "price": price,
        "subtotal": price
    })
    st.toast(f"✅ Added {item_name} to cart!")

def remove_from_cart(index: int):
    """Remove item from cart"""
    if 0 <= index < len(st.session_state.cart):
        item = st.session_state.cart.pop(index)
        st.success(f"🗑️ Removed {item['name']}")

def update_cart_quantity(index: int, new_qty: int):
    """Update item quantity"""
    if 0 <= index < len(st.session_state.cart):
        if new_qty <= 0:
            remove_from_cart(index)
        else:
            item = st.session_state.cart[index]
            item['qty'] = new_qty
            item['subtotal'] = new_qty * item['price']

def get_cart_total() -> float:
    """Calculate cart total"""
    return sum(item['subtotal'] for item in st.session_state.cart)

def clear_cart():
    """Clear cart"""
    st.session_state.cart = []
    st.success("🗑️ Cart cleared!")


# Initialize managers
if st.session_state.order_manager is None:
    try:
        st.session_state.order_manager = OrderManager()
    except Exception as e:
        st.warning(f"⚠️ Order system unavailable: {e}")

if st.session_state.payment_handler is None:
    try:
        st.session_state.payment_handler = PaymentHandler()
    except Exception as e:
        st.warning(f"⚠️ Payment system unavailable: {e}")


# Sidebar
with st.sidebar:
    st.markdown("# ⚙️ Control Center")
    st.markdown("---")
    
    restaurant_name = st.text_input("Restaurant Name", "Demo Restaurant")
    restaurant_tagline = st.text_input("Tagline", "Delicious food, AI service")
    
    st.markdown("---")
    
    if st.session_state.menu_processed:
        st.success("✅ **System Online**")
        items_count = len(st.session_state.rag_engine.menu_items) if st.session_state.rag_engine.menu_items else 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📋 Items", items_count)
        with col2:
            st.metric("💬 Chats", len(st.session_state.messages))
        
        if st.button("🔄 Reset Chat", use_container_width=True):
            if st.session_state.rag_engine:
                st.session_state.rag_engine.reset_conversation()
            st.session_state.messages = []
            st.rerun()
    else:
        st.info("⏳ **Ready to Launch**")
    
    st.markdown("---")
    
    # Cart summary
    if len(st.session_state.cart) > 0:
        st.markdown("### 🛒 Cart")
        cart_total = get_cart_total()
        items_count = sum(item['qty'] for item in st.session_state.cart)
        
        st.metric("Items", items_count)
        st.metric("Total", f"Rs {int(cart_total)}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👁️ View", use_container_width=True, key="sidebar_view_cart"):
                st.session_state.show_cart = True
                st.session_state.show_checkout = False
                st.rerun()
        with col2:
            if st.button("💳 Checkout", use_container_width=True, type="primary", key="sidebar_checkout"):
                st.session_state.show_checkout = True
                st.session_state.show_cart = False
                st.rerun()
    else:
        st.info("🛒 Cart is empty")
    
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <p style='font-weight: 700; color: #667eea;'>⚡ Powered by</p>
        <p style='color: #6b7280;'>Groq AI • LangChain • FAISS</p>
        <p style='font-weight: 800; font-size: 1.1rem; margin-top: 1rem;'>Made by Shahbaz</p>
        <p style='font-size: 0.8rem; color: #9ca3af;'>Full-Stack AI Developer</p>
    </div>
    """, unsafe_allow_html=True)


# Check API key
if not API_KEY_SET:
    st.error("⚠️ **API Key Not Configured**")
    st.info("Get your FREE Gemini API key: https://aistudio.google.com/app/apikey")
    st.info("Then add GEMINI_API_KEY in Streamlit secrets or .env file")
    st.stop()


# Hero Section
st.markdown(f"""
<div class='hero-container'>
    <div class='hero-title'>{restaurant_name}</div>
    <div class='hero-subtitle'>{restaurant_tagline}</div>
    <div class='hero-caption'>🤖 AI-Powered Menu • ⚡ Instant Answers • 🌍 24/7 Available</div>
</div>
""", unsafe_allow_html=True)

st.write("##")


# ============================================
# MAIN CONTENT ROUTING
# ============================================

# CHECKOUT VIEW
if st.session_state.show_checkout:
    st.markdown('<div class="chat-content">', unsafe_allow_html=True)
    st.markdown("### 💳 Checkout")
    
    if len(st.session_state.cart) == 0:
        st.warning("Your cart is empty!")
        if st.button("← Back to Menu"):
            st.session_state.show_checkout = False
            st.rerun()
    else:
        with st.expander("📋 Order Summary", expanded=True):
            for item in st.session_state.cart:
                st.write(f"{item['qty']}x {item['name']} - Rs {int(item['subtotal'])}")
            
            st.markdown("---")
            subtotal = get_cart_total()
            delivery_fee = 50
            tax = subtotal * 0.05
            total = subtotal + delivery_fee + tax
            
            st.write(f"**Subtotal:** Rs {int(subtotal)}")
            st.write(f"**Delivery Fee:** Rs {int(delivery_fee)}")
            st.write(f"**Tax (5%):** Rs {int(tax)}")
            st.markdown(f"### **Total: Rs {int(total)}**")
        
        st.markdown("---")
        st.markdown("### 📝 Delivery Details")
        
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("Full Name *", placeholder="Ahmed Khan")
        with col2:
            customer_phone = st.text_input("Phone *", placeholder="+92 300 1234567")
        
        delivery_address = st.text_area("Address *", placeholder="House #123, Street 4, DHA Phase 2")
        special_instructions = st.text_area("Special Instructions", placeholder="Extra spicy, no onions")
        
        st.markdown("---")
        st.markdown("### 💰 Payment Method")
        payment_method = st.radio("Choose:", ["💵 Cash on Delivery", "💳 Mock Payment", "📱 JazzCash"], label_visibility="collapsed")
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back to Cart", use_container_width=True):
                st.session_state.show_checkout = False
                st.session_state.show_cart = True
                st.rerun()
        with col2:
            if st.button("🚀 Place Order", use_container_width=True, type="primary"):
                if not customer_name or not customer_phone or not delivery_address:
                    st.error("⚠️ Please fill all required fields!")
                elif not st.session_state.order_manager:
                    st.error("⚠️ Order system unavailable")
                else:
                    try:
                        with st.spinner("Creating order..."):
                            order = st.session_state.order_manager.create_order(
                                customer_phone=customer_phone,
                                customer_name=customer_name,
                                items=st.session_state.cart,
                                delivery_address=delivery_address,
                                special_instructions=special_instructions,
                                delivery_type="DELIVERY"
                            )
                            
                            method = PaymentMethod.CASH if "Cash" in payment_method else PaymentMethod.MOCK
                            payment_result = st.session_state.payment_handler.initiate_payment(
                                order_id=order['order_id'],
                                amount=order['total'],
                                customer_phone=customer_phone,
                                method=method
                            )
                            
                            if payment_result['status'] == 'SUCCESS':
                                st.balloons()
                                st.success("✅ Order placed successfully!")
                                st.info(f"""
**Order ID:** {order['order_id']}  
**Total:** Rs {int(order['total'])}  
**Payment:** {payment_result['method']}  
**Status:** {payment_result['message']}  
**Estimated Delivery:** {order['estimated_delivery'].strftime('%I:%M %p')}
                                """)
                                st.session_state.cart = []
                                
                                if st.button("🏠 Back to Menu"):
                                    st.session_state.show_checkout = False
                                    st.rerun()
                            else:
                                st.error(f"❌ Payment failed: {payment_result['message']}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# CART VIEW
elif st.session_state.show_cart:
    st.markdown('<div class="chat-content">', unsafe_allow_html=True)
    st.markdown("### 🛒 Shopping Cart")
    
    if len(st.session_state.cart) == 0:
        st.info("Your cart is empty!")
        if st.button("← Back to Menu"):
            st.session_state.show_cart = False
            st.rerun()
    else:
        for idx, item in enumerate(st.session_state.cart):
            col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
            
            with col1:
                st.write(f"**{item['name']}**")
                st.caption(f"Rs {int(item['price'])} each")
            with col2:
                new_qty = st.number_input("Qty", min_value=0, value=item['qty'], key=f"qty_{idx}", label_visibility="collapsed")
                if new_qty != item['qty']:
                    update_cart_quantity(idx, new_qty)
                    st.rerun()
            with col3:
                st.write(f"Rs {int(item['subtotal'])}")
            with col4:
                if st.button("🗑️", key=f"remove_{idx}"):
                    remove_from_cart(idx)
                    st.rerun()
        
        st.markdown("---")
        
        subtotal = get_cart_total()
        delivery_fee = 50
        tax = subtotal * 0.05
        total = subtotal + delivery_fee + tax
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("**Subtotal:**")
            st.write("**Delivery Fee:**")
            st.write("**Tax (5%):**")
            st.markdown("**Total:**")
        with col2:
            st.write(f"Rs {int(subtotal)}")
            st.write(f"Rs {int(delivery_fee)}")
            st.write(f"Rs {int(tax)}")
            st.markdown(f"**Rs {int(total)}**")
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("← Continue Shopping", use_container_width=True):
                st.session_state.show_cart = False
                st.rerun()
        with col2:
            if st.button("🗑️ Clear Cart", use_container_width=True):
                clear_cart()
                st.rerun()
        with col3:
            if st.button("💳 Proceed to Checkout", use_container_width=True, type="primary"):
                st.session_state.show_checkout = True
                st.session_state.show_cart = False
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# UPLOAD VIEW
elif not st.session_state.menu_processed:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>💬</div>
            <div class='feature-title'>Intelligent Chat</div>
            <div class='feature-desc'>Natural conversations powered by Llama 3.3 70B</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>📱</div>
            <div class='feature-title'>WhatsApp Ready<span class='premium-badge'>PRO</span></div>
            <div class='feature-desc'>Integrate with WhatsApp Business API</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>⚡</div>
            <div class='feature-title'>Lightning Fast</div>
            <div class='feature-desc'>Powered by Groq's inference engine</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("##")
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("### 📤 Upload Your Restaurant Menu")
        uploaded_file = st.file_uploader("Drop PDF here", type=['pdf'], label_visibility="collapsed")
        
        if uploaded_file:
            st.success(f"✅ {uploaded_file.name} ready!")
    
    with col2:
        st.markdown("### 🚀 Quick Start")
        st.markdown("**1️⃣ Upload** PDF\n\n**2️⃣ Process** menu\n\n**3️⃣ Chat** away!")
    
    if uploaded_file:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 LAUNCH AI ASSISTANT", type="primary", use_container_width=True):
                with st.spinner("🧠 Training AI..."):
                    try:
                        progress_bar = st.progress(0)
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name
                        progress_bar.progress(40)
                        
                        st.session_state.rag_engine = RestaurantRAG(
                            api_key=GEMINI_API_KEY,
                            model="gemini-2.5-flash",  # FREE tier available!
                            provider="gemini",
                            agentic_mode=False
                        )
                        progress_bar.progress(60)
                        
                        st.session_state.rag_engine.process_menu(tmp_path)
                        st.session_state.rag_engine.set_cart_callback(add_to_cart)
                        progress_bar.progress(90)
                        
                        os.unlink(tmp_path)
                        progress_bar.progress(100)
                        
                        st.session_state.menu_processed = True
                        st.success("🎉 AI Assistant is live!")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

# CHAT INTERFACE
elif st.session_state.menu_processed and st.session_state.rag_engine:
    # st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    st.markdown("### 💭 Try These Questions")
    cols = st.columns(4)
    samples = [
        ("🌱", "What vegan options do you have?"),
        ("💰", "I have 800 rupees, order for me"),  # ✅ AGENTIC
        ("🌶️", "I want something spicy"),  # ✅ AGENTIC
        ("🗃", "I'm hungry, recommend something")  # ✅ AGENTIC
    ]

    for idx, (emoji, question) in enumerate(samples):
        if cols[idx].button(f"{emoji} {question[:25]}...", use_container_width=True, key=f"q_{idx}"):
            st.session_state.pending_question = question
            st.rerun()

    st.markdown("---")

    # Display message history
    for msg_idx, msg in enumerate(st.session_state.messages):
        avatar = "👤" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])
            
            # Show if AI took autonomous actions
            if msg["role"] == "assistant" and msg.get("agentic"):
                if msg.get("actions_taken"):
                    st.info(f"🤖 **Autonomous Actions:** Added {len(msg['actions_taken'])} items to your cart")
            
            # Show cart buttons for items
            if msg["role"] == "assistant" and "items_data" in msg:
                st.markdown("---")
                st.markdown("**🛒 Quick Add to Cart:**")
                
                items = msg["items_data"]
                cols = st.columns(min(3, len(items)))
                
                for item_idx, item_data in enumerate(items[:3]):
                    with cols[item_idx]:
                        st.markdown(f"**{item_data['name'][:22]}**")
                        st.caption(f"Rs {int(item_data['price'])}")
                        
                        btn_key = f"hist_{msg_idx}_{item_idx}"
                        if st.button("➕ Add", key=btn_key, use_container_width=True):
                            st.session_state[f'add_item_{btn_key}'] = {
                                'name': item_data['name'],
                                'price': float(item_data['price'])
                            }
                            st.rerun()

    # Process pending add-to-cart actions
    keys_to_remove = []
    for key in st.session_state.keys():
        if key.startswith('add_item_'):
            item_to_add = st.session_state[key]
            add_to_cart(item_to_add['name'], item_to_add['price'])
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del st.session_state[key]

    # Handle new input
    user_prompt = None
    if prompt := st.chat_input("💬 Tell me what you want..."):
        user_prompt = prompt
    elif st.session_state.pending_question:
        user_prompt = st.session_state.pending_question
        st.session_state.pending_question = None

    if user_prompt:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        
        with st.chat_message("user", avatar="👤"):
            st.write(user_prompt)
        
        # Get AI response - USE AGENTIC METHOD
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🤔 Thinking and taking actions..."):
                try:
                    # Check if user wants to place order (confirmation)
                    if any(word in user_prompt.lower() for word in ['yes', 'place order', 'confirm', 'proceed']):
                        # Check if cart has items
                        if len(st.session_state.cart) > 0:
                            st.info("🎉 **Great! Let's complete your order.**")
                            st.write("Please provide:")
                            st.write("1. Your name")
                            st.write("2. Phone number")
                            st.write("3. Delivery address")
                            st.write("\nExample: *Ahmed, +92 300 1234567, House 123 Street 4*")
                            
                            # Save special flag
                            message_data = {
                                "role": "assistant",
                                "content": "Great! I need your delivery details to complete the order. Please provide your name, phone, and address."
                            }
                            st.session_state.messages.append(message_data)
                        else:
                            st.warning("Your cart is empty! Tell me what you'd like to order.")
                            message_data = {
                                "role": "assistant",
                                "content": "Your cart is empty. What would you like to order?"
                            }
                            st.session_state.messages.append(message_data)
                    
                    # Check if user is providing delivery details
                    elif len(st.session_state.cart) > 0 and any(char.isdigit() for char in user_prompt):
                        # Try to extract delivery info
                        import re
                        phone_match = re.search(r'\+?\d{10,}', user_prompt)
                        
                        if phone_match:
                            st.success("📝 Processing your order...")
                            st.write("**Order Summary:**")
                            for item in st.session_state.cart:
                                st.write(f"- {item['qty']}x {item['name']} (Rs {item['subtotal']})")
                            st.write(f"\n**Total: Rs {int(get_cart_total())}**")
                            st.write("\n✅ Order details saved!")
                            st.write("\n*Click 'Proceed to Checkout' in the sidebar to complete payment.*")
                            
                            message_data = {
                                "role": "assistant",
                                "content": f"Perfect! Your order is ready. Total: Rs {int(get_cart_total())}. Click 'Proceed to Checkout' in the sidebar to complete your order!"
                            }
                            st.session_state.messages.append(message_data)
                        else:
                            st.write("I need your phone number to complete the order. Please provide it.")
                            message_data = {
                                "role": "assistant",
                                "content": "I need your phone number. Please provide your contact details."
                            }
                            st.session_state.messages.append(message_data)
                    
                    # Normal order/browse query - USE AGENTIC
                    else:
                        response = st.session_state.rag_engine.query_agentic(user_prompt)
                        answer = response['answer']
                        
                        # Check if AI auto-added items
                        auto_added = response.get('auto_added', False)
                        actions_taken = response.get('actions_taken', [])
                        
                        if auto_added and actions_taken:
                            st.success(f"🤖 **AI automatically added {len(actions_taken)} items to your cart!**")
                        
                        st.write(answer)
                        
                        # Show recommendations
                        items_to_show = response.get('recommendations', [])
                        
                        if items_to_show and len(items_to_show) > 0 and not auto_added:
                            st.markdown("---")
                            st.markdown("**🛒 Or manually add these:**")
                            
                            cols = st.columns(min(3, len(items_to_show)))
                            
                            for idx, item_data in enumerate(items_to_show[:3]):
                                with cols[idx]:
                                    st.markdown(f"**{item_data['name'][:20]}**")
                                    st.caption(f"Rs {int(item_data['price'])}")
                                    
                                    btn_key = f"new_{len(st.session_state.messages)}_{idx}"
                                    if st.button("➕ Add", key=btn_key, use_container_width=True):
                                        st.session_state[f'add_item_{btn_key}'] = {
                                            'name': item_data['name'],
                                            'price': float(item_data['price'])
                                        }
                                        st.rerun()
                        
                        # Save message
                        message_data = {
                            "role": "assistant",
                            "content": answer,
                            "agentic": response.get('agentic', False),
                            "actions_taken": actions_taken
                        }
                        if items_to_show and not auto_added:
                            message_data["items_data"] = items_to_show[:3]
                        
                        st.session_state.messages.append(message_data)
                
                except Exception as e:
                    st.error(f"❌ **Error:** {str(e)}")
                    st.info("💡 Try rephrasing your question")
    
    st.markdown('</div>', unsafe_allow_html=True)
# ```

# ---

## 🎯 **How It Works Now:**

### **Example 1: Budget Order**
# ```
# User: "I have 800 rupees"

# AI: *Analyzes budget*
#     *Selects: Chicken Biryani (Rs 450), Naan (Rs 80), Lassi (Rs 250)*
#     *AUTO-ADDS to cart*
    
#     "Perfect! I've added these items to your cart:
#     ✅ Chicken Biryani - Rs 450
#     ✅ Naan - Rs 80
#     ✅ Mango Lassi - Rs 250
    
#     💰 Total: Rs 780
#     Remaining: Rs 20
    
#     Ready to place your order? Just say 'Yes, place order'!"

# User: "Yes place order"

# AI: "Great! Please provide:
#      1. Your name
#      2. Phone number  
#      3. Delivery address"

# User: "Ahmed, +92 300 1234567, House 123"

# AI: "Perfect! Your order is ready. Total: Rs 780.
#      Click 'Proceed to Checkout' to complete!"
# ```

# ### **Example 2: Direct Order**
# ```
# User: "I want chicken biryani"

# AI: *Finds Chicken Biryani*
#     *AUTO-ADDS to cart*
    
#     "Perfect! I've added:
#     ✅ Chicken Biryani - Rs 450
    
#     Ready to order? Say 'Yes'!"


# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem; color: #333;'>
    <p style='font-size: 2rem; font-weight: 900; margin-bottom: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
        🤖 AI Menu Assistant Pro
    </p>
    <p style='font-size: 1.1rem; color: #666; margin-bottom: 1rem;'>
        Transforming Restaurants with Artificial Intelligence
    </p>
    <p style='color: #888; margin-bottom: 1.5rem;'>
        Powered by OpenAI • Built with LangChain • Secured by FAISS
    </p>
    <div style='display: inline-block; background: rgba(102, 126, 234, 0.1); padding: 1.8rem 2.8rem; border-radius: 24px;'>
        <p style='font-size: 1.3rem; font-weight: 900; margin-bottom: 0.5rem; background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            Made with ❤️ by Shahbaz
        </p>
        <p style='color: #666;'>
            Full-Stack AI Developer | Available for Freelance Projects
        </p>
    </div>
    <p style='margin-top: 2rem; color: #888;'>
        Open for custom AI solutions | Portfolio project showcasing RAG technology
    </p>
</div>
""", unsafe_allow_html=True)