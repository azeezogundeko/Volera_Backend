from .base import LLMIntegration
from db.cache.dict import DiskCacheDB


class ShopInverseIntegration(LLMIntegration):
    def __init__(self, db_manager: DiskCacheDB =None):
        super().__init__(
            name="shopinverse", 
            base_url="https://www.shopinverse.com", 
            url_patterns=["shopinverse.com"], 
            db_manager=db_manager
            )
        
class KongaIntegration(LLMIntegration):
    def __init__(self, db_manager: DiskCacheDB =None):
        super().__init__(
            name="konga", 
            base_url="https://www.konga.com", 
            url_patterns=["konga.com"], 
            db_manager=db_manager
            )

class SuperMartIntegration(LLMIntegration):
    def __init__(self, db_manager: DiskCacheDB =None):
        super().__init__(
            name="supermart", 
            base_url="https://www.supermart.ng", 
            url_patterns=["supermart.ng"], 
            db_manager=db_manager
            )
        
class SlotIntegration(LLMIntegration):
    def __init__(self, db_manager: DiskCacheDB =None):
        super().__init__(
            name="slot", 
            base_url="https://www.slot.ng", 
            url_patterns=["slot.ng"], 
            db_manager=db_manager
            )
        
class KaraIntegration(LLMIntegration):
    def __init__(self, db_manager: DiskCacheDB =None):
        super().__init__(
            name="kara", 
            base_url="https://www.kara.com.ng", 
            url_patterns=["kara.com.ng"], 
            db_manager=db_manager
            )
        
class ParkwayIntegration(LLMIntegration):
    def __init__(self, db_manager: DiskCacheDB =None):
        super().__init__(
            name="parkwaynigeria", 
            base_url="https://www.parkwaynigeria.com", 
            url_patterns=["parkwaynigeria.com"], 
            db_manager=db_manager
            )
 