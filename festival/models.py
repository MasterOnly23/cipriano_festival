from django.db import models
from django.contrib.auth.hashers import check_password, make_password


class PizzaStatus(models.TextChoices):
    PREPARACION = "PREPARACION", "Preparacion"
    LISTA = "LISTA", "Lista"
    VENDIDA = "VENDIDA", "Vendida"
    CANCELADA = "CANCELADA", "Cancelada"
    MERMA = "MERMA", "Merma"


class RoleType(models.TextChoices):
    COCINA = "COCINA", "Cocina"
    VENTAS = "VENTAS", "Ventas"
    ADMIN = "ADMIN", "Admin"


class OperatorRole(models.TextChoices):
    KITCHEN = "KITCHEN", "Kitchen"
    SALES = "SALES", "Sales"
    BATCHES = "BATCHES", "Batches"
    ADMIN = "ADMIN", "Admin"


class Operator(models.Model):
    username = models.CharField(max_length=40, unique=True)
    pin_hash = models.CharField(max_length=128)
    role = models.CharField(max_length=12, choices=OperatorRole.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["username"]

    def set_pin(self, raw_pin: str) -> None:
        self.pin_hash = make_password(raw_pin)

    def check_pin(self, raw_pin: str) -> bool:
        if not self.pin_hash:
            return False
        return check_password(raw_pin, self.pin_hash)

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"


class Batch(models.Model):
    code = models.CharField(max_length=24, unique=True)
    day = models.DateField()
    notes = models.CharField(max_length=200, blank=True)
    created_by = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.code


class PizzaItem(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    flavor = models.CharField(max_length=40, blank=True)
    size = models.CharField(max_length=20, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    status = models.CharField(
        max_length=16,
        choices=PizzaStatus.choices,
        default=PizzaStatus.PREPARACION,
    )
    batch = models.ForeignKey(
        Batch, on_delete=models.SET_NULL, null=True, blank=True, related_name="pizzas"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    sold_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    created_by = models.CharField(max_length=80, blank=True)
    ready_by = models.CharField(max_length=80, blank=True)
    sold_by = models.CharField(max_length=80, blank=True)
    canceled_by = models.CharField(max_length=80, blank=True)

    def __str__(self) -> str:
        return self.id


class ScanEvent(models.Model):
    pizza = models.ForeignKey(PizzaItem, on_delete=models.CASCADE, related_name="events")
    mode = models.CharField(max_length=20)
    actor_name = models.CharField(max_length=80, blank=True)
    actor_role = models.CharField(max_length=16, choices=RoleType.choices)
    from_status = models.CharField(max_length=16, choices=PizzaStatus.choices)
    to_status = models.CharField(max_length=16, choices=PizzaStatus.choices)
    note = models.CharField(max_length=200, blank=True)
    undone = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.pizza_id}: {self.from_status}->{self.to_status}"
