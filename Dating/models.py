from django.db import models

# Create your models here.

class Looking_for(models.Model):
    looking_for_type = models.CharField(max_length=255)

class Interests(models.Model):
    interest_name = models.CharField(max_length=255)
    interest_logo = models.CharField(max_length=255, null=True)

class User_Profile(models.Model):
    name = models.CharField(max_length=512)
    dob = models.DateField()
    gender = models.CharField(max_length=10)
    looking_for = models.CharField(max_length=255)
    bio = models.TextField()
    study_major = models.CharField(max_length=255, null=True)
    study_uni = models.CharField(max_length=255, null=True)
    work_position = models.CharField(max_length=255, null=True)
    company_name = models.CharField(max_length=255, null=True)
    height_ft = models.IntegerField(null=True)
    height_in = models.IntegerField(null=True)
    exercise = models.CharField(max_length=255, null=True)
    education_level = models.CharField(max_length=255, null=True)
    drinking = models.CharField(max_length=255, null=True)
    smoking = models.CharField(max_length=255, null=True)
    pets = models.CharField(max_length=255, null=True)
    fav_song = models.CharField(max_length=255, null=True)



