from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='gemini_api_key_1',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='gemini_api_key_2',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='gemini_api_key_3',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='gemini_api_key_4',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]

