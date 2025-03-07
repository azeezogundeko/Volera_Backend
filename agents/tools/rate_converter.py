import httpx
from utils.request_session import http_client

CURRENCY_SYMBOLS = {
    "$": "usd",
    "€": "eur",
    "₦": "ngn",
    "£": "gbp",
    "₵": "ghs"
}

async def get_exchange_rate(from_currency: str, to_currency: str, date: str = "latest"):
    primary_url = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date}/v1/currencies/{from_currency}.json"
    fallback_url = f"https://{date}.currency-api.pages.dev/v1/currencies/{from_currency}.json"
    
    try:
        # with httpx.Client(timeout=5) as client:
            response = await http_client.get(primary_url)
            response.raise_for_status()
    except (httpx.RequestError, httpx.HTTPStatusError):
        # If the primary API fails, try the fallback URL
        # with httpx.Client(timeout=5) as client:
            response = await http_client.get(fallback_url)
            response.raise_for_status()
    
    data = response.json()
    
    if to_currency in data[from_currency]:
        return data[from_currency][to_currency]
    else:
        raise ValueError(f"Exchange rate for {to_currency} not found.")

async def convert_currency(amount: float, from_currency: str, to_currency: str, date: str = "latest"):
    rate = await get_exchange_rate(from_currency, to_currency, date)
    return round(amount * rate, 2)

def normalize_currency(currency: str):
    """Convert currency symbol to currency code if necessary."""
    return CURRENCY_SYMBOLS.get(currency, currency.lower())


# Example Usage
if __name__ == "__main__":
    amount = 100
    from_currency = "usd"
    to_currency = "eur"
    converted_amount = convert_currency(amount, from_currency, to_currency)
    print(f"{amount} {from_currency.upper()} is approximately {converted_amount} {to_currency.upper()}")