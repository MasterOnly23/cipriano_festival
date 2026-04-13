from django.contrib import admin

from .models import Batch, Flavor, Operator, PizzaItem, ScanEvent, TransferRecord, Waiter


@admin.register(PizzaItem)
class PizzaItemAdmin(admin.ModelAdmin):
    list_display = ("id", "flavor", "current_location", "sold_location", "price", "status", "batch", "created_at")
    search_fields = ("id", "flavor")
    list_filter = ("status", "current_location", "sold_location", "flavor", "batch")


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("code", "branding", "day", "created_by", "created_at")
    search_fields = ("code",)
    list_filter = ("branding",)


@admin.register(ScanEvent)
class ScanEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "pizza",
        "mode",
        "from_location",
        "to_location",
        "from_status",
        "to_status",
        "actor_name",
        "created_at",
        "undone",
    )
    list_filter = ("branding", "to_status", "mode", "actor_role", "to_location", "undone")
    search_fields = ("pizza__id", "actor_name")


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ("username", "role", "branding", "location", "is_active", "created_at")
    list_filter = ("role", "branding", "location", "is_active")
    search_fields = ("username",)


@admin.register(Waiter)
class WaiterAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "branding", "is_active", "created_by", "created_at")
    list_filter = ("branding", "is_active")
    search_fields = ("code", "name")


@admin.register(Flavor)
class FlavorAdmin(admin.ModelAdmin):
    list_display = ("name", "prefix", "branding", "sort_order", "is_active", "created_by", "created_at")
    list_filter = ("branding", "is_active")
    search_fields = ("name", "prefix")
    ordering = ("branding", "sort_order", "name")


@admin.register(TransferRecord)
class TransferRecordAdmin(admin.ModelAdmin):
    list_display = ("branding", "first_id", "last_id", "quantity", "from_location", "to_location", "created_by", "created_at")
    list_filter = ("branding", "from_location", "to_location")
    search_fields = ("first_id", "last_id", "created_by")
