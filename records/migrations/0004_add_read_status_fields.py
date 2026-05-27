from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0003_add_upload_deadline_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='record',
            name='is_read_by_landlord',
            field=models.BooleanField(default=False, verbose_name='임대인 읽음'),
        ),
        migrations.AddField(
            model_name='record',
            name='is_read_by_tenant',
            field=models.BooleanField(default=False, verbose_name='임차인 읽음'),
        ),
    ]
