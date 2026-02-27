from django.contrib import admin

from .models import Batch, Operator, PizzaItem, ScanEvent, Waiter


@admin.register(PizzaItem)
class PizzaItemAdmin(admin.ModelAdmin):
    list_display = ("id", "flavor", "price", "status", "batch", "created_at")
    search_fields = ("id", "flavor")
    list_filter = ("status", "flavor", "batch")


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("code", "day", "created_by", "created_at")
    search_fields = ("code",)


@admin.register(ScanEvent)
class ScanEventAdmin(admin.ModelAdmin):
    list_display = ("id", "pizza", "from_status", "to_status", "mode", "actor_name", "created_at", "undone")
    list_filter = ("to_status", "mode", "actor_role", "undone")
    search_fields = ("pizza__id", "actor_name")


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ("username", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("username",)


@admin.register(Waiter)
class WaiterAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "created_by", "created_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
