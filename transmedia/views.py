from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .excel_import import read_inventory_sheet
from .forms import (
    ExcelUploadForm,
    MediaInventoryForm,
    ReparentingForm,
    DmwToOfForm,
    CpanToMaanForm,
    DmwMakeChangeForm,
    DiversionActionForm,
    ShiftToStoreForm,
)
from .models import MediaInventory, MediaChangeLog, SpareDMW, DiversionDMW
from .utils import snapshot, log_change


@login_required
def inventory_list(request):
    q = (request.GET.get("q") or "").strip()
    export = (request.GET.get("export") or "").strip()

    qs = MediaInventory.objects.all().order_by("site_name")
    if q:
        qs = qs.filter(Q(site_name__icontains=q) | Q(terminalequipment_id__icontains=q))

    if export == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="media_inventory.csv"'
        writer = csv.writer(response)
        writer.writerow([
            "Site", "Media", "B END", "Terminal Eq", "Make", "TE ID", "Cluster", "2G", "3G", "4G"
        ])
        for r in qs:
            writer.writerow([
                r.site_name,
                r.transmission_media,
                r.b_end,
                r.terminal_equipment_type,
                r.make,
                r.terminalequipment_id,
                r.cluster,
                r.port_2g,
                r.port_3g,
                r.port_4g,
            ])
        return response

    return render(request, "transmedia/inventory_list.html", {"rows": qs, "q": q})


@login_required
def inventory_edit(request, pk):
    obj = get_object_or_404(MediaInventory, pk=pk)
    old = snapshot(obj)

    if request.method == "POST":
        form = MediaInventoryForm(request.POST, instance=obj)
        if form.is_valid():
            rec = form.save()  # model.save regenerates TE ID always
            new = snapshot(rec)
            log_change(record=rec, action="EDIT", old_data=old, new_data=new, user=request.user)
            messages.success(request, "Record updated.")
            return redirect("transmedia:inventory_list")
    else:
        form = MediaInventoryForm(instance=obj)

    return render(request, "transmedia/inventory_edit.html", {"form": form, "obj": obj})


@login_required
def excel_upload(request):
    if request.method == "POST":
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            f = form.cleaned_data["file"]

            try:
                df = read_inventory_sheet(f)
            except Exception as e:
                messages.error(request, f"Excel read failed: {e}")
                return redirect("transmedia:excel_upload")

            created, updated = 0, 0

            with transaction.atomic():
                for _, row in df.iterrows():
                    site = (row.get("site_name") or "").strip()
                    te_type = (row.get("terminal_equipment_type") or "").strip()

                    if not site:
                        continue

                    # ✅ Simple uniqueness by site_name (can change if needed)
                    obj, is_created = MediaInventory.objects.get_or_create(
                        site_name=site,
                        defaults={"terminal_equipment_type": te_type},
                    )
                    old = snapshot(obj)

                    # Update from Excel (TE ID ignored - always auto)
                    sl = row.get("sl_no")
                    if sl and str(sl).isdigit():
                        obj.sl_no = int(sl)

                    obj.transmission_media = row.get("transmission_media") or obj.transmission_media
                    obj.a_end = row.get("a_end") or obj.a_end
                    obj.b_end = row.get("b_end") or obj.b_end
                    obj.terminal_equipment_type = te_type or obj.terminal_equipment_type
                    obj.make = row.get("make") or obj.make
                    obj.cluster = row.get("cluster") or obj.cluster
                    obj.port_2g = row.get("port_2g") or obj.port_2g
                    obj.port_3g = row.get("port_3g") or obj.port_3g
                    obj.port_4g = row.get("port_4g") or obj.port_4g

                    obj.save()  # regenerates TE ID
                    new = snapshot(obj)

                    log_change(
                        record=obj,
                        action="EXCEL_UPLOAD" if is_created else "EXCEL_UPDATE",
                        old_data=old,
                        new_data=new,
                        user=request.user,
                        remarks="Uploaded via Excel template",
                    )

                    if is_created:
                        created += 1
                    else:
                        updated += 1

            messages.success(request, f"Excel processed. Created: {created}, Updated: {updated}")
            return redirect("transmedia:inventory_list")
    else:
        form = ExcelUploadForm()

    return render(request, "transmedia/excel_upload.html", {"form": form})


