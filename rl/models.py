from __future__ import unicode_literals

from django.db import models

class Parent(models.Model):
    sentence = models.CharField(max_length=255)
    input_id = models.IntegerField()
    last_positive_id = models.CharField(null=True,max_length=100)
    last_negative_id = models.CharField(null=True,max_length=100)

class Positive(models.Model):
    sentence = models.CharField(max_length=255)
    parent_id = models.IntegerField()
    positive_id = models.CharField(null=True,max_length=100)

class Negative(models.Model):
    sentence = models.CharField(max_length=255)
    parent_id = models.IntegerField()
    negative_id = models.CharField(null=True,max_length=100)