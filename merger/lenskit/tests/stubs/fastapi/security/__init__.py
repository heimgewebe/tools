from typing import Optional


class HTTPAuthorizationCredentials:
    def __init__(self, scheme: Optional[str] = None, credentials: Optional[str] = None):
        self.scheme = scheme
        self.credentials = credentials

class HTTPBearer:
    def __init__(self, auto_error: bool = True):
        self.auto_error = auto_error

    def __call__(self, request=None):
        token = None
        if request and request.headers:
            auth = request.headers.get("Authorization") or ""
            if auth.lower().startswith("bearer "):
                token = auth.split(" ", 1)[1]
        if token:
            return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        if self.auto_error:
            from fastapi.exceptions import HTTPException
            raise HTTPException(status_code=403, detail="Not authenticated")
        return None
