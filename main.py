from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import jwt
import time
import uuid

EMAIL = "23f3001847@ds.study.iitm.ac.in"

ALLOWED_ORIGIN = "https://dash-mloyn2.example.com"

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""

ISSUER = "https://idp.exam.local"
AUDIENCE = "tds-ke1ilxr7.apps.exam.local"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = str(uuid.uuid4())
        response.headers["X-Process-Time"] = f"{time.perf_counter()-start:.6f}"
        return response

app.add_middleware(MetricsMiddleware)

@app.get("/stats")
async def stats(values: str = Query(...)):
    nums = [int(x.strip()) for x in values.split(",") if x.strip()]
    return {
        "email": EMAIL,
        "count": len(nums),
        "sum": sum(nums),
        "min": min(nums),
        "max": max(nums),
        "mean": sum(nums) / len(nums),
    }

class TokenRequest(BaseModel):
    token: str

@app.post("/verify")
def verify(request: TokenRequest):
    try:
        payload = jwt.decode(
            request.token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
        )

        return {
            "valid": True,
            "email": payload.get("email"),
            "sub": payload.get("sub"),
            "aud": payload.get("aud"),
        }

    except jwt.PyJWTError:
        return JSONResponse(
            status_code=401,
            content={"valid": False},
        )

import os

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

YAML_CONFIG = {
    "workers": 2
}

DOTENV_CONFIG = {
    "port": 8604,
    "log_level": "error",
    "api_key": "key-vv3kxadk5y",
}

def to_bool(value):
    return str(value).lower() in ("true", "1", "yes", "on")

@app.get("/effective-config")
async def effective_config(set: list[str] = Query(default=[])):
    config = DEFAULTS.copy()

    config.update(YAML_CONFIG)
    config.update(DOTENV_CONFIG)

    # OS environment variables (APP_* prefix)
    env_map = {
        "APP_PORT": "port",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
        "APP_DEBUG": "debug",
        "APP_WORKERS": "workers",
        "NUM_WORKERS": "workers",
    }

    for env_key, cfg_key in env_map.items():
        if env_key in os.environ:
            config[cfg_key] = os.environ[env_key]

    # CLI overrides
    for item in set:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        config[key] = value

    config["port"] = int(config["port"])
    config["workers"] = int(config["workers"])
    config["debug"] = to_bool(config["debug"])
    config["log_level"] = str(config["log_level"])

    # Never expose the API key
    config["api_key"] = "****"

    return config