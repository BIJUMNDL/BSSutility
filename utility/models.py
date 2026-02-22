from django.db import models

# Create your models here.
from django.db import models

class Site(models.Model):
    site_name = models.CharField(max_length=200, unique=True, db_index=True)
    site_code = models.CharField(max_length=50, blank=True, null=True)
    bss_incharge_name = models.CharField(max_length=120, blank=True, null=True)
    bss_incharge_mobile = models.CharField(max_length=20, blank=True, null=True)
    technician_name = models.CharField(max_length=120, blank=True, null=True)
    technician_mobile = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.site_name


class Inspection(models.Model):
    DG_STATUS_CHOICES = [("auto","Auto"), ("manual","Manual"), ("faulty","Faulty")]
    CLEAN_CHOICES = [("good","Good"), ("average","Average"), ("poor","Poor")]
    COND_CHOICES = [("working","Working"), ("not_working","Not Working"), ("not_available","Not Available")]

    inspection_date = models.DateField()
    site = models.ForeignKey(Site, on_delete=models.PROTECT, related_name="inspections")

    eb_reading = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    dg_kwh_reading = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    hour_meter_reading = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    dg_status = models.CharField(max_length=10, choices=DG_STATUS_CHOICES, null=True, blank=True)
    dg_remarks = models.TextField(blank=True, null=True)

    dc_load_kw = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    powerplant_max_modules = models.IntegerField(null=True, blank=True)
    modules_total =  models.IntegerField(null=True, blank=True)
    modules_working = models.IntegerField(null=True, blank=True)
    modules_faulty =  models.IntegerField(null=True, blank=True)
    modules_spare =  models.IntegerField(null=True, blank=True)
    
    battery_backup_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    discharge_test_conducted = models.BooleanField(null=True, blank=True)

    cleanliness_of_battery = models.CharField(max_length=10, choices=CLEAN_CHOICES, null=True, blank=True)
    aviation_lamp_condition = models.CharField(max_length=20, choices=COND_CHOICES, null=True, blank=True)
    fire_extinguisher_condition = models.CharField(max_length=20, choices=COND_CHOICES, null=True, blank=True)
    aircondition_status = models.CharField(max_length=20, choices=COND_CHOICES, null=True, blank=True)
    free_cooling_status = models.CharField(max_length=20, choices=COND_CHOICES, null=True, blank=True)
    overall_site_cleanliness = models.CharField(max_length=10, choices=CLEAN_CHOICES, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


class DieselFilling(models.Model):
    date_of_filling = models.DateField()
    site = models.ForeignKey(Site, on_delete=models.PROTECT, related_name="diesel_fillings")

    balance_on_tank = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    diesel_filled = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hour_meter_reading = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    kwh = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    balance_after_filling = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)