from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import Site
from .forms import InspectionForm, DieselFillingForm
from .forms import SiteUploadForm

def site_search_api(request):
    q = request.GET.get("q", "").strip()
    qs = Site.objects.all().order_by("site_name")
    if q:
        qs = qs.filter(site_name__icontains=q)
    qs = qs[:20]

    results = [{
        "id": s.id,
        "text": f"{s.site_name} ({s.site_code or ''})",
        "site_code": s.site_code,
        "bss_incharge_name": s.bss_incharge_name,
        "bss_incharge_mobile": s.bss_incharge_mobile,
        "technician_name": s.technician_name,
        "technician_mobile": s.technician_mobile,
    } for s in qs]

    return JsonResponse({"results": results})

def inspection_create(request):
    if request.method == "POST":
        form = InspectionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("inspection_create")
    else:
        form = InspectionForm()
    return render(request, "utility/inspection_form.html", {"form": form})

def diesel_filling_create(request):
    if request.method == "POST":
        form = DieselFillingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("diesel_filling_create")
    else:
        form = DieselFillingForm()
    return render(request, "utility/diesel_filling_form.html", {"form": form})

import os
import tempfile

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

import openpyxl

from .models import Site
from .forms import InspectionForm, DieselFillingForm
from .forms_upload import SiteUploadForm


def site_search_api(request):
    q = request.GET.get("q", "").strip()
    qs = Site.objects.all().order_by("site_name")
    if q:
        qs = qs.filter(site_name__icontains=q)
    qs = qs[:20]

    results = [{
        "id": s.id,
        "text": f"{s.site_name} ({s.site_code or ''})",
        "site_code": s.site_code,
        "bss_incharge_name": s.bss_incharge_name,
        "bss_incharge_mobile": s.bss_incharge_mobile,
        "technician_name": s.technician_name,
        "technician_mobile": s.technician_mobile,
    } for s in qs]

    return JsonResponse({"results": results})


def inspection_create(request):
    if request.method == "POST":
        form = InspectionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("inspection_create")
    else:
        form = InspectionForm()

    return render(request, "utility/inspection_form.html", {"form": form})


def diesel_filling_create(request):
    if request.method == "POST":
        form = DieselFillingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("diesel_filling_create")
    else:
        form = DieselFillingForm()

    return render(request, "utility/diesel_filling_form.html", {"form": form})


#@login_required
def upload_sites(request):
    """
    Upload an Excel (.xlsx) file and import/update Site master table.
    """
    if request.method == "POST":
        form = SiteUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data["file"]
            sheet_name = form.cleaned_data.get("sheet") or None
            header_row = form.cleaned_data.get("header_row") or 1

            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext != ".xlsx":
                messages.error(request, "Please upload an .xlsx Excel file only.")
                return redirect("upload_sites")

            # Save file to temp path
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                for chunk in uploaded_file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name

            try:
                created, updated, skipped = import_sites_from_xlsx(
                    tmp_path, sheet_name=sheet_name, header_row=header_row
                )
                messages.success(
                    request,
                    f"Upload completed ✅ Created: {created}, Updated: {updated}, Skipped: {skipped}"
                )
            except Exception as e:
                messages.error(request, f"Import failed: {e}")
            finally:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

            return redirect("upload_sites")
    else:
        form = SiteUploadForm()

    return render(request, "utility/upload_sites.html", {"form": form})


def import_sites_from_xlsx(xlsx_path, sheet_name=None, header_row=1):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb[sheet_name] if sheet_name else wb[wb.sheetnames[0]]

    # Read header row
    headers = []
    for cell in ws[header_row]:
        headers.append(str(cell.value).strip() if cell.value is not None else "")
    header_map = {h.lower(): idx for idx, h in enumerate(headers)}

    def get(row_values, *possible_headers):
        for h in possible_headers:
            idx = header_map.get(h.lower())
            if idx is not None and idx < len(row_values):
                v = row_values[idx]
                if v is None:
                    continue
                return str(v).strip() if isinstance(v, str) else v
        return None

    created = updated = skipped = 0

    for r in range(header_row + 1, ws.max_row + 1):
        row = [ws.cell(row=r, column=c).value for c in range(1, ws.max_column + 1)]

        site_name = get(row, "site_name", "site name", "site")
        if not site_name:
            skipped += 1
            continue

        site_code = get(row, "site_code", "site code", "pkey", "site id")
        bss_incharge_name = get(row, "bss_incharge_name", "bss incharge name", "bss incharge")
        bss_incharge_mobile = get(row, "bss_incharge_mobile", "bss incharge mobile", "bss mobile", "incharge mobile")
        technician_name = get(row, "technician_name", "technician name", "technicial name", "technical name")
        technician_mobile = get(row, "technician_mobile", "technician mobile", "technical mobile", "mobile number")

        obj, is_created = Site.objects.get_or_create(site_name=str(site_name).strip())

        if site_code is not None:
            obj.site_code = str(site_code).strip()
        if bss_incharge_name is not None:
            obj.bss_incharge_name = str(bss_incharge_name).strip()
        if bss_incharge_mobile is not None:
            obj.bss_incharge_mobile = str(bss_incharge_mobile).strip()
        if technician_name is not None:
            obj.technician_name = str(technician_name).strip()
        if technician_mobile is not None:
            obj.technician_mobile = str(technician_mobile).strip()

        obj.save()

        if is_created:
            created += 1
        else:
            updated += 1

    return created, updated, skipped