@login_required
def action_update(request, pk):
    obj = get_object_or_404(MediaInventory, pk=pk)
    old = snapshot(obj)

    if request.method != "POST":
        return redirect("transmedia:inventory_list")

    action = (request.POST.get("action") or "").strip()
    new_b_end = (request.POST.get("b_end") or "").strip()
    new_make = (request.POST.get("make") or "").strip()
    remarks = (request.POST.get("remarks") or "").strip() or None

    # 1) Reparenting: change B END
    if action == "REPAR":
        if new_b_end:
            obj.b_end = new_b_end

    # 2) DMW → OF conversion
    elif action == "DMW_TO_OF":
        obj.transmission_media = "OF"
        if new_b_end:
            obj.b_end = new_b_end
        if new_make:
            obj.make = new_make

    # 3) CPAN → MAAN conversion (only column G changes to MAAN)
    elif action == "CPAN_TO_MAAN":
        obj.terminal_equipment_type = "MAAN"
        if new_b_end:
            obj.b_end = new_b_end
        if new_make:
            obj.make = new_make

    # 4) DMW → DMW Make change (correct)
    elif action == "DMW_MAKE_CHANGE":
        obj.transmission_media = "DMW"
        obj.terminal_equipment_type = "DMW"
        if new_make:
            obj.make = new_make
        if new_b_end:
            obj.b_end = new_b_end

    else:
        messages.error(request, "Invalid action.")
        return redirect("transmedia:inventory_list")

    obj.save()  # regenerates TE ID always
    new = snapshot(obj)

    log_change(record=obj, action=action, old_data=old, new_data=new, user=request.user, remarks=remarks)
    messages.success(request, f"Action applied: {action}")
    return redirect("transmedia:inventory_list")


@login_required
def log_list(request):
    q = (request.GET.get("q") or "").strip()
    action = (request.GET.get("action") or "").strip()
    export = (request.GET.get("export") or "").strip()

    logs = MediaChangeLog.objects.select_related("record").order_by("-created_at")

    if q:
        logs = logs.filter(Q(site_name__icontains=q) | Q(action__icontains=q))

    if action:
        logs = logs.filter(action=action)

    actions = MediaChangeLog.objects.values_list("action", flat=True).distinct().order_by("action")

    if export == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="media_change_logs.csv"'
        writer = csv.writer(response)
        writer.writerow(["Date", "Site", "Action", "User", "Remarks", "Old", "New"])
        for l in logs:
            writer.writerow([
                l.created_at,
                l.site_name,
                l.action,
                l.changed_by,
                l.remarks or "",
                l.old_data,
                l.new_data,
            ])
        return response

    return render(request, "transmedia/log_list.html", {
        "logs": logs, "q": q, "actions": actions, "action_selected": action
    })


@login_required
def spare_list(request):
    q = (request.GET.get("q") or "").strip()
    stored = (request.GET.get("stored") or "").strip()
    export = (request.GET.get("export") or "").strip()

    spares = SpareDMW.objects.select_related("record").order_by("-created_at")

    if q:
        spares = spares.filter(
            Q(terminalequipment_id__icontains=q) |
            Q(terminal_equipment__icontains=q) |
            Q(record__site_name__icontains=q)
        )

    if stored:
        spares = spares.filter(stored=stored)

    stored_choices = SpareDMW.STORED_CHOICES

    if export == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="spare_dmw_records.csv"'
        writer = csv.writer(response)
        writer.writerow([
            "Terminal Equipment",
            "Date of Decommissioning",
            "TE ID",
            "Date of Commissioning",
            "Stored",
            "Site",
        ])
        for s in spares:
            writer.writerow([
                s.terminal_equipment,
                s.date_of_decommissioning,
                s.terminalequipment_id,
                s.date_of_commissioning,
                s.get_stored_display(),
                s.record.site_name if s.record else "",
            ])
        return response

    return render(request, "transmedia/spare_list.html", {
        "spares": spares, "q": q, "stored": stored, "stored_choices": stored_choices
    })


@login_required
def migrations_index(request):
    return render(request, "transmedia/migrations_index.html")


@login_required
def migration_diversion(request):
    if request.method == "POST":
        form = DiversionActionForm(request.POST)
        if form.is_valid():
            spare = form.cleaned_data["spare"]
            obj = spare.record
            site_name = (form.cleaned_data.get("site_name") or "").strip()
            diversion_letter_no = (form.cleaned_data.get("diversion_letter_no") or "").strip()
            remarks = form.cleaned_data.get("remarks") or None

            DiversionDMW.objects.create(
                record=obj,
                site_name=site_name or (obj.site_name if obj else ""),
                diversion_letter_no=diversion_letter_no,
                remarks=remarks,
            )

            spare.stored = "DIVERTED"
            spare.save(update_fields=["stored"])

            diversion_text = f"Diversion letter: {diversion_letter_no} | {site_name or (obj.site_name if obj else '')}"
            if obj:
                log_change(
                    record=obj,
                    action="DIVERSION",
                    old_data=snapshot(obj),
                    new_data=snapshot(obj),
                    user=request.user,
                    remarks=diversion_text,
                )

            messages.success(request, "Diversion recorded.")
            return redirect("transmedia:migrations_index")
    else:
        form = DiversionActionForm()

    return render(request, "transmedia/migration_diversion.html", {"form": form})


