import httpx

class HttpClient:
    def __init__(self, base_url: str = None, headers: dict = None, timeout: int = 10):
        """
        Initializes the HttpClient with optional base_url, headers, and timeout.
        """
        self.base_url = base_url
        self.headers = headers or {}
        self.timeout = timeout
        self.client = None

    def initialize(self):
        """
        Creates an httpx.AsyncClient instance.
        """
        if self.client is None:
            self.client = httpx.AsyncClient()

    async def close(self):
        """
        Closes the httpx.AsyncClient instance.
        """
        if self.client:
            await self.client.aclose()
            self.client = None

    async def get(self, url: str, **kwargs):
        """
        Sends a GET request.
        """
        if not self.client:
            raise RuntimeError("HttpClient is not initialized.")
        response = await self.client.get(url, **kwargs)
        response.raise_for_status()
        return response

    async def post(self, url: str, data: dict = None, json: dict = None, **kwargs):
        """
        Sends a POST request.
        """
        if not self.client:
            raise RuntimeError("HttpClient is not initialized.")
        response = await self.client.post(url, data=data, json=json, **kwargs)
        return response

    # Add more methods (put, delete, etc.) as needed.

http_client = HttpClient()