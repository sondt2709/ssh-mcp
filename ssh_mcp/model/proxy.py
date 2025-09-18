from pydantic import BaseModel


class ProxyConfig(BaseModel):
    host: str
    port: int = 1080
    username: str | None = None
    password: str | None = None