@login_required
def migration_shift_to_store(request):
    if request.method == "POST":
        form = ShiftToStoreForm(request.POST)
        if form.is_valid():
            spare = form.cleaned_data["spare"]
            spare.stored = "BSS_STORE"
            spare.save(update_fields=["stored"])

            if spare.record:
                log_change(
                    record=spare.record,
                    action="SHIFT_TO_STORE",
                    old_data=snapshot(spare.record),
                    new_data=snapshot(spare.record),
                    user=request.user,
                    remarks="Shifted to store (BSS Store)",
                )

            messages.success(request, "Shift to store recorded.")
            return redirect("transmedia:migrations_index")
    else:
        form = ShiftToStoreForm()

    return render(request, "transmedia/migration_shift_to_store.html", {"form": form})


@login_required
def migration_reparenting(request):
    if request.method == "POST":
        form = ReparentingForm(request.POST)
        if form.is_valid():
            obj = form.cleaned_data["record"]
            new_b_end = form.cleaned_data["b_end"]
            new_te_type = (form.cleaned_data.get("terminal_equipment_type") or "").strip()
            new_make = (form.cleaned_data.get("make") or "").strip()
            new_cluster = (form.cleaned_data.get("cluster") or "").strip()
            new_port_2g = (form.cleaned_data.get("port_2g") or "").strip()
            new_port_3g = (form.cleaned_data.get("port_3g") or "").strip()
            new_port_4g = (form.cleaned_data.get("port_4g") or "").strip()
            remarks = form.cleaned_data.get("remarks") or None

            old = snapshot(obj)
            obj.b_end = new_b_end
            obj.terminal_equipment_type = new_te_type
            obj.make = new_make
            obj.cluster = new_cluster
            obj.port_2g = new_port_2g
            obj.port_3g = new_port_3g
            obj.port_4g = new_port_4g
            obj.save()
            new = snapshot(obj)

            log_change(record=obj, action="REPAR", old_data=old, new_data=new, user=request.user, remarks=remarks)
            messages.success(request, "Reparenting applied.")
            return redirect("transmedia:migrations_index")
    else:
        form = ReparentingForm()

    return render(request, "transmedia/migration_reparenting.html", {"form": form})


@login_required
def migration_dmw_to_of(request):
    if request.method == "POST":
        form = DmwToOfForm(request.POST)
        if form.is_valid():
            obj = form.cleaned_data["record"]
            new_te_type = (form.cleaned_data.get("terminal_equipment_type") or "").strip()
            new_b_end = (form.cleaned_data.get("b_end") or "").strip()
            new_make = (form.cleaned_data.get("make") or "").strip()
            new_cluster = (form.cleaned_data.get("cluster") or "").strip()
            new_port_2g = (form.cleaned_data.get("port_2g") or "").strip()
            new_port_3g = (form.cleaned_data.get("port_3g") or "").strip()
            new_port_4g = (form.cleaned_data.get("port_4g") or "").strip()
            disposition = (form.cleaned_data.get("disposition") or "").strip()
            diverted_site_name = (form.cleaned_data.get("diverted_site_name") or "").strip()
            diversion_order = (form.cleaned_data.get("diversion_order") or "").strip()
            date_of_decommissioning = form.cleaned_data.get("date_of_decommissioning")
            date_of_commissioning = form.cleaned_data.get("date_of_commissioning")
            stored = (form.cleaned_data.get("stored") or "").strip() or None
            remarks = form.cleaned_data.get("remarks") or None

            old = snapshot(obj)
            obj.transmission_media = "OF"
            obj.terminal_equipment_type = new_te_type
            obj.b_end = new_b_end
            obj.make = new_make
            obj.cluster = new_cluster
            obj.port_2g = new_port_2g
            obj.port_3g = new_port_3g
            obj.port_4g = new_port_4g
            obj.save()
            new = snapshot(obj)

            if disposition == "DIVERSION":
                diversion_text = f"Diversion order: {diversion_order} | Diverted site: {diverted_site_name} | From: {old.get('site_name')}"
                remarks = f"{remarks} | {diversion_text}" if remarks else diversion_text
                DiversionDMW.objects.create(
                    record=obj,
                    site_name=diverted_site_name,
                    diversion_letter_no=diversion_order,
                    remarks=remarks,
                )
                SpareDMW.objects.create(
                    record=obj,
                    terminal_equipment=old.get("terminal_equipment_type"),
                    terminalequipment_id=old.get("terminalequipment_id"),
                    stored="DIVERTED",
                )
            elif disposition == "DECOMMISSION":
                SpareDMW.objects.create(
                    record=obj,
                    terminal_equipment=old.get("terminal_equipment_type"),
                    date_of_decommissioning=date_of_decommissioning,
                    terminalequipment_id=old.get("terminalequipment_id"),
                    date_of_commissioning=date_of_commissioning,
                    stored=stored,
                )

            log_change(record=obj, action="DMW_TO_OF", old_data=old, new_data=new, user=request.user, remarks=remarks)
            messages.success(request, "DMW to OF conversion applied.")
            return redirect("transmedia:migrations_index")
    else:
        form = DmwToOfForm()

    return render(request, "transmedia/migration_dmw_to_of.html", {"form": form})


