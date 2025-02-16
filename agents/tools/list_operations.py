from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
import time
import asyncio
from datetime import datetime, timedelta

class Specification(BaseModel):
    label: str 
    value: str 

class ProductDetail(BaseModel):
    product_id: str = ''
    name: str = ''
    brand: str = ''
    category: str = ''
    currency: str = '₦'
    description: str = ''
    current_price: float = 0.0
    original_price: float  = 0.0
    discount: float = 0.0
    url: str = ''
    image: str = ''
    source: str = Field(None, description='The source of the product eg Amazon, Jumia, Konga, etc')
    rating: float = 0.0
    rating_count: int  = 0
    specifications: List[Specification] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)

class ListOperationResponse(BaseModel):
    """Response model for list operations"""
    success: bool = Field(default=False)
    message: str = Field(default='')
    data: List[ProductDetail] = Field(default_factory=list)
    count: int = Field(default=0)

class ListTools:
    """Tools for list operations that can be used by AI agents"""
    
    def __init__(self, ttl_minutes: int = 5):
        self._lists: Dict[str, List[Any]] = {}
        self._timestamps: Dict[str, float] = {}  # Track creation time of lists
        self.ttl_seconds = ttl_minutes * 60
        self._cleanup_task = None
        
    async def initialize(self):
        """Initialize the ListTools instance asynchronously"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        return self

    @classmethod
    async def create(cls, ttl_minutes: int = 5):
        """Factory method to create and initialize a ListTools instance"""
        instance = cls(ttl_minutes)
        return await instance.initialize()
    
    async def _cleanup_loop(self):
        """Background task to periodically cleanup expired lists"""
        while True:
            self._cleanup_expired_lists()
            await asyncio.sleep(60)  # Check every minute
    
    def _cleanup_expired_lists(self):
        """Remove lists that have exceeded their TTL"""
        current_time = time.time()
        expired_lists = [
            list_name for list_name, timestamp in self._timestamps.items()
            if current_time - timestamp > self.ttl_seconds
        ]
        
        for list_name in expired_lists:
            self._lists.pop(list_name, None)
            self._timestamps.pop(list_name, None)

    def save_to_list(self, list_name: str, items: List[ProductDetail], unique: bool = False) -> Dict:
        """
        Save items to a specified list.
        
        Args:
            list_name: Name of the list to save to
            items: List of items to save
            unique: If True, only add items that don't exist
            
        Returns:
            Dict containing operation status and details
        """
        try:
            # Validate list name
            if not list_name or not isinstance(list_name, str):
                return ListOperationResponse(
                    success=False,
                    message="Invalid list name provided",
                    data=[]
                ).dict()
                
            # Validate items
            if not isinstance(items, list):
                items = [items]  # Convert single item to list
                
            # Validate that all items are ProductDetail instances
            try:
                validated_items = []
                for item in items:
                    if isinstance(item, dict):
                        validated_items.append(ProductDetail(**item))
                    elif isinstance(item, ProductDetail):
                        validated_items.append(item)
                    else:
                        raise ValueError(f"Invalid item type: {type(item)}")
                items = validated_items
            except Exception as e:
                return ListOperationResponse(
                    success=False,
                    message=f"Invalid item format: {str(e)}",
                    data=[]
                ).dict()
            
            # Create list if it doesn't exist or update timestamp if it does
            if list_name not in self._lists:
                self._lists[list_name] = []
                self._timestamps[list_name] = time.time()
            else:
                # Refresh timestamp on modification
                self._timestamps[list_name] = time.time()
            
            # Handle unique items if required
            if unique:
                items_to_add = [item for item in items if item not in self._lists[list_name]]
                if not items_to_add:
                    return ListOperationResponse(
                        success=False,
                        message=f"All items already exist in list '{list_name}'",
                        data=items
                    ).dict()
                items = items_to_add
            
            # Add items to list
            self._lists[list_name].extend(items)
            print(f"Items added to list '{list_name}': {items}")
            
            # Calculate time remaining before expiry
            time_remaining = int(self.ttl_seconds - (time.time() - self._timestamps[list_name]))
            
            return ListOperationResponse(
                success=True,
                message=f"Items successfully added to list '{list_name}'. List expires in {time_remaining} seconds",
                data=items,
                count=len(self._lists[list_name])
            ).dict()
            
        except Exception as e:
            return ListOperationResponse(
                success=False,
                message=f"Error saving items to list: {str(e)}",
                data=[]
            ).dict()

    def get_from_list(self, list_name: str, index: int = None) -> Dict:
        """
        Get item(s) from a specified list.
        
        Args:
            list_name: Name of the list to get from
            index: Optional index to get specific item. If None, returns entire list
            
        Returns:
            Dict containing operation status and retrieved item(s)
        """
        try:
            # Check if list exists
            if list_name not in self._lists:
                return ListOperationResponse(
                    success=False,
                    message=f"List '{list_name}' does not exist",
                ).dict()
            
            # Calculate time remaining
            time_remaining = int(self.ttl_seconds - (time.time() - self._timestamps[list_name]))
            
            # Get specific item if index provided
            if index is not None:
                if 0 <= index < len(self._lists[list_name]):
                    item = self._lists[list_name][index]
                    return ListOperationResponse(
                        success=True,
                        message=f"Successfully retrieved item at index {index}. List expires in {time_remaining} seconds",
                        data=item
                    ).dict()
                else:
                    return ListOperationResponse(
                        success=False,
                        message=f"Index {index} out of range for list '{list_name}'"
                    ).dict()
            
            # Return entire list if no index specified
            print(f"Items in list '{list_name}': {self._lists[list_name]}")
            return ListOperationResponse(
                success=True,
                message=f"Successfully retrieved all items from list '{list_name}'. List expires in {time_remaining} seconds",
                data=self._lists[list_name],
                count=len(self._lists[list_name])
            ).dict()
            
        except Exception as e:
            return ListOperationResponse(
                success=False,
                message=f"Error retrieving from list: {str(e)}"
            ).dict()

    def count_items(self, list_name: str, item: ProductDetail = None) -> Dict:
        """
        Count items in a specified list.
        
        Args:
            list_name: Name of the list to count from
            item: Optional specific item to count occurrences of
            
        Returns:
            Dict containing operation status and count
        """
        try:
            # Check if list exists
            if list_name not in self._lists:
                return ListOperationResponse(
                    success=False,
                    message=f"List '{list_name}' does not exist",
                    count=0
                ).dict()
            
            # Count specific item if provided
            if item is not None:
                count = self._lists[list_name].count(item)
                return ListOperationResponse(
                    success=True,
                    message=f"Found {count} occurrence(s) of item in list '{list_name}'",
                    data=item,
                    count=count
                ).dict()
            
            # Count all items if no specific item provided
            count = len(self._lists[list_name])
            print(f"Total items in list '{list_name}': {count}")
            return ListOperationResponse(
                success=True,
                message=f"Total items in list '{list_name}'",
                count=count
            ).dict()
            
        except Exception as e:
            return ListOperationResponse(
                success=False,
                message=f"Error counting items: {str(e)}",
                count=0
            ).dict()

    def remove_from_list(self, list_name: str, item: ProductDetail = None, index: int = None) -> Dict:
        """
        Remove an item from a specified list by value or index.
        
        Args:
            list_name: Name of the list to remove from
            item: Item to remove by value (if provided)
            index: Index of item to remove (if item not provided)
            
        Returns:
            Dict containing operation status and details
        """
        try:
            # Check if list exists
            if list_name not in self._lists:
                return ListOperationResponse(
                    success=False,
                    message=f"List '{list_name}' does not exist"
                ).dict()
            
            # Remove by index if provided and item not provided
            if item is None and index is not None:
                if 0 <= index < len(self._lists[list_name]):
                    removed_item = self._lists[list_name].pop(index)
                    return ListOperationResponse(
                        success=True,
                        message=f"Successfully removed item at index {index}",
                        data=removed_item,
                        count=len(self._lists[list_name])
                    ).dict()
                else:
                    return ListOperationResponse(
                        success=False,
                        message=f"Index {index} out of range for list '{list_name}'"
                    ).dict()
            
            # Remove by value if item provided
            if item is not None:
                try:
                    self._lists[list_name].remove(item)
                    return ListOperationResponse(
                        success=True,
                        message=f"Successfully removed item from list '{list_name}'",
                        data=item,
                        count=len(self._lists[list_name])
                    ).dict()
                except ValueError:
                    return ListOperationResponse(
                        success=False,
                        message=f"Item not found in list '{list_name}'",
                        data=item
                    ).dict()
            
            print(f"Items in list '{list_name}': {self._lists[list_name]}")
            return ListOperationResponse(
                success=False,
                message="Either item or index must be provided"
            ).dict()
            
        except Exception as e:
            return ListOperationResponse(
                success=False,
                message=f"Error removing item from list: {str(e)}"
            ).dict()

    def clear_list(self, list_name: str) -> Dict:
        """
        Clear all items from a specified list.
        
        Args:
            list_name: Name of the list to clear
            
        Returns:
            Dict containing operation status
        """
        try:
            # Check if list exists
            if list_name not in self._lists:
                return ListOperationResponse(
                    success=False,
                    message=f"List '{list_name}' does not exist"
                ).dict()
            
            # Store the count before clearing
            previous_count = len(self._lists[list_name])
            
            # Clear the list
            self._lists[list_name].clear()
            
            return ListOperationResponse(
                success=True,
                message=f"Successfully cleared list '{list_name}'",
                count=0,
                data={"previous_count": previous_count}
            ).dict()
            
        except Exception as e:
            return ListOperationResponse(
                success=False,
                message=f"Error clearing list: {str(e)}"
            ).dict()

    def get_ttl_info(self, list_name: str) -> Dict:
        """
        Get TTL information for a specified list.
        
        Args:
            list_name: Name of the list to get TTL info for
            
        Returns:
            Dict containing TTL information
        """
        try:
            if list_name not in self._timestamps:
                return ListOperationResponse(
                    success=False,
                    message=f"List '{list_name}' does not exist"
                ).dict()
            
            current_time = time.time()
            creation_time = self._timestamps[list_name]
            time_remaining = int(self.ttl_seconds - (current_time - creation_time))
            
            return ListOperationResponse(
                success=True,
                message=f"TTL information for list '{list_name}'",
                data={
                    "created_at": datetime.fromtimestamp(creation_time).isoformat(),
                    "expires_at": datetime.fromtimestamp(creation_time + self.ttl_seconds).isoformat(),
                    "time_remaining_seconds": time_remaining
                }
            ).dict()
            
        except Exception as e:
            return ListOperationResponse(
                success=False,
                message=f"Error getting TTL info: {str(e)}"
            ).dict()

    def __del__(self):
        """Cleanup when the instance is destroyed"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()

# Example usage:
"""
list_tools = ListTools()

# Save items
result = list_tools.save_to_list("lenovo_laptops", {"item": "laptop", "price": 999})
print(result)  # {'success': True, 'message': 'Item successfully added...', 'data': {...}, 'count': 1}

# Remove item by value
result = list_tools.remove_from_list("lenovo_laptops", item={"item": "laptop", "price": 999})
print(result)  # {'success': True, 'message': 'Successfully removed item...', 'data': {...}, 'count': 0}

# Remove item by index
result = list_tools.remove_from_list("lenovo_laptops", index=0)
print(result)  # {'success': True, 'message': 'Successfully removed item at index 0...', 'data': {...}, 'count': 0}

# Clear list
result = list_tools.clear_list("lenovo_laptops")
print(result)  # {'success': True, 'message': 'Successfully cleared list...', 'count': 0, 'data': {'previous_count': 1}}
""" 