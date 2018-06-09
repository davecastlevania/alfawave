# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os

from django.db import migrations, models
from funkwhale_api.common.utils import rename_file


def bind_jobs(apps, schema_editor):
    TrackFile = apps.get_model("music", "TrackFile")
    ImportJob = apps.get_model("music", "ImportJob")

    for job in ImportJob.objects.all().only("mbid"):
        f = TrackFile.objects.filter(track__mbid=job.mbid).first()
        if not f:
            print("No file for mbid {}".format(job.mbid))
            continue
        job.track_file = f
        job.save(update_fields=["track_file"])


def rewind(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [("music", "0014_importjob_track_file")]

    operations = [migrations.RunPython(bind_jobs, rewind)]
