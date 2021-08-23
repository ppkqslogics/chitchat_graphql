from djongo import models

# Create your models here.
class Report(models.Model):
    report_type = models.CharField(max_length=255)

class Reported_info(models.Model):
    reported_user_id = models.CharField(max_length=255)
    report = models.CharField(max_length=255)
    reported_datetime = models.DateTimeField()
    report_text = models.TextField(null=True)

    class Meta:
        abstract = True

class Reported_Data(models.Model):
    user_id = models.CharField(max_length=255, primary_key=True)
    reported_info = models.ArrayField(model_container=Reported_info)

