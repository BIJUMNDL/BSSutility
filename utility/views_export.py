import datetime

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from openpyxl import Workbook

from .models import Site, Inspection, DieselFilling


def _naive(value):
    """Strip timezone info so openpyxl can handle datetimes."""
    if isinstance(value, datetime.datetime) and value.tzinfo is not None:
        return value.replace(tzinfo=None)
    return value


def _workbook_response(wb: Workbook, filename: str) -> HttpResponse:
    resp = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(resp)
    return resp


@login_required
def export_sites_xlsx(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Sites"

    ws.append([
        "site_name", "site_code",
        "bss_incharge_name", "bss_incharge_mobile",
        "technician_name", "technician_mobile",
    ])

    for s in Site.objects.all().order_by("site_name"):
        ws.append([
            s.site_name, s.site_code,
            s.bss_incharge_name, s.bss_incharge_mobile,
            s.technician_name, s.technician_mobile,
        ])

    return _workbook_response(wb, "sites.xlsx")


@login_required
def export_inspections_xlsx(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Inspections"

    ws.append([
        "inspection_date", "site_name", "site_code",
        "eb_reading", "dg_kwh_reading", "hour_meter_reading",
        "dg_status", "dg_remarks",
        "dc_load_kw",
        "powerplant_max_modules",
        "modules_total", "modules_working", "modules_faulty", "modules_spare",
        "battery_backup_hours", "discharge_test_conducted",
        "cleanliness_of_battery",
        "aviation_lamp_condition", "fire_extinguisher_condition",
        "aircondition_status", "free_cooling_status",
        "overall_site_cleanliness",
        "created_at",
    ])

    qs = Inspection.objects.select_related("site").all().order_by("-inspection_date", "-created_at")
    for x in qs:
        ws.append([
            _naive(x.inspection_date),
            x.site.site_name, x.site.site_code,
            x.eb_reading, x.dg_kwh_reading, x.hour_meter_reading,
            x.dg_status, x.dg_remarks,
            x.dc_load_kw,
            x.powerplant_max_modules,
            x.modules_total, x.modules_working, x.modules_faulty, x.modules_spare,
            x.battery_backup_hours, x.discharge_test_conducted,
            x.cleanliness_of_battery,
            x.aviation_lamp_condition, x.fire_extinguisher_condition,
            x.aircondition_status, x.free_cooling_status,
            x.overall_site_cleanliness,
            _naive(x.created_at),
        ])

    return _workbook_response(wb, "inspections.xlsx")


@login_required
def export_diesel_xlsx(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "DieselFilling"

    ws.append([
        "date_of_filling", "site_name", "site_code",
        "balance_on_tank", "diesel_filled",
        "hour_meter_reading", "kwh",
        "balance_after_filling",
        "created_at",
    ])

    qs = DieselFilling.objects.select_related("site").all().order_by("-date_of_filling", "-created_at")
    for d in qs:
        ws.append([
            _naive(d.date_of_filling),
            d.site.site_name, d.site.site_code,
            d.balance_on_tank, d.diesel_filled,
            d.hour_meter_reading, d.kwh,
            d.balance_after_filling,
            _naive(d.created_at),
        ])

    return _workbook_response(wb, "diesel_filling.xlsx")


@login_required
def export_all_xlsx(request):
    wb = Workbook()

    # Sheet 1: Sites
    ws1 = wb.active
    ws1.title = "Sites"
    ws1.append([
        "site_name", "site_code",
        "bss_incharge_name", "bss_incharge_mobile",
        "technician_name", "technician_mobile",
    ])
    for s in Site.objects.all().order_by("site_name"):
        ws1.append([s.site_name, s.site_code, s.bss_incharge_name, s.bss_incharge_mobile, s.technician_name, s.technician_mobile])

    # Sheet 2: Inspections
    ws2 = wb.create_sheet("Inspections")
    ws2.append([
        "inspection_date", "site_name", "site_code",
        "eb_reading", "dg_kwh_reading", "hour_meter_reading",
        "dg_status", "dg_remarks",
        "dc_load_kw",
        "powerplant_max_modules",
        "modules_total", "modules_working", "modules_faulty", "modules_spare",
        "battery_backup_hours", "discharge_test_conducted",
        "cleanliness_of_battery",
        "aviation_lamp_condition", "fire_extinguisher_condition",
        "aircondition_status", "free_cooling_status",
        "overall_site_cleanliness",
        "created_at",
    ])
    for x in Inspection.objects.select_related("site").all().order_by("-inspection_date", "-created_at"):
        ws2.append([
            _naive(x.inspection_date),
            x.site.site_name, x.site.site_code,
            x.eb_reading, x.dg_kwh_reading, x.hour_meter_reading,
            x.dg_status, x.dg_remarks,
            x.dc_load_kw,
            x.powerplant_max_modules,
            x.modules_total, x.modules_working, x.modules_faulty, x.modules_spare,
            x.battery_backup_hours, x.discharge_test_conducted,
            x.cleanliness_of_battery,
            x.aviation_lamp_condition, x.fire_extinguisher_condition,
            x.aircondition_status, x.free_cooling_status,
            x.overall_site_cleanliness,
            _naive(x.created_at),
        ])

    # Sheet 3: Diesel
    ws3 = wb.create_sheet("DieselFilling")
    ws3.append([
        "date_of_filling", "site_name", "site_code",
        "balance_on_tank", "diesel_filled",
        "hour_meter_reading", "kwh",
        "balance_after_filling",
        "created_at",
    ])
    for d in DieselFilling.objects.select_related("site").all().order_by("-date_of_filling", "-created_at"):
        ws3.append([
            _naive(d.date_of_filling),
            d.site.site_name, d.site.site_code,
            d.balance_on_tank, d.diesel_filled,
            d.hour_meter_reading, d.kwh,
            d.balance_after_filling,
            _naive(d.created_at),
        ])

    return _workbook_response(wb, "bssutility_all.xlsx")