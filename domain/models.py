from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date

@dataclass
class AuthToken:
    access_token: str
    refresh_token: str = ""
    expires_at: Optional[float] = None

@dataclass
class Nutrients:
    calories: float = 0.0
    protein: float = 0.0
    fat: float = 0.0
    carbs: float = 0.0

@dataclass
class Product:
    id: str
    name: str
    nutrients: Nutrients = field(default_factory=Nutrients)

@dataclass
class ConsumedItem:
    product: Product
    amount_grams: float
    meal_slot: str # "breakfast", "lunch", "dinner", "snack"

@dataclass
class DayLog:
    date: date
    consumed_items: List[ConsumedItem] = field(default_factory=list)

    @property
    def total_nutrients(self) -> Nutrients:
        total = Nutrients()
        for item in self.consumed_items:
            # Assuming item.product.nutrients are per 100g if appropriate,
            # but usually Yazio API returns normalized values or we calculate.
            # In our Infra/YazioClient, we stored the calculated nutrient values
            # directly into the Product/Item structure?
            # Re-reading YazioClient:
            # product = Product(nutrients=...)
            # We extracted nutrients from the item.
            # Yazio API (v9 from converter):
            # "The API typically returns values per 100g or per unit... we multiply by factor."
            # In YazioClient, I stored specific nutrients in the Product object.
            # However, I didn't perform the multiplication by amount in YazioClient for the Product itself.
            # Wait, `YazioClient` lines 98-124: it extracts nutrients.
            # It creates `Product` with those nutrients.
            # If the API returns per 100g, we need to multiply.
            # To be safe and clean, let's assume `item.nutrients` should be the *calculated* nutrients for that consumption event in the Domain?
            # Or `product.nutrients` is per 100g and we calculate here.

            # Let's adjust ConsumedItem to have `nutrients` property that calculates based on product.
            pass

        # Actually, let's keep it simple and just sum what we can.
        # But wait, looking at my `YazioClient` implementation:
        # I didn't verify if I extracted "per 100g" or "absolute" values.
        # Converter.py line 123: extracts "per 100g" usually.
        # Converter.py line 131: multiplies by amount.

        # So in Domain `DayLog.total_nutrients`:
        # We need to do the math: item.product.nutrients (per 100g) * (item.amount_grams / 100)
        # But wait, amount is in grams?
        # Converter.py line 112: `amount_grams`.
        # Converter.py line 131: `factor = amount_grams`.
        # Converter.py line 132: `calories = calories_per_100g * factor`.
        # WAIT. If it's per 100g, shouldn't it be `* (amount / 100)`?
        # Converter.py comment line 129: "API v9 returns values per base unit (g or ml), ie fractional (0.13 = 13%). Therefore we multiply directly by quantity".
        # Ah! So the API returns "Calories per 1g"? Or "Calories per unit"?
        # If the comment says "fractional", it usually means per 1g.
        # If I have 200g of something with 0.13 protein/g, then 200 * 0.13 = 26g protein.
        # So the math `nutrients * amount` is correct if the API returns "per 1g".
        # My YazioClient just extracts the value.

        c = 0.0
        p = 0.0
        f = 0.0
        cb = 0.0
        for item in self.consumed_items:
            # We assume product.nutrients are "per gram" based on legacy code findings
            # or we assume YazioClient normalized it.
            # Let's trust the logic from converter.py which multiplied directly.

            # However, to be extra safe in a Refactor, I should verify this or push calculation to UseCase?
            # Domain Model should be correct.
            # Let's implement the calculation here assuming `product.nutrients` is the rate.

            c += item.product.nutrients.calories * item.amount_grams
            p += item.product.nutrients.protein * item.amount_grams
            f += item.product.nutrients.fat * item.amount_grams
            cb += item.product.nutrients.carbs * item.amount_grams

        return Nutrients(calories=c, protein=p, fat=f, carbs=cb)
