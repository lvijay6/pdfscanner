import datetime
from typing import Dict, Any, List

class ExpenseManagerService:
    """Module 10: Expense Management & Receipt Scanner Integration"""

    _expenses: List[Dict[str, Any]] = [
        {"id": "EXP-101", "vendor": "Starbucks Coffee", "amount": 45.50, "category": "Food & Travel", "date": "2026-03-20", "gst_amount": 8.19, "status": "Verified"},
        {"id": "EXP-102", "vendor": "Amazon Web Services", "amount": 450.00, "category": "Software & Hosting", "date": "2026-03-22", "gst_amount": 81.00, "status": "Verified"},
        {"id": "EXP-103", "vendor": "Uber Trips", "amount": 32.80, "category": "Food & Travel", "date": "2026-03-25", "gst_amount": 5.90, "status": "Pending Review"}
    ]

    @classmethod
    def add_expense(cls, vendor: str, amount: float, category: str, date: str = None, gst_included: bool = True) -> Dict[str, Any]:
        exp_id = f"EXP-{len(cls._expenses) + 101}"
        exp_date = date or datetime.date.today().isoformat()
        gst_amount = round(amount * 0.18, 2) if gst_included else 0.0

        entry = {
            "id": exp_id,
            "vendor": vendor,
            "amount": amount,
            "category": category,
            "date": exp_date,
            "gst_amount": gst_amount,
            "status": "Verified"
        }
        cls._expenses.append(entry)
        return entry

    @classmethod
    def get_summary_report(cls) -> Dict[str, Any]:
        total_spend = sum(item["amount"] for item in cls._expenses)
        total_gst = sum(item["gst_amount"] for item in cls._expenses)
        by_category = {}
        for item in cls._expenses:
            cat = item["category"]
            by_category[cat] = round(by_category.get(cat, 0.0) + item["amount"], 2)

        return {
            "total_expenses_count": len(cls._expenses),
            "total_spend": round(total_spend, 2),
            "total_gst_reclaimable": round(total_gst, 2),
            "category_breakdown": by_category,
            "recent_expenses": cls._expenses[-5:]
        }
