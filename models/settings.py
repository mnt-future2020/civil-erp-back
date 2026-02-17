from pydantic import BaseModel
from typing import Optional


class GSTCredentialsCreate(BaseModel):
    gstin: str
    username: str
    password: str
    client_id: str
    client_secret: str
    nic_url: str = "https://einv-apisandbox.nic.in"
    is_sandbox: bool = True


class GSTCredentialsResponse(BaseModel):
    gstin: str
    username: str
    client_id: str
    nic_url: str
    is_sandbox: bool
    is_configured: bool = True
    last_updated: Optional[str] = None


class CloudinaryCredentials(BaseModel):
    cloud_name: str
    api_key: str
    api_secret: str


class SMTPCredentials(BaseModel):
    host: str
    port: int = 587
    username: str
    password: str  # "___unchanged___" sentinel to keep existing
    from_email: str
    from_name: str = "Civil ERP"
    use_tls: bool = True


class SMTPCredentialsResponse(BaseModel):
    host: str
    port: int
    username: str
    from_email: str
    from_name: str
    use_tls: bool
    is_configured: bool = True
    last_updated: Optional[str] = None
