import calendar
import datetime
from decimal import Decimal

from django.db.models import Sum

from .models import DieselFilling, Inspection, Site

# Field mapping notes for this project:
# - Requested `SiteInspection` model maps to `Inspection`
# - Requested `diesel_available_liters` maps to `Inspection.diesel_balance`
# - Requested `filling_date` maps to `DieselFilling.date_of_filling`
# - Requested `liters_filled` maps to `DieselFilling.diesel_filled`
# - Requested `bss_incharge` maps to `Site.bss_incharge_name` via FK from Inspection/DieselFilling


def month_bounds(year, month):
    start = datetime.date(year, month, 1)
    if month == 12:
        next_month = datetime.date(year + 1, 1, 1)
        next_next_month = datetime.date(year + 1, 2, 1)
    elif month == 11:
        next_month = datetime.date(year, 12, 1)
        next_next_month = datetime.date(year + 1, 1, 1)
    else:
        next_month = datetime.date(year, month + 1, 1)
        next_next_month = datetime.date(year, month + 2, 1)
    return start, next_month, next_next_month


def _quantize_2(value):
    if value is None:
        return None
    return Decimal(value).quantize(Decimal("0.01"))


def _first_inspections_in_range(start_date, end_date, site_ids=None):
    qs = (
        Inspection.objects.select_related("site")
        .filter(inspection_date__gte=start_date, inspection_date__lt=end_date)
        .order_by("site_id", "inspection_date", "created_at", "id")
    )
    if site_ids is not None:
        qs = qs.filter(site_id__in=site_ids)

    first_by_site = {}
    for rec in qs:
        first_by_site.setdefault(rec.site_id, rec)
    return first_by_site


def generate_diesel_statement(month, year, bss_incharge=None):
    start_date, next_month_start, next_next_month_start = month_bounds(year, month)

    sites_qs = Site.objects.all()
    if bss_incharge:
        sites_qs = sites_qs.filter(bss_incharge_name__iexact=bss_incharge.strip())
    allowed_site_ids = list(sites_qs.values_list("id", flat=True))

    opening_map = _first_inspections_in_range(start_date, next_month_start, allowed_site_ids)
    closing_map = _first_inspections_in_range(next_month_start, next_next_month_start, allowed_site_ids)

    filled_qs = DieselFilling.objects.filter(date_of_filling__gte=start_date, date_of_filling__lt=next_month_start)
    if allowed_site_ids:
        filled_qs = filled_qs.filter(site_id__in=allowed_site_ids)
    else:
        filled_qs = filled_qs.none()

    filled_map = {
        row["site_id"]: row["total_filled"] or Decimal("0")
        for row in filled_qs.values("site_id").annotate(total_filled=Sum("diesel_filled"))
    }

    site_ids = set(opening_map.keys()) | set(closing_map.keys()) | set(filled_map.keys())
    sites = Site.objects.filter(id__in=site_ids).order_by("bss_incharge_name", "site_name")

    rows = []
    month_label = f"{calendar.month_name[month]} {year}"

    for site in sites:
        opening = opening_map.get(site.id)
        closing = closing_map.get(site.id)

        opening_balance = opening.diesel_balance if opening else None
        opening_hmr = opening.hour_meter_reading if opening else None
        closing_balance = closing.diesel_balance if closing else None
        closing_hmr = closing.hour_meter_reading if closing else None
        diesel_filled = filled_map.get(site.id, Decimal("0"))

        remarks = []
        if opening is None:
            remarks.append("No opening inspection")
        if closing is None:
            remarks.append("No next-month closing inspection")

        diesel_consumption = None
        if opening_balance is not None and closing_balance is not None:
            diesel_consumption = (opening_balance - closing_balance) + diesel_filled

        running_hours = None
        if opening_hmr is not None and closing_hmr is not None:
            running_hours = closing_hmr - opening_hmr

        hourly_consumption = None
        if running_hours is None or running_hours <= 0:
            remarks.append("Invalid HMR")
        elif diesel_consumption is not None:
            hourly_consumption = diesel_consumption / running_hours

        row = {
            "month": month_label,
            "site_id": site.id,
            "bss_incharge_name": (site.bss_incharge_name or "").strip() or "Unassigned",
            "site_name": site.site_name,
            "site_code": site.site_code,
            "opening_balance": _quantize_2(opening_balance),
            "opening_hmr": _quantize_2(opening_hmr),
            "diesel_filled": _quantize_2(diesel_filled),
            "closing_balance": _quantize_2(closing_balance),
            "closing_hmr": _quantize_2(closing_hmr),
            "diesel_consumption": _quantize_2(diesel_consumption),
            "running_hours": _quantize_2(running_hours),
            "hourly_consumption": _quantize_2(hourly_consumption),
            "remarks": ", ".join(dict.fromkeys(remarks)),
        }
        rows.append(row)

    return rows


def summarize_diesel_statement(rows):
    summary = {}
    for row in rows:
        incharge = row["bss_incharge_name"]
        agg = summary.setdefault(
            incharge,
            {
                "bss_incharge_name": incharge,
                "site_count": 0,
                "diesel_filled_total": Decimal("0"),
                "diesel_consumption_total": Decimal("0"),
                "running_hours_total": Decimal("0"),
            },
        )
        agg["site_count"] += 1
        agg["diesel_filled_total"] += row["diesel_filled"] or Decimal("0")
        agg["diesel_consumption_total"] += row["diesel_consumption"] or Decimal("0")
        agg["running_hours_total"] += row["running_hours"] or Decimal("0")

    summary_rows = []
    for incharge in sorted(summary.keys()):
        agg = summary[incharge]
        hourly_total = None
        if agg["running_hours_total"] > 0:
            hourly_total = agg["diesel_consumption_total"] / agg["running_hours_total"]
        summary_rows.append(
            {
                "bss_incharge_name": agg["bss_incharge_name"],
                "site_count": agg["site_count"],
                "diesel_filled_total": _quantize_2(agg["diesel_filled_total"]),
                "diesel_consumption_total": _quantize_2(agg["diesel_consumption_total"]),
                "running_hours_total": _quantize_2(agg["running_hours_total"]),
                "hourly_consumption_total": _quantize_2(hourly_total),
            }
        )
    return summary_rows


def build_diesel_statement(year, month, bss_incharge=None):
    rows = generate_diesel_statement(month=month, year=year, bss_incharge=bss_incharge)
    summary_rows = summarize_diesel_statement(rows)
    start_date, next_month_start, _ = month_bounds(year, month)
    return {
        "rows": rows,
        "summary_rows": summary_rows,
        "start_date": start_date,
        "next_month_start": next_month_start,
    }
