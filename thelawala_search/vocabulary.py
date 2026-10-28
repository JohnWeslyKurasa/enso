"""Vocabulary and Synonym Mappings for Thelawala Search.

Supports:
- Telugu colloquial terms (both Latin transliteration and Telugu Unicode script)
- Hindi / Hinglish grocery terms
- Common grocery synonyms (e.g., 'red lentils' -> 'masoor dal', 'refined oil' -> 'sunflower oil')
"""

from typing import Dict, List, Set

# Telugu Script to English grocery mappings
TELUGU_SCRIPT_SYNONYMS: Dict[str, str] = {
    "పాలు": "milk",
    "గేదె పాలు": "buffalo milk",
    "వెన్న": "butter",
    "పెరుగు": "curd",
    "మజ్జిగ": "buttermilk",
    "గుడ్లు": "eggs",
    "గుడ్డు": "egg",
    "నిమ్మకాయ": "lemon",
    "బియ్యం": "rice",
    "బియ్యం పిండి": "rice flour",
    "ఉల్లిపాయ": "onion",
    "బెల్లం": "jaggery",
    "నెయ్యి": "ghee",
    "కంది పప్పు": "toor dal",
    "టమాట": "tomato",
    "ఆవకాయ": "mango pickle",
    "పసుపు": "turmeric powder",
    "మునగకాయ": "drumstick",
    "పప్పు": "dal",
    "నూనె": "oil",
}

# Devanagari Hindi to English grocery mappings
HINDI_SCRIPT_SYNONYMS: Dict[str, str] = {
    "दूध": "milk",
    "दही": "curd",
    "घी": "ghee",
    "चावल": "rice",
    "आटा": "atta",
    "दाल": "dal",
    "तेल": "oil",
}

# Transliterated Telugu & Hinglish to English grocery mappings
TRANSLITERATED_SYNONYMS: Dict[str, str] = {
    # Telugu transliteration
    "paalu": "milk",
    "gede paalu": "buffalo milk",
    "venna": "butter",
    "biyyam pindi": "rice flour",
    "biyyam": "rice",
    "perugu": "curd",
    "majiga": "buttermilk",
    "majjiga": "buttermilk",
    "gudlu": "eggs",
    "guddu": "eggs",
    "nimmakaya": "lemon",
    "ullipaya": "onion",
    "bellam": "jaggery",
    "neyyi": "ghee",
    "kandi pappu": "toor dal",
    "tamata": "tomato",
    "avakaya": "mango pickle",
    "pasupu": "turmeric",
    "munagakaya": "drumstick",
    "pappu": "dal",
    "nune": "oil",
    "miriyalu": "black pepper",
    "dhaniyalu": "coriander seeds",
    "jeelakarra": "cumin seeds",
    "chintha pandu": "tamarind",

    # Hindi / Hinglish
    "doodh": "milk",
    "dahi": "curd",
    "haldi": "turmeric",
    "jeera": "cumin",
    "dhaniya": "coriander",
    "mirchi": "chilli",
    "adrak": "ginger",
    "lehsun": "garlic",
    "elaichi": "cardamom",
    "laung": "clove",
    "methi": "fenugreek",
    "poha": "flattened rice",
    "suji": "rava semolina",
    "sooji": "rava semolina",
    "mawa": "milk khoya",
    "khoya": "milk powder",

    # Conceptual grocery synonyms
    "red lentils": "masoor dal",
    "refined oil": "sunflower oil",
    "cooking oil": "sunflower oil",
    "low fat milk": "toned milk double toned milk",
    "skimmed milk": "double toned milk",
    "brown bread": "multigrain bread whole wheat",
    "peanut butter": "peanut butter",
}

# Known brand names in catalog for brand protection (Kavya's rule)
KNOWN_BRANDS: Set[str] = {
    "godavari dairy",
    "godavari",
    "gomatha",
    "krishna valley",
    "thela select",
    "thela fresh",
    "deccan gold",
    "fizzo",
    "purely",
    "biscoo",
    "kaapi house",
    "snackwala",
    "crispo",
    "chocomore",
    "morning oven",
    "golconda grains",
    "annapurna mills",
    "kisanpur",
    "kalpavriksha",
    "ammas kitchen",
    "amma kitchen",
    "suryakanti",
    "ruchi andhra",
    "henfresh",
    "sparkle",
    "local farm",
}


def expand_query_synonyms(query_text: str) -> str:
    """Expands Telugu/Hinglish/Synonym terms into normalized catalog terms."""
    q = query_text.strip().lower()

    # 1. Exact phrase substitution
    if q in TELUGU_SCRIPT_SYNONYMS:
        return f"{q} {TELUGU_SCRIPT_SYNONYMS[q]}"
    if q in HINDI_SCRIPT_SYNONYMS:
        return f"{q} {HINDI_SCRIPT_SYNONYMS[q]}"
    if q in TRANSLITERATED_SYNONYMS:
        return f"{q} {TRANSLITERATED_SYNONYMS[q]}"

    # 2. Multi-word phrase substitution within query
    expanded = q
    for phrase, target in sorted(TRANSLITERATED_SYNONYMS.items(), key=lambda x: -len(x[0])):
        if phrase in expanded:
            expanded = expanded.replace(phrase, f"{phrase} {target}")

    for phrase, target in sorted(TELUGU_SCRIPT_SYNONYMS.items(), key=lambda x: -len(x[0])):
        if phrase in expanded:
            expanded = expanded.replace(phrase, f"{phrase} {target}")

    return expanded
