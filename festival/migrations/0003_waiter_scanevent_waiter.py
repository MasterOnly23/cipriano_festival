from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("festival", "0002_operator"),
    ]

    operations = [
        migrations.CreateModel(
            name="Waiter",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=24, unique=True)),
                ("name", models.CharField(max_length=80)),
                ("is_active", models.BooleanField(default=True)),
                ("created_by", models.CharField(blank=True, max_length=80)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["name", "code"]},
        ),
        migrations.AddField(
            model_name="scanevent",
            name="waiter_code",
            field=models.CharField(blank=True, max_length=24),
        ),
        migrations.AddField(
            model_name="scanevent",
            name="waiter_name",
            field=models.CharField(blank=True, max_length=80),
        ),
    ]