@login_required
def migration_cpan_to_maan(request):
    if request.method == "POST":
        form = CpanToMaanForm(request.POST)
        if form.is_valid():
            obj = form.cleaned_data["record"]
            new_b_end = (form.cleaned_data.get("b_end") or "").strip()
            new_make = (form.cleaned_data.get("make") or "").strip()
            new_cluster = (form.cleaned_data.get("cluster") or "").strip()
            new_port_2g = (form.cleaned_data.get("port_2g") or "").strip()
            new_port_3g = (form.cleaned_data.get("port_3g") or "").strip()
            new_port_4g = (form.cleaned_data.get("port_4g") or "").strip()
            remarks = form.cleaned_data.get("remarks") or None

            old = snapshot(obj)
            obj.terminal_equipment_type = "MAAN"
            obj.b_end = new_b_end
            obj.make = new_make
            obj.cluster = new_cluster
            obj.port_2g = new_port_2g
            obj.port_3g = new_port_3g
            obj.port_4g = new_port_4g
            obj.save()
            new = snapshot(obj)

            log_change(record=obj, action="CPAN_TO_MAAN", old_data=old, new_data=new, user=request.user, remarks=remarks)
            messages.success(request, "CPAN to MAAN conversion applied.")
            return redirect("transmedia:migrations_index")
    else:
        form = CpanToMaanForm()

    return render(request, "transmedia/migration_cpan_to_maan.html", {"form": form})


@login_required
def migration_dmw_make_change(request):
    if request.method == "POST":
        form = DmwMakeChangeForm(request.POST)
        if form.is_valid():
            obj = form.cleaned_data["record"]
            new_b_end = (form.cleaned_data.get("b_end") or "").strip()
            new_make = (form.cleaned_data.get("make") or "").strip()
            disposition = (form.cleaned_data.get("disposition") or "").strip()
            diverted_site_name = (form.cleaned_data.get("diverted_site_name") or "").strip()
            diversion_order = (form.cleaned_data.get("diversion_order") or "").strip()
            date_of_decommissioning = form.cleaned_data.get("date_of_decommissioning")
            date_of_commissioning = form.cleaned_data.get("date_of_commissioning")
            stored = (form.cleaned_data.get("stored") or "").strip() or None
            remarks = form.cleaned_data.get("remarks") or None

            old = snapshot(obj)
            obj.transmission_media = "DMW"
            obj.terminal_equipment_type = "DMW"
            if new_b_end:
                obj.b_end = new_b_end
            if new_make:
                obj.make = new_make
            obj.save()
            new = snapshot(obj)

            if disposition == "DIVERSION":
                diversion_text = f"Diversion order: {diversion_order} | Diverted site: {diverted_site_name} | From: {old.get('site_name')}"
                remarks = f"{remarks} | {diversion_text}" if remarks else diversion_text
                DiversionDMW.objects.create(
                    record=obj,
                    site_name=diverted_site_name,
                    diversion_letter_no=diversion_order,
                    remarks=remarks,
                )
                SpareDMW.objects.create(
                    record=obj,
                    terminal_equipment=old.get("terminal_equipment_type"),
                    terminalequipment_id=old.get("terminalequipment_id"),
                    stored="DIVERTED",
                )
            elif disposition == "DECOMMISSION":
                SpareDMW.objects.create(
                    record=obj,
                    terminal_equipment=old.get("terminal_equipment_type"),
                    date_of_decommissioning=date_of_decommissioning,
                    terminalequipment_id=old.get("terminalequipment_id"),
                    date_of_commissioning=date_of_commissioning,
                    stored=stored,
                )

            log_change(record=obj, action="DMW_MAKE_CHANGE", old_data=old, new_data=new, user=request.user, remarks=remarks)
            messages.success(request, "DMW make change applied.")
            return redirect("transmedia:migrations_index")
    else:
        form = DmwMakeChangeForm()

    return render(request, "transmedia/migration_dmw_make_change.html", {"form": form})
