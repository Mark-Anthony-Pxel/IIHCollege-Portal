# Generated by Django 5.1.2 on 2024-11-08 16:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website_portal', '0010_teacher_email_teacher_first_name_teacher_last_name_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnotherModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('teacher', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='teacher_profile', to='website_portal.teacher')),
            ],
        ),
    ]
