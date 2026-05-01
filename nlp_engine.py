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
- Traffic violations, fines, challan
