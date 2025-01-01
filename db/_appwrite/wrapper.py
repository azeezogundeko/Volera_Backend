import asyncio
from concurrent.futures import ThreadPoolExecutor
from .base import AsyncAppWriteClient
from appwrite.services.users import Users

class AsyncUsersWrapper(Users):
    def __init__(self, client=None):
        self.client = client or AsyncAppWriteClient().client
        super().__init__(self.client)
        self._executor = ThreadPoolExecutor(max_workers=10)

    def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(self._executor, func, *args, **kwargs)

    def __getattr__(self, name):
        # Access the method from the parent Users class
        print(f"Trying to access: {name}")
        try:
            sync_method = getattr(super(), name)  # Accessing method of the parent Users class
            if callable(sync_method):
                # Wrap the method as an async method
                async def async_method(*args, **kwargs):
                    print(f"Calling {name} asynchronously")
                    return await self._run_in_executor(sync_method, *args, **kwargs)
                return async_method
            else:
                return sync_method  # if it's not callable, return it as is
        except AttributeError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __dir__(self):
        # List both client methods and wrapper methods
        return dir(self.client) + dir(self)

    def close(self):
        self._executor.shutdown(wait=True)

    def __del__(self):
        self.close()

user_db = AsyncUsersWrapper()