from domain.interfaces import IAuthService
from domain.models import AuthToken
from domain.interfaces import IAuthService
from domain.models import AuthToken
from infrastructure.api.yazio_client import YazioClient

class AuthService(IAuthService):
    def __init__(self, client: YazioClient):
        self.client = client

    def login(self, email: str, password: str) -> AuthToken:
        data = self.client.login_password(email, password)
        return self._parse_token(data)

    def login_with_google(self, id_token: str, access_token: str) -> AuthToken:
        data = self.client.exchange_google_token(id_token, access_token)
        return self._parse_token(data)

    def _parse_token(self, data: dict) -> AuthToken:
        return AuthToken(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", ""),
            expires_at=None # Could parse expiry if needed
        )
