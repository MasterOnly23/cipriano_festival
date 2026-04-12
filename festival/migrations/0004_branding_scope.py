from django.db import migrations, models


def set_default_operator_branding(apps, schema_editor):
    Operator = apps.get_model("festival", "Operator")
    Operator.objects.filter(username="admin").update(branding="BOTH")
    Operator.objects.exclude(username="admin").update(branding="FESTIVAL")


class Migration(migrations.Migration):

    dependencies = [
        ("festival", "0003_waiter_scanevent_waiter"),
    ]

    operations = [
        migrations.AddField(
            model_name="batch",
            name="branding",
            field=models.CharField(
                choices=[("FESTIVAL", "Festival"), ("BURGERS", "Burgers")],
                db_index=True,
                default="FESTIVAL",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="operator",
            name="branding",
            field=models.CharField(
                choices=[("FESTIVAL", "Festival"), ("BURGERS", "Burgers"), ("BOTH", "Both")],
                db_index=True,
                default="FESTIVAL",
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="pizzaitem",
            name="branding",
            field=models.CharField(
                choices=[("FESTIVAL", "Festival"), ("BURGERS", "Burgers")],
                db_index=True,
                default="FESTIVAL",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="scanevent",
            name="branding",
            field=models.CharField(
                choices=[("FESTIVAL", "Festival"), ("BURGERS", "Burgers")],
                db_index=True,
                default="FESTIVAL",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="waiter",
            name="branding",
            field=models.CharField(
                choices=[("FESTIVAL", "Festival"), ("BURGERS", "Burgers")],
                db_index=True,
                default="FESTIVAL",
                max_length=10,
            ),
        ),
        migrations.RunPython(set_default_operator_branding, migrations.RunPython.noop),
    ]
