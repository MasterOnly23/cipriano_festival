from rest_framework import serializers

from .models import PizzaItem, ScanEvent, Waiter


class PizzaItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PizzaItem
        fields = [
            "id",
            "flavor",
            "size",
            "price",
            "status",
            "created_at",
            "ready_at",
            "sold_at",
        ]


class ScanEventSerializer(serializers.ModelSerializer):
    pizza_id = serializers.CharField(source="pizza.id")

    class Meta:
        model = ScanEvent
        fields = [
            "id",
            "pizza_id",
            "mode",
            "actor_name",
            "actor_role",
            "from_status",
            "to_status",
            "waiter_code",
            "waiter_name",
            "note",
            "created_at",
            "undone",
        ]


class WaiterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Waiter
        fields = ["id", "code", "name", "is_active", "created_at"]
