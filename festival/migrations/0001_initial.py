from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Batch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=24, unique=True)),
                ("day", models.DateField()),
                ("notes", models.CharField(blank=True, max_length=200)),
                ("created_by", models.CharField(blank=True, max_length=80)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="PizzaItem",
            fields=[
                ("id", models.CharField(max_length=32, primary_key=True, serialize=False)),
                ("flavor", models.CharField(blank=True, max_length=40)),
                ("size", models.CharField(blank=True, max_length=20)),
                ("price", models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PREPARACION", "Preparacion"),
                            ("LISTA", "Lista"),
                            ("VENDIDA", "Vendida"),
                            ("CANCELADA", "Cancelada"),
                            ("MERMA", "Merma"),
                        ],
                        default="PREPARACION",
                        max_length=16,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("ready_at", models.DateTimeField(blank=True, null=True)),
                ("sold_at", models.DateTimeField(blank=True, null=True)),
                ("canceled_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.CharField(blank=True, max_length=80)),
                ("ready_by", models.CharField(blank=True, max_length=80)),
                ("sold_by", models.CharField(blank=True, max_length=80)),
                ("canceled_by", models.CharField(blank=True, max_length=80)),
                (
                    "batch",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="pizzas",
                        to="festival.batch",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ScanEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("mode", models.CharField(max_length=20)),
                ("actor_name", models.CharField(blank=True, max_length=80)),
                (
                    "actor_role",
                    models.CharField(
                        choices=[("COCINA", "Cocina"), ("VENTAS", "Ventas"), ("ADMIN", "Admin")],
                        max_length=16,
                    ),
                ),
                (
                    "from_status",
                    models.CharField(
                        choices=[
                            ("PREPARACION", "Preparacion"),
                            ("LISTA", "Lista"),
                            ("VENDIDA", "Vendida"),
                            ("CANCELADA", "Cancelada"),
                            ("MERMA", "Merma"),
                        ],
                        max_length=16,
                    ),
                ),
                (
                    "to_status",
                    models.CharField(
                        choices=[
                            ("PREPARACION", "Preparacion"),
                            ("LISTA", "Lista"),
                            ("VENDIDA", "Vendida"),
                            ("CANCELADA", "Cancelada"),
                            ("MERMA", "Merma"),
                        ],
                        max_length=16,
                    ),
                ),
                ("note", models.CharField(blank=True, max_length=200)),
                ("undone", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("pizza", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="festival.pizzaitem")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
