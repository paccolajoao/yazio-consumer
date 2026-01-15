from datetime import date
from typing import List, Dict, Any, Optional
from domain.interfaces import IAuthService, IYazioClient, IExporter
from domain.models import AuthToken, DayLog

class LoginUseCase:
    def __init__(self, auth_service: IAuthService):
        self.auth_service = auth_service

    def execute_password_login(self, email: str, password: str) -> AuthToken:
        return self.auth_service.login(email, password)

    def execute_google_login(self, id_token: str, access_token: str) -> AuthToken:
        return self.auth_service.login_with_google(id_token, access_token)

class ExportDataUseCase:
    def __init__(self, yazio_client: IYazioClient, exporter: IExporter):
        self.client = yazio_client
        self.exporter = exporter

    def execute(self, token: AuthToken, start_date: date, end_date: date, output_dir: str) -> List[str]:
        # 1. Fetch data
        print(f"Fetching data from {start_date} to {end_date}...")
        data = self.client.get_days_data(token, start_date, end_date)

        if not data:
            print("No data found for the given period.")
            return []

        # 2. Export data
        print(f"Exporting {len(data)} days of data...")
        created_files = self.exporter.export(data, output_dir)

        return created_files
