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

# Define patterns (mix of exact and regex)
brand_patterns = [
    # Tech Brands
    {"label": "BRAND", "pattern": "Apple"},
    {"label": "BRAND", "pattern": [{"LOWER": "samsung"}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)sony"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)dell"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)hp"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)lenovo"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)acer"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)asus"}}]},

    # Fashion Brands
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)h&m"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)zara"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)gucci"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)prada"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)burberry"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)louis vuitton"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)nike"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)adidas"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)puma"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)reebok"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)under armour"}}]},

    # Automotive Brands
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)toyota"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)honda"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)ford"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)bmw"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)mercedes(-benz)?"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)tesla"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)audi"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)chevrolet"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)hyundai"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)nissan"}}]},

    # Food & Beverage Brands
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)coca(-cola)?"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)pepsi"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)nestle"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)kfc"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)mcdonald's"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)starbucks"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)domino's"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)burger king"}}]},

    # Miscellaneous
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)lego"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)ikea"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)amazon"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)google"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)microsoft"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)facebook"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)tiktok"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)netflix"}}]},
    {"label": "BRAND", "pattern": [{"TEXT": {"REGEX": r"(?i)spotify"}}]},
]


category_patterns = [
    # Appliances
    {"label": "CATEGORY", "pattern": "Appliances"},
    {"label": "CATEGORY", "pattern": "Small Appliances"},
    {"label": "CATEGORY", "pattern": "Blenders"},
    {"label": "CATEGORY", "pattern": "Deep Fryers"},
    {"label": "CATEGORY", "pattern": "Juicers"},
    {"label": "CATEGORY", "pattern": "Air Fryers"},
    {"label": "CATEGORY", "pattern": "Rice Cookers"},
    {"label": "CATEGORY", "pattern": "Toasters & Ovens"},
    {"label": "CATEGORY", "pattern": "Microwaves"},
    {"label": "CATEGORY", "pattern": "Bundles"},
    {"label": "CATEGORY", "pattern": "Vacuum Cleaners"},
    {"label": "CATEGORY", "pattern": "Kettles"},
    {"label": "CATEGORY", "pattern": "Yam Pounders"},
    {"label": "CATEGORY", "pattern": "Irons"},
    {"label": "CATEGORY", "pattern": "Electric Cookware"},
    {"label": "CATEGORY", "pattern": "Electric Drink Mixers"},
    {"label": "CATEGORY", "pattern": "Food Processors"},
    {"label": "CATEGORY", "pattern": "Coffee Makers"},
    {"label": "CATEGORY", "pattern": "Electric Pressure Cookers"},
    
    # Large Appliances
    {"label": "CATEGORY", "pattern": "Large Appliances"},
    {"label": "CATEGORY", "pattern": "Washing Machines"},
    {"label": "CATEGORY", "pattern": "Fridges"},
    {"label": "CATEGORY", "pattern": "Freezers"},
    {"label": "CATEGORY", "pattern": "Air Conditioners"},
    {"label": "CATEGORY", "pattern": "Heaters"},
    {"label": "CATEGORY", "pattern": "Fans"},
    {"label": "CATEGORY", "pattern": "Air Purifiers"},
    {"label": "CATEGORY", "pattern": "Water Dispensers"},
    {"label": "CATEGORY", "pattern": "Generators & Inverters"},
    
    # Brands (within category context)
    {"label": "CATEGORY", "pattern": "Nexus"},
    {"label": "CATEGORY", "pattern": "Hisense"},
    {"label": "CATEGORY", "pattern": "Polystar"},
    {"label": "CATEGORY", "pattern": "TCL"},
    
    # Phones & Tablets
    {"label": "CATEGORY", "pattern": "Phones & Tablets"},
    
    # Health & Beauty
    {"label": "CATEGORY", "pattern": "Health & Beauty"},
    
    # Home & Office
    {"label": "CATEGORY", "pattern": "Home & Office"},
    
    # Electronics
    {"label": "CATEGORY", "pattern": "Electronics"},
    
    # Fashion
    {"label": "CATEGORY", "pattern": "Fashion"},
    
    # Supermarket
    {"label": "CATEGORY", "pattern": "Supermarket"},
    
    # Computing
    {"label": "CATEGORY", "pattern": "Computing"},
    
    # Baby Products
    {"label": "CATEGORY", "pattern": "Baby Products"},
    
    # Gaming
    {"label": "CATEGORY", "pattern": "Gaming"},
    
    # Musical Instruments
    {"label": "CATEGORY", "pattern": "Musical Instruments"},
    
    # Other categories (catch-all)
    {"label": "CATEGORY", "pattern": "Other categories"},

    # Regex Patterns (Optional: You can add regex patterns for compound or variations)
    {"label": "CATEGORY", "pattern": [{"TEXT": {"REGEX": r"(?i)small appliances"}}]},
    {"label": "CATEGORY", "pattern": [{"TEXT": {"REGEX": r"(?i)home & office"}}]},
    {"label": "CATEGORY", "pattern": [{"TEXT": {"REGEX": r"(?i)health & beauty"}}]},
    {"label": "CATEGORY", "pattern": [{"TEXT": {"REGEX": r"(?i)phones and tablets"}}]},
    {"label": "CATEGORY", "pattern": [{"TEXT": {"REGEX": r"(?i)baby products"}}]},
    {"label": "CATEGORY", "pattern": [{"TEXT": {"REGEX": r"(?i)gaming"}}]},
    {"label": "CATEGORY", "pattern": [{"TEXT": {"REGEX": r"(?i)musical instruments"}}]},
]

def extract_brands(text):
    brands = extract_keywords(text, brand_patterns)
    if brands:
        return brands[0]
    return None

# Function to extract Categories
def extract_categories(text):
    categories = extract_keywords(text, category_patterns)
    print(categories)
    if categories:
        return categories[0]
    return None

