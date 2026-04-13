from rest_framework import serializers

from .models import Batch, Flavor, PizzaItem, ScanEvent, TransferRecord, Waiter


class BatchSerializer(serializers.ModelSerializer):
    total_items = serializers.IntegerField(read_only=True)
    first_item_id = serializers.CharField(read_only=True)
    last_item_id = serializers.CharField(read_only=True)

    class Meta:
        model = Batch
        fields = [
            "id",
            "code",
            "branding",
            "day",
            "notes",
            "created_by",
            "created_at",
            "total_items",
            "first_item_id",
            "last_item_id",
        ]


class PizzaItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PizzaItem
        fields = [
            "id",
            "flavor",
            "size",
            "price",
            "current_location",
            "sold_location",
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
            "from_location",
            "to_location",
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


class FlavorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flavor
        fields = ["id", "branding", "name", "prefix", "is_active", "sort_order", "created_at"]


class TransferRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransferRecord
        fields = [
            "id",
            "branding",
            "from_location",
            "to_location",
            "first_id",
            "last_id",
            "quantity",
            "created_by",
            "note",
            "created_at",
        ]
