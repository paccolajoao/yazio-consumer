import concurrent.futures
import logging
import requests
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional
from domain.interfaces import IYazioClient
from domain.models import AuthToken, DayLog, ConsumedItem, Product, Nutrients

class YazioClient(IYazioClient):
    BASE_URL = "https://yzapi.yazio.com"
    TIMEOUT = 30

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Yazio/Android"
        })

    def login_password(self, email: str, password: str) -> Dict[str, Any]:
        """Performs password login and returns raw token data."""
        url = f"{self.BASE_URL}/v9/oauth/token"

        # Credentials known from Yazio Exporter
        CLIENT_ID = "1_4hiybetvfksgw40o0sog4s884kwc840wwso8go4k8c04goo4c"
        CLIENT_SECRET = "6rok2m65xuskgkgogw40wkkk8sw0osg84s8cggsc4woos4s8o"

        payload = {
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "username": email,
            "password": password
        }

        response = self.session.post(url, json=payload, timeout=self.TIMEOUT)
        response.raise_for_status()
        return response.json()

    def exchange_google_token(self, id_token: str, access_token: str) -> Dict[str, Any]:
        """Exchanges Google tokens for Yazio tokens."""
        endpoints = [
            "/v11/user/login/google",
            "/v11/user/login/social",
            "/v11/user/login-google",
            "/v11/auth/google",
            "/v11/oauth/google",
        ]

        payloads = []
        if id_token:
            payloads.extend([
                {"id_token": id_token},
                {"token": id_token},
                {"google_token": id_token},
                {"credential": id_token},
            ])
        if access_token:
            payloads.extend([
                {"access_token": access_token},
                {"token": access_token},
            ])

        last_error = None
        for endpoint in endpoints:
            url = f"{self.BASE_URL}{endpoint}"
            for payload in payloads:
                try:
                    self.logger.debug(f"Trying {endpoint}...")
                    response = self.session.post(url, json=payload, timeout=self.TIMEOUT)
                    if response.status_code == 200:
                        data = response.json()
                        if "access_token" in data:
                            self.logger.info(f"Authenticated via {endpoint}")
                            return data

                    if response.status_code != 404:
                         last_error = f"{endpoint}: {response.status_code} - {response.text[:100]}"
                except Exception as e:
                    last_error = f"{endpoint}: {e}"
                    continue

        raise RuntimeError(f"Failed to authenticate with Yazio. Last error: {last_error}")

    def get_days_data(self, token: AuthToken, start_date: date, end_date: date) -> List[DayLog]:
        self.session.headers["Authorization"] = f"Bearer {token.access_token}"

        date_list = []
        curr = start_date
        while curr <= end_date:
            date_list.append(curr)
            curr += timedelta(days=1)

        raw_days_data: List[Dict] = []
        product_ids = set()

        # 1. Fetch Days (Parallel)
        def fetch_day(day_date: date) -> Optional[Dict]:
            date_str = day_date.strftime("%Y-%m-%d")
            try:
                # Using v9 endpoint
                url = f"{self.BASE_URL}/v9/user/consumed-items"
                params = {"date": date_str}
                resp = self.session.get(url, params=params, timeout=20)

                if resp.status_code == 200:
                    data = resp.json()
                    # Data normalization
                    if isinstance(data, list):
                         items = data
                    elif isinstance(data, dict):
                         items = data.get("products", []) + data.get("simple_products", [])
                    else:
                         items = []

                    # Collect IDs
                    for item in items:
                        pid = item.get("product_id")
                        if not pid and "product" in item:
                             pid = item["product"].get("id")
                        if pid:
                            product_ids.add(pid)

                    return {"date": day_date, "items": items}
                elif resp.status_code == 404:
                    return None
            except Exception as e:
                self.logger.warning(f"Error fetching {date_str}: {e}")
                return None
            return None

        # Execute Day Fetch
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_date = {executor.submit(fetch_day, d): d for d in date_list}
            for future in concurrent.futures.as_completed(future_to_date):
                result = future.result()
                if result:
                    raw_days_data.append(result)

        # 2. Fetch Products (Parallel)
        self.logger.info(f"Fetching details for {len(product_ids)} unique products...")
        products_map: Dict[str, Product] = {}

        def fetch_product(pid: str) -> Optional[Product]:
            try:
                # Legacy code uses v9 product endpoint
                url = f"{self.BASE_URL}/v9/products/{pid}"
                resp = self.session.get(url, timeout=20)
                if resp.status_code == 200:
                    p_data = resp.json()

                    # Ensure ID is present
                    p_id = p_data.get("id", pid)
                    p_name = p_data.get("name", "Unknown Product")

                    # Nutrients in product details
                    # Legacy notes: "API returns values per base unit... fractional"
                    nutrients = self._extract_nutrients(p_data.get("nutrients", {}), p_data)

                    return Product(id=p_id, name=p_name, nutrients=nutrients)
                else:
                    self.logger.warning(f"Failed to fetch product {pid}: {resp.status_code}")
                    return None
            except Exception as e:
                self.logger.warning(f"Error fetching product {pid}: {e}")
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_pid = {executor.submit(fetch_product, pid): pid for pid in product_ids}
            for future in concurrent.futures.as_completed(future_to_pid):
                prod = future.result()
                if prod:
                    products_map[prod.id] = prod

        # 3. Hydrate and Build Domain Models
        results = []
        for day_data in raw_days_data:
            day_date = day_data["date"]
            items_data = day_data["items"]

            consumed_items = []
            for item in items_data:
                # Resolve Product
                pid = item.get("product_id")
                if not pid and "product" in item:
                     pid = item["product"].get("id")

                # Look up in map, or fallback to incomplete data (better than nothing)
                if pid and pid in products_map:
                    product = products_map[pid]
                else:
                    # Fallback
                    p_data = item.get("product", {}) or {}
                    p_name = p_data.get("name") or item.get("name") or "Unknown Product"
                    p_nutrients = self._extract_nutrients(item.get("nutrients") or p_data.get("nutrients"))
                    product = Product(id=pid or "unknown", name=p_name, nutrients=p_nutrients)

                # Amount
                amount = item.get("amount") or item.get("serving_amount") or 0.0

                # Slot
                slot_raw = item.get("daytime_slot") or item.get("slot") or item.get("daytime") or 3
                slot_mapping = {
                    "breakfast": "Café da manhã",
                    "lunch": "Almoço",
                    "dinner": "Jantar",
                    "snack": "Lanches",
                    "snacks": "Lanches",
                     0: "Café da manhã",
                     1: "Almoço",
                     2: "Jantar",
                     3: "Lanches"
                }
                slot_name = slot_mapping.get(slot_raw, "Lanches")
                if isinstance(slot_raw, str):
                     slot_name = slot_mapping.get(slot_raw.lower(), "Lanches")

                consumed_items.append(ConsumedItem(
                    product=product,
                    amount_grams=float(amount),
                    meal_slot=slot_name
                ))

            results.append(DayLog(date=day_date, consumed_items=consumed_items))

        results.sort(key=lambda x: x.date)
        return results

    def get_user_profile(self, token: AuthToken) -> Dict[str, Any]:
        # Not strictly needed for export, but implemented for interface compliance
        return {}

    def _extract_nutrients(self, data: Any, extra_context: dict = None) -> Nutrients:
        if not isinstance(data, dict):
             # Try to find nutrients in extra_context (like product root)
             if extra_context and "nutrients" in extra_context and isinstance(extra_context["nutrients"], dict):
                 data = extra_context["nutrients"]
             else:
                 return Nutrients()

        def get_val(keys):
            for k in keys:
                 # Support dot notation e.g. "energy.energy"
                 parts = k.split('.')
                 val = data
                 found = True
                 for part in parts:
                     if isinstance(val, dict) and part in val:
                         val = val[part]
                     else:
                         found = False
                         break

                 if found:
                      if isinstance(val, dict): return float(val.get("value", 0))
                      try: return float(val)
                      except: continue

                 # Fallback: check if key exists literally (unlikely but good measure)
                 if k in data:
                      v = data[k]
                      try: return float(v)
                      except: continue
            return 0.0

        return Nutrients(
            calories=get_val(["energy", "calories", "energy.energy"]),
            protein=get_val(["protein", "nutrient.protein"]),
            fat=get_val(["fat", "nutrient.fat"]),
            carbs=get_val(["carbohydrates", "carbohydrate", "carbs", "nutrient.carb"])
        )
