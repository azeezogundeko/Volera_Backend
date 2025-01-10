import requests
import json

# Define the Algolia endpoint and credentials
ALGOLIA_APP_ID = "B9ZCRRRVOM"  # Replace with your Algolia Application ID
ALGOLIA_API_KEY = "1013eebf1ca008149d66ea7a385a1366"  # Replace with your Algolia Admin or Search-only API Key
ALGOLIA_URL = f"https://{ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes/*/queries"

# Headers for the request
headers = {
    "X-Algolia-Application-Id": ALGOLIA_APP_ID,
    "X-Algolia-API-Key": ALGOLIA_API_KEY,
    "Content-Type": "application/json",
}

# JSON payload (the batch request)
payload = {
    "requests": [
        {
        "indexName": "catalog_store_konga_price_asc",
        "params": "query=&facetFilters=[\"attributes.brand:Lenovo\"]"
        },
        {
            "indexName": "catalog_store_konga_price_asc",
            "params": (
                "query=&"
                "maxValuesPerFacet=50&"
                "page=0&"
                "highlightPreTag=<ais-highlight-0000000000>&"
                "highlightPostTag=</ais-highlight-0000000000>&"
                "hitsPerPage=1&"
                "attributesToRetrieve=[]&"
                "attributesToHighlight=[]&"
                "attributesToSnippet=[]&"
                "analytics=false&"
                "clickAnalytics=false&"
                "facets=attributes.brand"
            ),
        },
    ]
}

# Send the POST request
response = requests.post(ALGOLIA_URL, headers=headers, json=payload)

# Check for successful response
if response.status_code == 200:
    print("Response from Algolia:")
    print(json.dumps(response.json(), indent=2))  # Pretty-print JSON response
    import json
    with open("algolia_response.json", "w") as f:
        json.dump(response.json(), f, indent=4)
else:
    print(f"Error: {response.status_code}")
    print(response.text)
