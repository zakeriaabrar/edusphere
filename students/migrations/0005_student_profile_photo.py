from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("students", "0004_restore_course"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="profile_photo",
            field=models.FileField(blank=True, null=True, upload_to="profile_photos/"),
        ),
    ]
