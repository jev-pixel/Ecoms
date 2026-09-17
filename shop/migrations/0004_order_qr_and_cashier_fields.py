# Adds the cashier/QR-checkout fields that shop/models.py's Order class
# now declares: payment_type, qr_token, confirmed_by.
#
# Before applying: run `python manage.py makemigrations shop --check --dry-run`
# first. If it reports "No changes detected," this file is correct as-is.
# If Django wants to generate its own migration for these same fields
# instead, use that one and delete this file — don't apply both.

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0003_notification'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_type',
            field=models.CharField(
                choices=[('cash', 'Cash at Counter'), ('online', 'Online Payment')],
                default='cash',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='qr_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name='order',
            name='confirmed_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='punched_orders',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
