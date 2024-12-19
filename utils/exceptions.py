class AgentInintilaztionError(Exception):
    def __init__(self, message):
        super().__init__(message)

class AgentProcessingError(Exception):
    def __init__(self, message):
        super().__init__(message)
        
class WebSocketProcessingError(Exception):
    def __init__(self, message):
        super().__init__(message)