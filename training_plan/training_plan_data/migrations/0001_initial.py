# Generated by Django 2.2.28 on 2025-04-07 17:31

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SheetData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.CharField(max_length=20)),
                ('date', models.DateField()),
                ('time_session_1', models.CharField(blank=True, max_length=50, null=True)),
                ('session_1', models.TextField(blank=True, null=True)),
                ('time_session_2', models.CharField(blank=True, max_length=50, null=True)),
                ('session_2', models.TextField(blank=True, null=True)),
            ],
        ),
    ]
