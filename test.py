import re

def extract_keywords(text, patterns):
    """
    Extract keywords from the text based on category patterns.

    Args:
        text (str): The input text.
        patterns (list): A list of patterns to match, each being a dictionary with 'label' and 'pattern'.

    Returns:
        list: A list of extracted keywords matching the category patterns.
    """
    extracted_keywords = set()  # Use a set to prevent duplicates
    
    for pattern in patterns:
        if isinstance(pattern["pattern"], str):
            # Exact string match (case-insensitive)
            if pattern["pattern"].lower() in text.lower():
                extracted_keywords.add(pattern["pattern"])
        elif isinstance(pattern["pattern"], dict):
            # Regex match
            regex = pattern["pattern"].get("REGEX")
            if regex and re.search(regex, text, re.IGNORECASE):
                match = re.search(regex, text, re.IGNORECASE)
                if match:
                    extracted_keywords.add(match.group())
    
    return list(extracted_keywords)

# Example usage
text = "I love aple products and Samsung devices. I recently bought a Sony TV and a Tesla car."
patterns = [
    {"label": "BRAND", "pattern": "Apple"},
    {"label": "BRAND", "pattern": {"REGEX": r"(?i)samsung"}},
    {"label": "BRAND", "pattern": {"REGEX": r"(?i)sony"}},
    {"label": "BRAND", "pattern": {"REGEX": r"(?i)tesla"}},
]

print(extract_keywords(text, patterns))
