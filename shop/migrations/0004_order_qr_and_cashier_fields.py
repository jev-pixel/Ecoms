# Generated for the cashier / QR-code checkout feature
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
            name='qr_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
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
