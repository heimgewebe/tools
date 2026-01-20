from fastapi import HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from ..adapters.security import get_security_config

security_scheme = HTTPBearer(auto_error=False)

def verify_token(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    token: Optional[str] = Query(None)
):
    config = get_security_config()
    if not config.token:
        return

    if creds and creds.credentials == config.token:
        return

    if token and token == config.token:
        return

    raise HTTPException(status_code=401, detail="Missing or invalid authentication token")
