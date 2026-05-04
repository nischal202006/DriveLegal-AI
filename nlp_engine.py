"""
NLP Engine â€” DriveLegal.ai
Gemini-first conversational AI with rule-based offline fallback.
Domain-restricted to road safety, traffic law, and driving assistance.
"""

import re, os, json, time
from collections import defaultdict
import datetime

SYSTEM_PROMPT = """You are DriveLegal.ai, a professional road safety and Indian traffic law assistant.

YOUR DOMAIN (answer ONLY these topics):
- Indian traffic laws and the Motor Vehicles (Amendment) Act, 2019
- Traffic violations, fines, challans, and penalties
- State-specific traffic rules and overrides
- Road safety education and best practices
- Emergency helpline numbers and accident procedures
- Vehicle documentation and driving license rules

STRICT RULES:
1. NEVER answer questions outside road safety, traffic law, or driving assistance. If a user asks about politics, programming, jokes, or general knowledge, politely decline and steer them back to traffic laws.
2. Always cite the specific Section of the Motor Vehicles Act when discussing violations.
3. Use INR (Rs.) for all fine amounts. Never use emojis.
4. Be conversational, professional, and concise. Do not write essays. Use bullet points for multiple items.
5. If you do not know the exact fine, state clearly that it varies and advise checking with local authorities.
6. When calculating fines for a state, remember that some states have different structures than the national act.

Context: You will be provided with some JSON data containing relevant rules or fine amounts to help answer the user's query. Use it accurately.
"""


class NLPEngine:
    """Gemini-first AI engine with rule-based offline fallback."""

    def __init__(self, db=None):
        self.db = db
        self.gemini_model = None
        self.chat_sessions = {}
        self._init_gemini()
        self.fallback_patterns = self._compile_fallback_patterns()

    def _init_gemini(self):
        """Initialize the Gemini API client."""
        api_key = os.environ.get('GEMINI_API_KEY', '')
        if not api_key:
            print("WARNING: GEMINI_API_KEY not found. NLP Engine will run in OFFLINE fallback mode only.")
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel(
                model_name='gemini-2.0-flash',
                system_instruction=SYSTEM_PROMPT,
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                }
            )
            print("SUCCESS: Gemini 2.0 API initialized.")
        except Exception as e:
            print(f"ERROR: Failed to initialize Gemini API: {e}")
            self.gemini_model = None

    def _compile_fallback_patterns(self):
        """Compile regex patterns for the offline rule-based fallback engine."""
        patterns = {
            'helmet': re.compile(r'\b(helmet|without helmet|no helmet)\b', re.IGNORECASE),
            'seatbelt': re.compile(r'\b(seatbelt|seat belt|without seat belt)\b', re.IGNORECASE),
            'speeding': re.compile(r'\b(speeding|overspeeding|fast driving|speed limit)\b', re.IGNORECASE),
            'drunk': re.compile(r'\b(drunk|drinking|alcohol|dui|dwi)\b', re.IGNORECASE),
            'license': re.compile(r'\b(license|driving license|dl|without license)\b', re.IGNORECASE),
            'signal': re.compile(r'\b(red light|signal|jumping signal|stop sign)\b', re.IGNORECASE),
            'phone': re.compile(r'\b(phone|mobile|talking on phone|texting)\b', re.IGNORECASE),
            'pollution': re.compile(r'\b(puc|pollution|emissions|smog)\b', re.IGNORECASE),
            'insurance': re.compile(r'\b(insurance|without insurance|uninsured)\b', re.IGNORECASE),
            'emergency': re.compile(r'\b(emergency|ambulance|accident|sos|help|police)\b', re.IGNORECASE),
        }
        return patterns

    def _get_context(self, message):
        """Extract relevant context from the database based on the message."""
        if not self.db:
            return ""

        context_items = []
        msg_lower = message.lower()
        
        # Check against all violations in the DB
        all_violations = self.db.get_all_violations()
        for key, v in all_violations.items():
            # Check if name or keywords match
            keywords = v.get('keywords', [])
            keywords.append(v.get('name', '').lower())
            
            for keyword in keywords:
                if keyword in msg_lower:
                    context_items.append(
                        f"Violation: {v.get('name')}\n"
                        f"Section: {v.get('section')}\n"
                        f"Fine: Rs. {v.get('fine', 'Varies')}\n"
                        f"Penalty: {v.get('penalty', 'None')}"
                    )
                    break
        
        if not context_items:
            return ""
            
        return "DATABASE CONTEXT (Use this to answer accurately):\n" + "\n---\n".join(context_items[:3])

    def process(self, message, location=None, session_id='default'):
        """
        Process a user message.
        Attempts Gemini first, falls back to rule-based matching if offline/failed.
        """
        start_time = time.time()
        
        # Domain filtering - check for obvious out-of-domain prompts to save API calls
        out_of_domain = re.search(r'\b(write a poem|code|python|java|html|joke|recipe|movie|politics)\b', message, re.IGNORECASE)
        if out_of_domain:
            return {
                'text': "I am DriveLegal.ai, a specialized assistant for Indian traffic laws and road safety. I cannot assist with topics outside of my domain.",
                'data': {'type': 'rejection'},
                'confidence': 'High',
                'latency_ms': int((time.time() - start_time) * 1000)
            }

        # Session management
        if session_id not in self.chat_sessions:
            if self.gemini_model:
                self.chat_sessions[session_id] = self.gemini_model.start_chat(history=[])
            else:
                self.chat_sessions[session_id] = [] # Fallback history

        context = self._get_context(message)
        
        # Try Gemini API
        if self.gemini_model:
            try:
                chat = self.chat_sessions[session_id]
                
                # Inject context transparently
                full_prompt = message
                if context:
                    full_prompt = f"{context}\n\nUser Question: {message}"
                
                response = chat.send_message(full_prompt)
                
                return {
                    'text': response.text.replace('**', ''), # Strip markdown bolding for UI
                    'data': {'type': 'ai_response', 'source': 'gemini-2.0'},
                    'confidence': 'High',
                    'latency_ms': int((time.time() - start_time) * 1000)
                }
            except Exception as e:
                print(f"Gemini API Error: {e}. Falling back to rule-based engine.")

        # â”€â”€ 
