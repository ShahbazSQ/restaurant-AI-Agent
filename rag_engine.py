import os
import re
import json
import time
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass

# CORRECT Gemini import - modern SDK
import google.generativeai as genai

# LangChain for embeddings and vector store ONLY
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

# PDF Library Detection
try:
    from pypdf import PdfReader
    PDF_LIBRARY = "pypdf"
    print("📄 Using pypdf for PDF processing")
except ImportError:
    try:
        import pymupdf
        PDF_LIBRARY = "pymupdf"
        print("📄 Using pymupdf for PDF processing")
    except ImportError:
        raise ImportError("Please install either pypdf or pymupdf: pip install pypdf")


@dataclass
class MenuItem:
    """Structure for parsed menu items"""
    name: str
    price: Optional[float]
    description: str
    category: Optional[str]
    tags: List[str]


class RestaurantRAG:
    """
    WORKING GEMINI RAG Engine - Simplified, No Agent (For Now)
    Gets it working first, then add agentic features
    """
    
    def __init__(self, 
                 api_key: str, 
                 model: str = "gemini-2.5-flash",
                 provider: str = "gemini",
                 agentic_mode: bool = False):
        """
        Initialize RAG engine with Gemini
        
        Args:
            api_key: Your Gemini API key
            model: Gemini model (gemini-2.5-flash or gemini-2.5-flash)
            provider: Always 'gemini'
            agentic_mode: Set to False for now (we'll add later)
        """
        self.api_key = api_key
        self.model = model
        self.provider = "gemini"
        self.agentic_mode = False  # Force disable for now
        self.vectorstore = None
        self.menu_items = []
        self.last_recommended_items = []  # Store what AI just recommended
        self.conversation_context = []
        
        # Agentic features (for later)
        self.cart_callback = None
        self.customer_memory = {
            'past_orders': [],
            'preferences': {},
            'last_items': [],
            'chat_history': []
        }
        
        print(f"🤖 Initializing GEMINI with model: {self.model}")
        
        # CRITICAL: Configure Gemini API with modern SDK
        genai.configure(api_key=self.api_key)
        
        # Test connection
        try:
            # List available models to verify connection
            models = genai.list_models()
            available = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
            print(f"✅ Gemini API connected! Found {len(available)} models")
            
            # Verify our model exists
            model_full_name = f"models/{self.model}"
            if model_full_name not in available:
                print(f"⚠️ Model {self.model} not found in available models")
                print(f"Available models: {', '.join([m.split('/')[-1] for m in available[:5]])}")
                # Use first available model
                self.model = available[0].split('/')[-1]
                print(f"✅ Using: {self.model}")
        except Exception as e:
            print(f"⚠️ Warning: Could not list models: {e}")
            print(f"Proceeding with model: {self.model}")
        
        # Initialize embeddings (FREE HuggingFace)
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            print("✅ Using FREE HuggingFace embeddings")
        except Exception as e:
            print(f"❌ HuggingFace embeddings failed: {e}")
            raise Exception("Please install: pip install sentence-transformers")
        
        # Initialize Gemini model (CORRECT way)
        self.gemini_model = genai.GenerativeModel(self.model)
        print(f"✅ Gemini model initialized!")
    
    # ============================================
    # PDF PROCESSING (UNCHANGED)
    # ============================================
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF menu"""
        try:
            if PDF_LIBRARY == "pypdf":
                reader = PdfReader(pdf_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
            else:
                doc = pymupdf.open(pdf_path)
                text = ""
                for page in doc:
                    text += page.get_text() + "\n"
                doc.close()
                return text
        except Exception as e:
            raise Exception(f"Error extracting PDF: {str(e)}")
    
    def parse_menu_items(self, text: str) -> List[MenuItem]:
        """Parse menu text to extract structured items"""
        items = []
        
        print(f"🔍 Analyzing text (length: {len(text)} chars)")
        
        patterns = [
            r'([A-Za-z\s&\-\']+?)[\s\.]+(?:Rs\.?\s*|PKR\s*|rs\.?\s*|pkr\s*)(\d{2,5})',
            r'([A-Za-z\s&\-\']{3,40}?)\s*[-—]\s*(\d{2,5})(?:\s|$|\.)',
            r'([A-Za-z\s&\-\']{3,40}?)\s{2,}(\d{2,5})(?:\s|$|\.)',
            r'(?:Rs\.?\s*|PKR\s*)?(\d{2,5})\s+([A-Za-z\s&\-\']{3,40})',
            r'([A-Za-z\s&\-\']{3,40}?)\.{2,}\s*(\d{2,5})',
        ]
        
        for pattern_idx, pattern in enumerate(patterns):
            matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                try:
                    if pattern_idx == 3:
                        price = float(match.group(1))
                        name = match.group(2).strip()
                    else:
                        name = match.group(1).strip()
                        price = float(match.group(2))
                    
                    name = re.sub(r'\s+', ' ', name)
                    name = name.strip('.-_')
                    
                    if len(name) < 3 or len(name) > 50:
                        continue
                    if price < 10 or price > 10000:
                        continue
                    if sum(c.isdigit() for c in name) > 3:
                        continue
                    
                    tags = []
                    name_lower = name.lower()
                    if any(word in name_lower for word in ['vegan', 'vegetarian', 'veggie']):
                        tags.append('vegetarian')
                    if any(word in name_lower for word in ['spicy', 'hot', 'chili', 'jalapeño']):
                        tags.append('spicy')
                    if any(word in name_lower for word in ['chicken', 'beef', 'mutton', 'fish', 'meat', 'lamb']):
                        tags.append('meat')
                    
                    items.append(MenuItem(
                        name=name,
                        price=price,
                        description="",
                        category=None,
                        tags=tags
                    ))
                except (ValueError, IndexError):
                    continue
        
        seen = {}
        unique_items = []
        for item in items:
            key = (item.name.lower(), item.price)
            if key not in seen:
                seen[key] = True
                unique_items.append(item)
        
        self.menu_items = unique_items
        
        if len(unique_items) == 0:
            print("⚠️ WARNING: No menu items found!")
        else:
            print(f"✅ Found {len(unique_items)} menu items")
            for item in unique_items[:5]:
                print(f"   - {item.name}: Rs {item.price}")
        
        return unique_items
    
    def process_menu(self, pdf_path: str):
        """Main processing pipeline"""
        print("📄 Extracting text from PDF...")
        text = self.extract_text_from_pdf(pdf_path)
        
        print("🍽️ Parsing menu items...")
        items = self.parse_menu_items(text)
        print(f"✅ Found {len(items)} menu items")
        
        print("✂️ Chunking text...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)
        print(f"✅ Created {len(chunks)} text chunks")
        
        print("🧠 Creating embeddings...")
        self.vectorstore = FAISS.from_texts(
            texts=chunks,
            embedding=self.embeddings
        )
        
        print("✅ Menu processed successfully!")
    
    # ============================================
    # CALLBACKS
    # ============================================
    
    def set_cart_callback(self, callback: Callable):
        """Set callback function to add items to cart"""
        self.cart_callback = callback
        print("✅ Cart callback connected")
    
    def set_order_callback(self, callback: Callable):
        """Set callback function to place orders"""
        self.order_callback = callback
        print("✅ Order callback connected")
    # Add these methods to your RestaurantRAG class

    def _detect_intent(self, question: str) -> Dict[str, any]:
        """
        Detect what user wants to do
        Returns: {
            'intent': 'order' | 'browse' | 'ask',
            'has_budget': bool,
            'budget': float or None,
            'keywords': List[str]
        }
        """
        question_lower = question.lower()
        
        # Order intent triggers
        order_triggers = [
            'order', 'want', 'get me', 'i need', 'hungry', 
            'buy', 'purchase', 'add', 'give me'
        ]
        
        # Check if user wants to order
        wants_to_order = any(trigger in question_lower for trigger in order_triggers)
        
        # Extract budget
        budget = self._extract_price_limit(question)
        
        # Extract food keywords
        keywords = []
        food_keywords = {
            'chicken': ['chicken'],
            'beef': ['beef'],
            'mutton': ['mutton', 'lamb'],
            'fish': ['fish'],
            'vegetarian': ['vegetarian', 'vegan', 'veggie'],
            'spicy': ['spicy', 'hot'],
            'rice': ['rice', 'biryani', 'pulao'],
            'bread': ['naan', 'roti', 'bread']
        }
        
        for category, words in food_keywords.items():
            if any(word in question_lower for word in words):
                keywords.append(category)
        
        return {
            'intent': 'order' if wants_to_order else 'browse',
            'has_budget': budget is not None,
            'budget': budget,
            'keywords': keywords
        }

    def _auto_select_items(self, intent_data: Dict) -> List[Dict]:
        """
        Automatically select items based on user intent
        This is the CORE agentic behavior
        """
        selected_items = []
        budget = intent_data.get('budget')
        keywords = intent_data.get('keywords', [])
        
        # If budget specified, create meal plan
        if budget:
            # Allocate budget: 50% main, 30% side, 20% drink
            main_budget = budget * 0.5
            side_budget = budget * 0.3
            drink_budget = budget * 0.2
            
            # Find main dish
            main_items = [
                item for item in self.menu_items
                if item.price <= main_budget and
                (not keywords or any(kw in ' '.join(item.tags + [item.name.lower()]) for kw in keywords))
            ]
            
            if main_items:
                # Pick best match or most expensive within budget
                main = max(main_items, key=lambda x: x.price)
                selected_items.append({
                    'name': main.name,
                    'price': main.price,
                    'quantity': 1
                })
                
                # Find side dish
                side_items = [
                    item for item in self.menu_items
                    if item.price <= side_budget and
                    any(word in item.name.lower() for word in ['naan', 'rice', 'roti', 'salad'])
                ]
                
                if side_items:
                    side = max(side_items, key=lambda x: x.price)
                    selected_items.append({
                        'name': side.name,
                        'price': side.price,
                        'quantity': 1
                    })
                
                # Find drink
                drink_items = [
                    item for item in self.menu_items
                    if item.price <= drink_budget and
                    any(word in item.name.lower() for word in ['drink', 'lassi', 'juice', 'water'])
                ]
                
                if drink_items:
                    drink = min(drink_items, key=lambda x: x.price)  # Cheapest drink
                    selected_items.append({
                        'name': drink.name,
                        'price': drink.price,
                        'quantity': 1
                    })
        
        # If keywords but no budget
        elif keywords:
            matching_items = []
            for item in self.menu_items:
                item_text = (item.name + ' ' + ' '.join(item.tags)).lower()
                if any(kw in item_text for kw in keywords):
                    matching_items.append(item)
            
            # Pick top 2-3 items
            matching_items.sort(key=lambda x: x.price, reverse=True)
            for item in matching_items[:2]:
                selected_items.append({
                    'name': item.name,
                    'price': item.price,
                    'quantity': 1
                })
        
        # Default: popular items
        else:
            for item in self.menu_items[:2]:
                selected_items.append({
                    'name': item.name,
                    'price': item.price,
                    'quantity': 1
                })
        
        return selected_items

    def query_agentic(self, question: str) -> Dict[str, any]:

    
        # Add to conversation history
        self.conversation_context.append({
            'role': 'user',
            'content': question,
            'timestamp': time.time()
        })
    
        # ============================================
        # CHECK IF USER IS REFERRING TO PREVIOUS ITEMS
        # ============================================
        referring_words = ['these', 'those', 'them', 'that', 'it', 'same', 'all']
        action_words = ['add', 'order', 'want', 'get', 'buy', 'take']
        
        question_lower = question.lower()
        is_referring_back = any(word in question_lower for word in referring_words)
        wants_action = any(word in question_lower for word in action_words)
        
        # If user says "add these/those/them" AND we have previous recommendations
        if is_referring_back and wants_action and self.last_recommended_items:
            print(f"🧠 MEMORY: User referring to previous {len(self.last_recommended_items)} items")
            
            # AUTO-ADD the previously recommended items
            added_items = []
            for item in self.last_recommended_items:
                if self.cart_callback:
                    self.cart_callback(item['name'], item['price'])
                    added_items.append(item)
            
            total = sum(item['price'] for item in added_items)
            items_text = "\n".join([
                f"✅ {item['name']} - Rs {item['price']}"
                for item in added_items
            ])
            
            answer = f"""Perfect! I've added those items to your cart:

    {items_text}

    💰 **Total: Rs {int(total)}**

    Ready to place your order? Just say **'Yes, place order'** and I'll help you complete it!"""
            
            # Store in conversation
            self.conversation_context.append({
                'role': 'assistant',
                'content': answer,
                'items_added': [item['name'] for item in added_items]
            })
            
            # Clear last recommended since we added them
            self.last_recommended_items = []
            
            return {
                "answer": answer,
                "source_documents": [],
                "recommendations": [],
                "actions_taken": [item['name'] for item in added_items],
                "agentic": True,
                "auto_added": True
            }
        
        # ============================================
        # DETECT INTENT
        # ============================================
        intent = self._detect_intent(question)
        
        # Get vector search context
        docs = self.vectorstore.similarity_search(question, k=3)
        menu_context = "\n".join([doc.page_content for doc in docs])
        
        # ============================================
        # INTENT: USER WANTS TO ORDER
        # ============================================
        if intent['intent'] == 'order':
            print(f"🤖 ORDER INTENT detected: budget={intent.get('budget')}, keywords={intent.get('keywords')}")
            
            selected_items = self._auto_select_items(intent)
            
            # AUTO-ADD to cart
            for item in selected_items:
                if self.cart_callback:
                    self.cart_callback(item['name'], item['price'])
            
            # Build response
            total = sum(item['price'] * item['quantity'] for item in selected_items)
            
            items_text = "\n".join([
                f"✅ {item['name']} - Rs {item['price']}"
                for item in selected_items
            ])
            
            answer = f"""Perfect! I've added these items to your cart:

    {items_text}

    💰 **Total: Rs {int(total)}**

    """
            
            if intent['has_budget']:
                remaining = intent['budget'] - total
                answer += f"Remaining from your Rs {intent['budget']} budget: Rs {int(remaining)}\n\n"
            
            answer += "Ready to place your order? Just say **'Yes, place order'** and provide your delivery address!"
            
            # Store in conversation
            self.conversation_context.append({
                'role': 'assistant',
                'content': answer,
                'items_added': [item['name'] for item in selected_items]
            })
            
            # Clear recommendations since we auto-added
            self.last_recommended_items = []
            
            return {
                "answer": answer,
                "source_documents": docs,
                "recommendations": self._get_relevant_items(question, None),
                "actions_taken": [item['name'] for item in selected_items],
                "agentic": True,
                "auto_added": True
            }
        
        # ============================================
        # INTENT: USER IS BROWSING/ASKING
        # ============================================
        else:
            print(f"📖 BROWSE INTENT: Showing recommendations, storing for memory")
            
            # Get normal query response
            result = self.query(question)
            
            # Store recommended items for next turn
            recommended = self._get_relevant_items(question, intent.get('budget'))
            self.last_recommended_items = recommended
            
            # Add to conversation context
            self.conversation_context.append({
                'role': 'assistant',
                'content': result['answer'],
                'recommended_items': [item['name'] for item in recommended]
            })
            
            print(f"💾 STORED {len(recommended)} items in memory: {[i['name'] for i in recommended[:3]]}")
            
            # Return with stored recommendations
            return {
                **result,
                "agentic": False,
                "stored_for_later": True  # Flag that we stored these
            }
    # ============================================
    # SIMPLIFIED QUERY (NO AGENT - WORKING)
    # ============================================
    
    def query(self, question: str) -> Dict[str, any]:
        """
        Simple working query with Gemini
        NO agent/function calling - just works!
        """
        
        if not self.vectorstore:
            raise Exception("Menu not processed yet. Call process_menu() first.")
        
        try:
            # Get relevant menu context from vector store
            docs = self.vectorstore.similarity_search(question, k=4)
            menu_context = "\n\n".join([doc.page_content for doc in docs])
            
            # Build menu items list for context
            menu_items_text = "\n".join([
                f"- {item.name}: Rs {item.price} {('(' + ', '.join(item.tags) + ')') if item.tags else ''}"
                for item in self.menu_items[:30]
            ])
            
            # Create prompt
            prompt = f"""You are a helpful restaurant assistant. Answer customer questions about the menu.

MENU CONTEXT FROM PDF:
{menu_context}

AVAILABLE ITEMS:
{menu_items_text}

CUSTOMER QUESTION: {question}

INSTRUCTIONS:
- Answer ONLY based on the menu information above
- Always mention specific items and their prices (Rs XXX)
- Be friendly and conversational
- If recommending items, suggest 2-3 with prices
- For dietary preferences (vegetarian, spicy), filter accordingly
- If item not found, politely say it's not on the menu

Your answer:"""

            # Call Gemini (CORRECT way with modern SDK)
            response = self.gemini_model.generate_content(prompt)
            answer = response.text
            
            # Get recommendations for display
            recommendations = self._get_relevant_items(question, None)
            
            # Save to history
            self.customer_memory['chat_history'].append({
                'role': 'user',
                'content': question
            })
            self.customer_memory['chat_history'].append({
                'role': 'assistant',
                'content': answer
            })
            
            return {
                "answer": answer,
                "source_documents": docs,
                "recommendations": recommendations,
                "actions_taken": [],
                "agentic": False
            }
        
        except Exception as e:
            print(f"❌ Query error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                "answer": f"Sorry, I encountered an error: {str(e)}. Please try rephrasing your question.",
                "source_documents": [],
                "recommendations": self._get_relevant_items(question, None)[:3],
                "actions_taken": [],
                "agentic": False
            }
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    def _get_relevant_items(self, question: str, price_limit: Optional[float] = None) -> List[Dict]:
    
        if not self.menu_items:
            return []
        
        question_lower = question.lower()
        relevant_items = []
        
        keywords = {
            'chicken': ['chicken'],
            'beef': ['beef'],
            'mutton': ['mutton', 'lamb'],
            'fish': ['fish', 'seafood'],
            'vegan': ['vegan', 'vegetarian'],
            'spicy': ['spicy', 'hot'],
            'rice': ['rice', 'biryani', 'pulao'],
            'bread': ['bread', 'naan', 'roti'],
            'drink': ['drink', 'juice', 'coffee', 'tea', 'lassi'],
            'dessert': ['dessert', 'sweet', 'ice cream', 'cake']
        }
        
        # Extract price limit from question if mentioned
        if not price_limit:
            price_limit = self._extract_price_limit(question)
        
        for item in self.menu_items:
            item_name_lower = item.name.lower()
            
            # Price filter FIRST
            if price_limit and item.price > price_limit:
                continue
            
            # Check if question directly mentions this item
            if any(word in question_lower for word in item_name_lower.split()):
                relevant_items.append({
                    "name": item.name, 
                    "price": item.price,
                    "tags": item.tags
                })
                continue
            
            # Check keyword categories
            for category, words in keywords.items():
                if any(word in question_lower for word in words):
                    if any(word in item_name_lower for word in words):
                        relevant_items.append({
                            "name": item.name,
                            "price": item.price,
                            "tags": item.tags
                        })
                        break
        
        # Apply price filter if specified
        if price_limit:
            relevant_items = [item for item in relevant_items if item['price'] <= price_limit]
        
        # If no specific matches, return popular items
        if not relevant_items:
            relevant_items = [
                {
                    "name": item.name,
                    "price": item.price,
                    "tags": item.tags
                }
                for item in self.menu_items[:6]
            ]
        
        return relevant_items[:6]
    
    def _extract_price_limit(self, question: str) -> Optional[float]:
        """Extract price limit from question"""
        patterns = [
            r'under\s+(?:Rs\.?\s*|PKR\s*)?(\d+)',
            r'below\s+(?:Rs\.?\s*|PKR\s*)?(\d+)',
            r'less than\s+(?:Rs\.?\s*|PKR\s*)?(\d+)',
            r'maximum\s+(?:Rs\.?\s*|PKR\s*)?(\d+)',
            r'(?:Rs\.?\s*|PKR\s*)?(\d+)\s+budget',
            r'budget.*?(?:Rs\.?\s*|PKR\s*)?(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, question.lower())
            if match:
                return float(match.group(1))
        return None
    
    def reset_conversation(self):
        """Reset conversation memory"""
        self.customer_memory['chat_history'] = []
        self.customer_memory['last_items'] = []
        print("🔄 Conversation reset")