import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

try:
    print("Importing main...")
    import main
    print("Importing infrastructure...")
    from infrastructure.api.yazio_client import YazioClient
    from infrastructure.services.auth_service import AuthService
    from infrastructure.exporters.csv_exporter import CsvExporter
    from infrastructure.services.google_oauth_service import GoogleOAuthService
    print("Importing application...")
    from application.use_cases import LoginUseCase, ExportDataUseCase
    print("Importing domain...")
    from domain.models import DayLog
    print("Importing ui...")
    from ui.main_window import YazioExporterApp
    print("✅ All imports successful!")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
