from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import date
from .models import DayLog, AuthToken

class IAuthService(ABC):
    @abstractmethod
    def login(self, email: str, password: str) -> AuthToken:
        """Authenticates with username/password."""
        pass

    @abstractmethod
    def login_with_google(self, id_token: str, access_token: str) -> AuthToken:
        """Authenticates with Google tokens."""
        pass

class IYazioClient(ABC):
    @abstractmethod
    def get_days_data(self, token: AuthToken, start_date: date, end_date: date) -> List[DayLog]:
        """Fetches consumption data for a date range."""
        pass

    @abstractmethod
    def get_user_profile(self, token: AuthToken) -> Dict[str, Any]:
        """Fetches user profile information."""
        pass

class IExporter(ABC):
    @abstractmethod
    def export(self, data: List[DayLog], output_dir: str) -> List[str]:
        """Exports data to the specified format. Returns list of created file paths."""
        pass
