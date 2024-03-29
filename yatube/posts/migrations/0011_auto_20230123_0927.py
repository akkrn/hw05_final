# Generated by Django 2.2.16 on 2023-01-23 06:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("posts", "0010_auto_20230123_0912"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="follow",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="follow",
            constraint=models.UniqueConstraint(
                fields=("user", "author"), name="unique_following"
            ),
        ),
    ]
