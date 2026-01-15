import os
import logging
from typing import Optional, Dict
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

class GoogleOAuthService:
    SCOPES = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]

    def __init__(self, credentials_path: str, token_path: str = "token.json"):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds: Optional[Credentials] = None
        self.logger = logging.getLogger(__name__)

    def authenticate(self, force_new: bool = False, interactive: bool = True) -> Dict[str, str]:
        """
        Authenticate with Google (Desktop flow).
        Args:
            force_new: Ignore existing token.
            interactive: If True, launch browser for login if needed. If False, return empty if not logged in.
        Returns dict with access_token and id_token.
        """
        if not force_new and os.path.exists(self.token_path):
            try:
                self.creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
            except Exception as e:
                self.logger.warning(f"Error loading tokens: {e}")

        if self.creds and self.creds.valid:
            return self._get_tokens_dict()

        if self.creds and self.creds.expired and self.creds.refresh_token:
            try:
                self.creds.refresh(Request())
                self._save_credentials()
                return self._get_tokens_dict()
            except Exception:
                pass

        if not interactive:
            return {}

        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"Google credentials not found at {self.credentials_path}")

        flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
        self.creds = flow.run_local_server(port=8080)
        self._save_credentials()
        return self._get_tokens_dict()

    def _save_credentials(self):
        if self.creds:
            with open(self.token_path, 'w') as token:
                token.write(self.creds.to_json())

    def _get_tokens_dict(self) -> Dict[str, str]:
        if not self.creds: return {}
        return {
            "access_token": self.creds.token,
            "id_token": getattr(self.creds, "id_token", None)
        }
