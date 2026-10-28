"""Query Parser for Thelawala Search.

Handles:
- Extraction of price filters (e.g., 'oil under 200', 'ghee below 500', 'curd < 40')
- Normalization and punctuation cleanup (e.g., 'Amma\'s Kitchen' -> 'ammas kitchen')
- Token extraction and price constraint resolution
"""

import re
from typing import Optional, Tuple, List, Dict, Any

class ParsedQuery:
    def __init__(
        self,
        raw_query: str,
        clean_query: str,
        tokens: List[str],
        max_price: Optional[float] = None,
        min_price: Optional[float] = None
    ):
        self.raw_query = raw_query
        self.clean_query = clean_query
        self.tokens = tokens
        self.max_price = max_price
        self.min_price = min_price

    def __repr__(self) -> str:
        return (
            f"ParsedQuery(clean='{self.clean_query}', tokens={self.tokens}, "
            f"max_price={self.max_price}, min_price={self.min_price})"
        )


def parse_query(raw_query: str) -> ParsedQuery:
    """Parses a raw search query string into clean tokens and price filters."""
    if not raw_query:
        return ParsedQuery(raw_query="", clean_query="", tokens=[])

    text = raw_query.strip()
    max_price: Optional[float] = None
    min_price: Optional[float] = None

    # 1. Regex patterns for price constraints
    # e.g., 'under 200', 'below 500', '< 100', '<= 50', 'less than 150', 'upto 200', 'up to 200'
    under_pattern = re.compile(
        r'\b(?:under|below|less than|upto|up to|within)\s*(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)\b',
        re.IGNORECASE
    )
    symbol_under_pattern = re.compile(
        r'(?:<=|<)\s*(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)',
        re.IGNORECASE
    )
    
    # e.g., 'above 100', '> 50', 'more than 200'
    above_pattern = re.compile(
        r'\b(?:above|over|more than|greater than)\s*(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)\b',
        re.IGNORECASE
    )
    symbol_above_pattern = re.compile(
        r'(?:>=|>)\s*(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)',
        re.IGNORECASE
    )

    # Check 'under' matches
    m = under_pattern.search(text)
    if m:
        max_price = float(m.group(1))
        text = under_pattern.sub(" ", text)
    else:
        m_sym = symbol_under_pattern.search(text)
        if m_sym:
            max_price = float(m_sym.group(1))
            text = symbol_under_pattern.sub(" ", text)

    # Check 'above' matches
    m_ab = above_pattern.search(text)
    if m_ab:
        min_price = float(m_ab.group(1))
        text = above_pattern.sub(" ", text)
    else:
        m_ab_sym = symbol_above_pattern.search(text)
        if m_ab_sym:
            min_price = float(m_ab_sym.group(1))
            text = symbol_above_pattern.sub(" ", text)

    # Handle suffix like "200 rs", "50 rupees" if preceded by "under" or remaining standalone
    trailing_currency = re.compile(r'\b(?:rs\.?|rupees|inr|bucks)\b', re.IGNORECASE)
    text = trailing_currency.sub(" ", text)

    # 2. Clean punctuation and apostrophes (e.g. Amma's -> Ammas, fruit & nut -> fruit nut)
    text = re.sub(r"['’]", "", text)
    text = re.sub(r"[^\w\s\u0C00-\u0C7F\u0900-\u097F]", " ", text) # Preserve Telugu and Devanagari Unicode
    text = re.sub(r"\s+", " ", text).strip().lower()

    tokens = [t for t in text.split(" ") if t]

    return ParsedQuery(
        raw_query=raw_query,
        clean_query=text,
        tokens=tokens,
        max_price=max_price,
        min_price=min_price
    )
