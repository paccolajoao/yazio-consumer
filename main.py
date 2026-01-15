import sys
import logging
import tkinter as tk
from pathlib import Path

# Infrastructure
from infrastructure.api.yazio_client import YazioClient
from infrastructure.services.auth_service import AuthService
from infrastructure.services.google_oauth_service import GoogleOAuthService
from infrastructure.exporters.csv_exporter import CsvExporter

# Application
from application.use_cases import LoginUseCase, ExportDataUseCase

# Presentation
from ui.main_window import YazioExporterApp

def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Root path
    if hasattr(sys, '_MEIPASS'):
        app_dir = Path(sys._MEIPASS)
    else:
        app_dir = Path(__file__).parent

    # 1. Infrastructure Setup
    yazio_client = YazioClient()
    auth_service = AuthService(yazio_client)
    google_service = GoogleOAuthService(
        credentials_path=str(app_dir / "google" / "credentials.json"),
        token_path=str(app_dir / "google" / "token.json")
    )
    exporter = CsvExporter()

    # 2. Application Setup (Use Cases)
    login_use_case = LoginUseCase(auth_service)
    export_use_case = ExportDataUseCase(yazio_client, exporter)

    # 3. Presentation Setup
    root = tk.Tk()
    app = YazioExporterApp(
        root=root,
        login_use_case=login_use_case,
        export_use_case=export_use_case,
        google_auth_service=google_service,
        app_dir=app_dir
    )

    # Start
    root.mainloop()

if __name__ == "__main__":
    main()
