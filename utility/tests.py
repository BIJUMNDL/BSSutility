from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .diesel_statement import generate_diesel_statement
from .models import DieselFilling, Inspection, Site


class DieselStatementServiceTests(TestCase):
    def setUp(self):
        self.site = Site.objects.create(
            site_name="SITE-A",
            site_code="A001",
            bss_incharge_name="Incharge 1",
        )

    def _make_inspection(self, y, m, d, diesel_balance=None, hmr=None):
        return Inspection.objects.create(
            site=self.site,
            inspection_date=date(y, m, d),
            diesel_balance=diesel_balance,
            hour_meter_reading=hmr,
        )

    def _make_filling(self, y, m, d, liters):
        return DieselFilling.objects.create(
            site=self.site,
            date_of_filling=date(y, m, d),
            diesel_filled=Decimal(liters),
            balance_on_tank=Decimal("0"),
            balance_after_filling=Decimal("0"),
        )

    def _row(self):
        rows = generate_diesel_statement(month=3, year=2026)
        self.assertEqual(len(rows), 1)
        return rows[0]

    def test_opening_uses_earliest_inspection_in_month(self):
        self._make_inspection(2026, 3, 5, diesel_balance=Decimal("100"), hmr=Decimal("200"))
        self._make_inspection(2026, 3, 20, diesel_balance=Decimal("300"), hmr=Decimal("500"))
        self._make_inspection(2026, 4, 2, diesel_balance=Decimal("80"), hmr=Decimal("240"))

        row = self._row()
        self.assertEqual(row["opening_balance"], Decimal("100.00"))
        self.assertEqual(row["opening_hmr"], Decimal("200.00"))

    def test_closing_uses_earliest_inspection_in_next_month(self):
        self._make_inspection(2026, 3, 5, diesel_balance=Decimal("100"), hmr=Decimal("200"))
        self._make_inspection(2026, 4, 2, diesel_balance=Decimal("70"), hmr=Decimal("230"))
        self._make_inspection(2026, 4, 10, diesel_balance=Decimal("50"), hmr=Decimal("260"))

        row = self._row()
        self.assertEqual(row["closing_balance"], Decimal("70.00"))
        self.assertEqual(row["closing_hmr"], Decimal("230.00"))

    def test_diesel_filled_is_month_sum(self):
        self._make_inspection(2026, 3, 5, diesel_balance=Decimal("100"), hmr=Decimal("200"))
        self._make_inspection(2026, 4, 2, diesel_balance=Decimal("70"), hmr=Decimal("230"))
        self._make_filling(2026, 3, 6, "10")
        self._make_filling(2026, 3, 20, "15")
        self._make_filling(2026, 4, 4, "99")  # outside selected month; ignored

        row = self._row()
        self.assertEqual(row["diesel_filled"], Decimal("25.00"))

    def test_consumption_formula_is_correct(self):
        self._make_inspection(2026, 3, 5, diesel_balance=Decimal("100"), hmr=Decimal("200"))
        self._make_inspection(2026, 4, 2, diesel_balance=Decimal("60"), hmr=Decimal("260"))
        self._make_filling(2026, 3, 6, "20")
        self._make_filling(2026, 3, 20, "10")

        row = self._row()
        self.assertEqual(row["diesel_consumption"], Decimal("70.00"))  # 100 - 60 + 30
        self.assertEqual(row["running_hours"], Decimal("60.00"))  # 260 - 200
        self.assertEqual(row["hourly_consumption"], Decimal("1.17"))  # 70 / 60

    def test_divide_by_zero_adds_invalid_hmr_remark(self):
        self._make_inspection(2026, 3, 5, diesel_balance=Decimal("100"), hmr=Decimal("200"))
        self._make_inspection(2026, 4, 2, diesel_balance=Decimal("70"), hmr=Decimal("200"))
        self._make_filling(2026, 3, 6, "10")

        row = self._row()
        self.assertEqual(row["running_hours"], Decimal("0.00"))
        self.assertIsNone(row["hourly_consumption"])
        self.assertIn("Invalid HMR", row["remarks"])


class DieselStatementRestrictionTests(TestCase):
    def _latest_closed_month(self, today):
        if today.month == 1:
            return today.year - 1, 12
        return today.year, today.month - 1

    def test_statement_view_restricts_current_month(self):
        today = timezone.localdate()
        latest_year, latest_month = self._latest_closed_month(today)

        response = self.client.get(
            reverse("diesel_statement_list"),
            {"year": today.year, "month": today.month},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_year"], latest_year)
        self.assertEqual(response.context["selected_month"], latest_month)

    def test_statement_export_rejects_current_month(self):
        today = timezone.localdate()

        response = self.client.get(
            reverse("export_diesel_statement_xlsx"),
            {"year": today.year, "month": today.month},
        )

        self.assertEqual(response.status_code, 400)
