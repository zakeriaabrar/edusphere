from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('students', '0003_usersettings_delete_course'),
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_code', models.CharField(max_length=20, unique=True)),
                ('course_name', models.CharField(max_length=100)),
                ('credit', models.PositiveIntegerField(default=3)),
                ('department', models.CharField(max_length=100)),
                ('semester', models.CharField(max_length=30)),
                ('teacher_name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
