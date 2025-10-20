import os
import re
import json
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
        """Extract menu items relevant to the question"""
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
            
            # Check if question directly mentions this item
            if any(word in question_lower for word in item_name_lower.split()):
                relevant_items.append({"name": item.name, "price": item.price})
                continue
            
            # Check keyword categories
            for category, words in keywords.items():
                if any(word in question_lower for word in words):
                    if any(word in item_name_lower for word in words):
                        relevant_items.append({"name": item.name, "price": item.price})
                        break
        
        # Apply price filter if specified
        if price_limit:
            relevant_items = [item for item in relevant_items if item['price'] <= price_limit]
        
        # If no specific matches, return popular items
        if not relevant_items:
            relevant_items = [
                {"name": item.name, "price": item.price} 
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