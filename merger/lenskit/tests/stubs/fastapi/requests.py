class Request:
    def __init__(self, headers=None):
        self.headers = headers or {}

    async def is_disconnected(self):
        return False
