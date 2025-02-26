import zlib
import base62  # Install with: pip install pybase62

def shorten_url(url: str) -> str:
    # Compress the URL and encode to Base62
    compressed = zlib.compress(url.encode('utf-8'), level=9)
    encoded = base62.encodebytes(compressed)
    # Return first 20 characters (truncate if necessary)
    return encoded

def restore_url(short_id: str) -> str:
    # Decode Base62 and decompress
    compressed = base62.decodebytes(short_id)
    original = zlib.decompress(compressed)
    return original.decode('utf-8')

original_url = "https://www.example.com/some/long/path?query=param"
short_id = shorten_url(original_url)  # e.g., "1a2b3c4d5e6f7g8h9i0j"
restored_url = restore_url(short_id)  # Matches original_url

print(short_id)
print(restored_url)
