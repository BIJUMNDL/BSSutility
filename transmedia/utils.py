from .models import MediaChangeLog


def snapshot(rec):
    return {
        "sl_no": rec.sl_no,
        "site_name": rec.site_name,
        "transmission_media": rec.transmission_media,
        "a_end": rec.a_end,
        "b_end": rec.b_end,
        "terminal_equipment_type": rec.terminal_equipment_type,
        "make": rec.make,
        "terminalequipment_id": rec.terminalequipment_id,
        "cluster": rec.cluster,
        "port_2g": rec.port_2g,
        "port_3g": rec.port_3g,
        "port_4g": rec.port_4g,
    }


def log_change(*, record, action, old_data, new_data, user=None, remarks=None):
    MediaChangeLog.objects.create(
        record=record,
        site_name=record.site_name,
        action=action,
        old_data=old_data,
        new_data=new_data,
        changed_by=user,
        remarks=remarks,
    )