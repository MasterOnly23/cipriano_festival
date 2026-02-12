from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("festival", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Operator",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("username", models.CharField(max_length=40, unique=True)),
                ("pin_hash", models.CharField(max_length=128)),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("KITCHEN", "Kitchen"),
                            ("SALES", "Sales"),
                            ("BATCHES", "Batches"),
                            ("ADMIN", "Admin"),
                        ],
                        max_length=12,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["username"]},
        ),
    ]
