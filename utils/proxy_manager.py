import asyncio
import httpx
import logging
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
import random
import time
import aiohttp
import os
import json

logger = logging.getLogger(__name__)

@dataclass
class ProxyInfo:
    host: str
    port: int
    protocol: str = "http"
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None
    anonymity: Optional[str] = None
    speed: Optional[int] = None  # in ms
    last_checked: Optional[float] = None
    is_working: bool = True
    is_rotating: bool = False

@dataclass
class RotatingProxyInfo(ProxyInfo):
    def __init__(self, domain: str, port: int, username: str, password: str):
        super().__init__(
            host=domain,
            port=port,
            protocol="http",
            username=username,
            password=password,
            is_rotating=True
        )

class ProxyManager:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, test_url: str = "https://www.volera.app"):
        if not ProxyManager._initialized:
            self.test_url = test_url
            self.headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Upgrade-Insecure-Requests": "1"
            }
            self.proxies = {}  # Dictionary to store proxies
            self.working_proxies = []  # List of working proxies
            self.fast_proxies = []  # List of proxies meeting speed threshold
            self.rotating_proxy = None  # Rotating proxy instance
            self.last_test_time = 0
            self.test_interval = 300  # Test every 5 minutes
            self.current_proxy_index = 0  # Add rotation counter
            self.speed_threshold = 1000  # Speed threshold in ms (1 second)
            self.max_fast_proxies = 5  # Maximum number of fast proxies to maintain
            ProxyManager._initialized = True

    async def initialize(self, rotating_proxy: Optional[Dict] = None, proxy_list: Optional[List[Dict]] = None) -> None:
        """Initialize the proxy manager by testing all proxies."""
        logger.info("Initializing proxy manager...")
        
        # Reset proxy lists
        self.working_proxies = []
        self.fast_proxies = []
        
        # Set up rotating proxy if provided
        if rotating_proxy:
            logger.info("Setting up rotating proxy...")
            try:
                self.set_rotating_proxy(
                    domain=rotating_proxy["domain"],
                    port=rotating_proxy["port"],
                    username=rotating_proxy["username"],
                    password=rotating_proxy["password"]
                )
                logger.info("Rotating proxy configured successfully")
            except Exception as e:
                logger.error(f"Error setting up rotating proxy: {str(e)}")

        # Add proxy list if provided
        if proxy_list:
            logger.info(f"Adding {len(proxy_list)} proxies to the pool...")
            try:
                self.add_proxies_from_list(proxy_list)
                logger.info(f"Successfully added {len(self.proxies)} proxies to the pool")
            except Exception as e:
                logger.error(f"Error adding proxies from list: {str(e)}")
        
        # Test all proxies
        if self.proxies or self.rotating_proxy:
            await self.test_all_proxies()
            
            if not self.working_proxies and not (self.rotating_proxy and self.rotating_proxy.is_working):
                logger.warning("No working proxies found during initialization!")
            else:
                working_count = len(self.working_proxies)
                fast_count = len(self.fast_proxies)
                logger.info(f"Initialization complete. Found {working_count} working proxies, {fast_count} fast proxies.")
                if self.rotating_proxy and self.rotating_proxy.is_working:
                    logger.info("Rotating proxy is operational.")
        else:
            logger.warning("No proxies provided during initialization!")

    def add_proxy(self, proxy: ProxyInfo) -> None:
        """Add a proxy to the manager"""
        if isinstance(proxy, RotatingProxyInfo):
            self.rotating_proxy = proxy
            return
            
        key = f"{proxy.protocol}://{proxy.host}:{proxy.port}"
        self.proxies[key] = proxy

    def set_rotating_proxy(self, domain: str, port: int, username: str, password: str) -> None:
        """Set up a rotating proxy"""
        self.rotating_proxy = RotatingProxyInfo(domain, port, username, password)
        
    def add_proxies_from_list(self, proxy_list: List[Dict]) -> None:
        """Add multiple proxies from a list of dictionaries"""
        for proxy_data in proxy_list:
            proxy = ProxyInfo(
                host=proxy_data.get('host'),
                port=int(proxy_data.get('port')),
                protocol=proxy_data.get('protocol', 'http'),
                username=proxy_data.get('username'),
                password=proxy_data.get('password'),
                country=proxy_data.get('country'),
                anonymity=proxy_data.get('anonymity'),
                speed=proxy_data.get('speed')
            )
            self.add_proxy(proxy)

    async def test_proxy(self, proxy: ProxyInfo) -> bool:
        """Test if a proxy is working."""
        try:
            if proxy.username and proxy.password:
                auth = aiohttp.BasicAuth(proxy.username, proxy.password)
            else:
                auth = None
                
            proxy_url = self.get_proxy_url(proxy)
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(connector=connector, auth=auth) as session:
                try:
                    async with session.get(
                        self.test_url,
                        proxy=proxy_url,
                        headers=self.headers,
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            proxy.is_working = True
                            proxy.last_checked = time.time()
                            if proxy not in self.working_proxies:
                                self.working_proxies.append(proxy)
                            return True
                except Exception as e:
                    logger.error(f"Error testing proxy {proxy_url}: {str(e)}")
                    
            proxy.is_working = False
            if proxy in self.working_proxies:
                self.working_proxies.remove(proxy)
            return False
            
        except Exception as e:
            logger.error(f"Error in test_proxy: {str(e)}")
            proxy.is_working = False
            if proxy in self.working_proxies:
                self.working_proxies.remove(proxy)
            return False

    async def test_all_proxies(self) -> None:
        """Test all proxies and update working/fast lists."""
        logger.info("Testing all proxies...")
        tasks = []
        
        # Test rotating proxy first if available
        if self.rotating_proxy:
            logger.info("Testing rotating proxy...")
            tasks.append(self.test_proxy(self.rotating_proxy))
            
        # Test all regular proxies
        for proxy in self.proxies.values():
            if not proxy.is_rotating:  # Skip rotating proxy as it's tested above
                tasks.append(self.test_proxy(proxy))
                
        # Wait for all tests to complete
        if tasks:
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                working_count = sum(1 for r in results if r is True)
                logger.info(f"Proxy testing completed. {working_count}/{len(tasks)} proxies working")
                
                # Update fast proxies list
                self.fast_proxies = sorted(
                    [p for p in self.working_proxies if p.speed is not None],
                    key=lambda x: x.speed
                )[:self.max_fast_proxies]
                
                if self.fast_proxies:
                    logger.info(f"Found {len(self.fast_proxies)} fast proxies")
                else:
                    logger.warning("No fast proxies found")
            except Exception as e:
                logger.error(f"Error during proxy testing: {str(e)}")
        else:
            logger.warning("No proxies available to test!")

    async def load_proxies(self) -> None:
        """Load proxies from file if available."""
        try:
            if os.path.exists(self.proxy_file):
                with open(self.proxy_file, 'r') as f:
                    proxy_list = json.load(f)
                    
                for proxy_data in proxy_list:
                    proxy = ProxyInfo(
                        host=proxy_data['host'],
                        port=proxy_data['port'],
                        username=proxy_data.get('username'),
                        password=proxy_data.get('password'),
                        is_rotating=proxy_data.get('is_rotating', False)
                    )
                    if proxy.is_rotating:
                        self.rotating_proxy = proxy
                    self.proxies.append(proxy)
                    
                logger.info(f"Loaded {len(self.proxies)} proxies from {self.proxy_file}")
            else:
                logger.warning(f"Proxy file {self.proxy_file} not found")
        except Exception as e:
            logger.error(f"Error loading proxies: {str(e)}")

    async def get_next_proxy(self) -> Optional[ProxyInfo]:
        """Get the next working proxy using round-robin."""
        if not self.working_proxies:
            logger.warning("No working proxies found, attempting to retest all proxies...")
            await self.test_all_proxies()
            if not self.working_proxies:
                return None

        # Try to get a rotating proxy first
        if self.rotating_proxy and self.rotating_proxy.is_working:
            return self.rotating_proxy

        # If no rotating proxy, use round-robin on working proxies
        if self.working_proxies:
            next_proxy = self.working_proxies[0]
            # Move used proxy to the end of the list
            self.working_proxies.append(self.working_proxies.pop(0))
            
            # Check if proxy was tested recently (within last 5 minutes)
            if next_proxy.last_checked and time.time() - next_proxy.last_checked > 300:
                logger.info(f"Testing proxy that hasn't been checked recently: {self.get_proxy_url(next_proxy)}")
                is_working = await self.test_proxy(next_proxy)
                if not is_working:
                    return await self.get_next_proxy()  # Recursively try next proxy
                
            return next_proxy
            
        logger.error("No working proxies available")
        return None

    def get_random_working_proxy(self) -> Optional[ProxyInfo]:
        """Get a random working proxy, prioritizing rotating proxy if available"""
        if not self._initialized:
            logger.warning("ProxyManager not initialized! Call initialize() first.")
            return None
            
        if self.rotating_proxy and self.rotating_proxy.is_working:
            return self.rotating_proxy
            
        if not self.working_proxies:
            return None
        return random.choice(self.working_proxies)

    def get_fastest_proxy(self) -> Optional[ProxyInfo]:
        """Get the fastest working proxy."""
        if not self.working_proxies:
            return None
            
        # Sort working proxies by speed
        sorted_proxies = sorted(
            [p for p in self.working_proxies if p.speed is not None],
            key=lambda x: x.speed
        )
        
        return sorted_proxies[0] if sorted_proxies else self.get_next_proxy()

    def get_proxy_url(self, proxy: ProxyInfo) -> str:
        """Get the proxy URL in the format protocol://username:password@host:port"""
        if proxy.username and proxy.password:
            return f"{proxy.protocol}://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
        return f"{proxy.protocol}://{proxy.host}:{proxy.port}"

    async def retry_with_another_proxy(
        self, 
        request_func, 
        max_retries: int = 3,
        prefer_fast: bool = True
    ) -> Any:
        """Retry a request with different proxies until success or max retries reached."""
        attempts = 0
        errors = []
        
        while attempts < max_retries:
            proxy = self.get_fastest_proxy() if prefer_fast else self.get_next_proxy()
            if not proxy:
                logger.warning(f"No {'fast' if prefer_fast else 'working'} proxy available, retesting proxies...")
                await self.test_all_proxies()
                proxy = self.get_fastest_proxy() if prefer_fast else self.get_next_proxy()
                if not proxy:
                    attempts += 1
                    continue

            try:
                proxy_url = self.get_proxy_url(proxy)
                result = await request_func(proxy_url)
                if result:
                    return result
            except Exception as e:
                logger.error(f"Request failed with proxy {self.get_proxy_url(proxy)}: {str(e)}")
                errors.append(str(e))
                # Mark proxy as not working and remove from working list
                proxy.is_working = False
                if proxy in self.working_proxies:
                    self.working_proxies.remove(proxy)
            
            attempts += 1
        
        error_msg = f"All proxy attempts failed after {max_retries} retries. Errors: {', '.join(errors)}"
        logger.error(error_msg)
        raise Exception("No working proxies available")