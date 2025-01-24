import os
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import string

from config import ID_SECRET_KEY

# Base62 encoding/decoding
BASE62_ALPHABET = string.ascii_letters + string.digits

def base62_encode(data):
    result = []
    num = int.from_bytes(data, byteorder='big')
    base = len(BASE62_ALPHABET)

    while num:
        num, rem = divmod(num, base)
        result.append(BASE62_ALPHABET[rem])

    return ''.join(reversed(result))

def base62_decode(data):
    num = 0
    base = len(BASE62_ALPHABET)

    for char in data:
        num = num * base + BASE62_ALPHABET.index(char)

    return num.to_bytes((num.bit_length() + 7) // 8, byteorder='big')

# Encryption and Decryption
class TextEncryptor:
    def __init__(self, key):
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, plaintext):
        cipher = AES.new(self.key, AES.MODE_CBC)
        iv = cipher.iv
        ciphertext = cipher.encrypt(pad(plaintext.encode(), AES.block_size))
        encoded = base62_encode(iv + ciphertext)
        return encoded[:36]  # Ensure the result is 36 characters long

    def decrypt(self, encoded_text):
        encoded_data = base62_decode(encoded_text)
        iv = encoded_data[:16]
        ciphertext = encoded_data[16:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv=iv)
        plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return plaintext.decode()


ID = TextEncryptor(ID_SECRET_KEY)

# Example usage
if __name__ == "__main__":
    secret_key = "your_secret_key_here"  # Use a secure key
    encryptor = TextEncryptor(secret_key)

    original_text = "HelloWorldExampleText"
    encrypted_id = encryptor.encrypt(original_text)
    decrypted_text = encryptor.decrypt(encrypted_id)

    print(f"Original Text: {original_text}")
    print(f"Encrypted ID: {encrypted_id}")
    print(f"Decrypted Text: {decrypted_text}")
