import requests
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_proxy_url():
    """Get proxy URL from environment variables"""
    proxy_host = os.getenv('PROXY_HOST')
    proxy_port = os.getenv('PROXY_PORT')
    proxy_auth = os.getenv('PROXY_AUTH')
    
    if not all([proxy_host, proxy_port, proxy_auth]):
        raise ValueError("Missing proxy configuration in .env file")
    
    return f"http://{proxy_auth}@{proxy_host}:{proxy_port}"

def test_proxy_connection():
    """Test proxy connection with multiple endpoints"""
    proxy_url = get_proxy_url()
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    test_urls = [
        ('http://httpbin.org/ip', 'HTTP'),
        ('https://ipv4.icanhazip.com', 'HTTPS'),
        ('https://api.ipify.org?format=json', 'HTTPS API')
    ]
    
    print("Testing proxy configuration...")
    print(f"Proxy URL format: {proxy_url.replace(os.getenv('PROXY_AUTH'), '***:***@')}")
    
    for url, protocol in test_urls:
        try:
            time_start = time.time()
            response = requests.get(url, proxies=proxies, timeout=10)
            time_end = time.time()
            
            print(f"\n{protocol} Test ({url}):")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text.strip()}")
            print(f"Time taken: {time_end - time_start:.2f} seconds")
            
        except requests.exceptions.RequestException as e:
            print(f"\nError testing {protocol} connection ({url}):")
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    try:
        test_proxy_connection()
    except Exception as e:
        print(f"Configuration Error: {str(e)}")