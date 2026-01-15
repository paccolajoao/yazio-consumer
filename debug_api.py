
import logging
import sys
import json
from pathlib import Path
from datetime import date

# Add root to path
sys.path.append(str(Path(__file__).parent.parent))

from infrastructure.api.yazio_client import YazioClient
from infrastructure.services.auth_service import AuthService
from domain.models import AuthToken

# Configure logging
logging.basicConfig(level=logging.INFO)

def debug_response():
    # Setup client
    client = YazioClient()
    auth = AuthService(client)

    # Load token from .env or manual input (assuming user has logged in via UI and .env is populated)
    from dotenv import load_dotenv
    import os
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)

    access = os.getenv("YAZIO_ACCESS_TOKEN")
    if not access:
        print("❌ No access token found in .env. Please login using the UI first.")
        return

    token = AuthToken(access_token=access)

    # Fetch today or yesterday
    d = date.today()
    print(f"Fetching data for {d}...")

    # We call the internal session directly to see raw json,
    # as get_days_data processes it.
    client.session.headers["Authorization"] = f"Bearer {token.access_token}"
    url = f"{client.BASE_URL}/v9/user/consumed-items"
    params = {"date": d.strftime("%Y-%m-%d")}

    resp = client.session.get(url, params=params)
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Response received.")
        print("Structure keys:", data.keys() if isinstance(data, dict) else "List")

        items = []
        if isinstance(data, list): items = data
        elif isinstance(data, dict):
            items.extend(data.get("products", []))
            items.extend(data.get("simple_products", []))

        print(f"Found {len(items)} items.")
        if items:
            print("--- SAMPLE ITEM 0 ---")
            print(json.dumps(items[0], indent=2))
        else:
            print("No items found today. Try adding something to Yazio for today.")

    else:
        print(f"❌ Failed: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    debug_response()
