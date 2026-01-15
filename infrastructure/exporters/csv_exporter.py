import csv
from pathlib import Path
from typing import List, Dict
from domain.interfaces import IExporter
from domain.models import DayLog

class CsvExporter(IExporter):
    def export(self, data: List[DayLog], output_dir: str) -> List[str]:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        created_files = []

        # 1. nutrition_log.csv
        log_path = output_path / "nutrition_log.csv"
        self._write_nutrition_log(data, log_path)
        created_files.append(str(log_path))

        # 2. meal_summary.csv
        meal_path = output_path / "meal_summary.csv"
        self._write_meal_summary(data, meal_path)
        created_files.append(str(meal_path))

        # 3. daily_summary.csv
        daily_path = output_path / "daily_summary.csv"
        self._write_daily_summary(data, daily_path)
        created_files.append(str(daily_path))

        return created_files

    def _write_nutrition_log(self, days: List[DayLog], path: Path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "date", "meal", "product_name", "amount_g",
                "calories", "protein_g", "fat_g", "carbs_g"
            ])
            writer.writeheader()

            for day in days:
                for item in day.consumed_items:
                    # Calculate values for this specific amount
                    n = item.product.nutrients
                    # Assuming nutrients are per gram as established
                    amt = item.amount_grams

                    writer.writerow({
                        "date": day.date.strftime("%Y-%m-%d"),
                        "meal": item.meal_slot,
                        "product_name": item.product.name,
                        "amount_g": round(amt, 1),
                        "calories": round(n.calories * amt, 1),
                        "protein_g": round(n.protein * amt, 1),
                        "fat_g": round(n.fat * amt, 1),
                        "carbs_g": round(n.carbs * amt, 1)
                    })

    def _write_meal_summary(self, days: List[DayLog], path: Path):
        # Dictionary to aggregate: (date, meal) -> calories
        summary: Dict[tuple, float] = {}

        for day in days:
            date_str = day.date.strftime("%Y-%m-%d")
            for item in day.consumed_items:
                key = (date_str, item.meal_slot)
                cal = item.product.nutrients.calories * item.amount_grams
                summary[key] = summary.get(key, 0.0) + cal

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["date", "meal", "calories"])
            writer.writeheader()

            # Sort by date then meal??
            # Sorting logic: Date asc, then meal order?
            # Meal slot is string, so sorting might be alphabetical if not careful.
            # Let's just sort by date key.
            for (d, m), cal in sorted(summary.items()):
                writer.writerow({
                    "date": d,
                    "meal": m,
                    "calories": round(cal, 1)
                })

    def _write_daily_summary(self, days: List[DayLog], path: Path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "date", "calories", "protein_g", "fat_g", "carbs_g"
            ])
            writer.writeheader()

            for day in days:
                t = day.total_nutrients
                writer.writerow({
                    "date": day.date.strftime("%Y-%m-%d"),
                    "calories": round(t.calories, 1),
                    "protein_g": round(t.protein, 1),
                    "fat_g": round(t.fat, 1),
                    "carbs_g": round(t.carbs, 1)
                })
