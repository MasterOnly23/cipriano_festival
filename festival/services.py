from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from .models import Batch, Flavor, LocationType, PizzaItem, PizzaStatus, RoleType, ScanEvent, TransferRecord, Waiter


class TransitionError(Exception):
    pass


@dataclass
class Actor:
    name: str
    role: str
    location: str = LocationType.MAIN


def _set_transition_fields(item: PizzaItem, to_status: str, actor_name: str) -> None:
    now = timezone.now()
    if to_status == PizzaStatus.LISTA:
        item.ready_at = now
        item.ready_by = actor_name
    elif to_status == PizzaStatus.VENDIDA:
        item.sold_at = now
        item.sold_by = actor_name
    elif to_status in {PizzaStatus.CANCELADA, PizzaStatus.MERMA}:
        item.canceled_at = now
        item.canceled_by = actor_name


def _create_event(
    *,
    item: PizzaItem,
    actor: Actor,
    from_status: str,
    to_status: str,
    mode: str,
    waiter_code: str = "",
    waiter_name: str = "",
    note: str = "",
    from_location: str = "",
    to_location: str = "",
) -> ScanEvent:
    return ScanEvent.objects.create(
        pizza=item,
        branding=item.branding,
        mode=mode,
        actor_name=actor.name,
        actor_role=actor.role,
        from_location=from_location,
        to_location=to_location,
        from_status=from_status,
        to_status=to_status,
        waiter_code=waiter_code,
        waiter_name=waiter_name,
        note=note,
    )


@transaction.atomic
def process_scan(
    *,
    pizza_id: str,
    mode: str,
    actor: Actor,
    flavor_if_empty: str = "",
    override_pin: str = "",
    waiter_code: str = "",
    branding: str = "FESTIVAL",
) -> tuple[PizzaItem, ScanEvent]:
    try:
        item = PizzaItem.objects.select_for_update().get(pk=pizza_id, branding=branding)
    except PizzaItem.DoesNotExist as exc:
        raise TransitionError(f"ID no encontrado: {pizza_id}") from exc

    from_status = item.status
    from_location = item.current_location
    mode = mode.upper()

    if flavor_if_empty and not item.flavor:
        item.flavor = flavor_if_empty.strip().upper()

    if mode == "KITCHEN":
        if actor.location not in {LocationType.MAIN, LocationType.BOTH}:
            raise TransitionError("Solo el local principal puede marcar produccion")
        if item.status == PizzaStatus.PREPARACION:
            item.status = PizzaStatus.LISTA
        elif item.status == PizzaStatus.LISTA:
            pass
        else:
            raise TransitionError(f"No se puede pasar a LISTA desde {item.status}")
    elif mode == "SALES":
        waiter = None
        waiter_code = waiter_code.strip().upper()
        if not waiter_code:
            raise TransitionError("Debes escanear primero el QR del mesero")
        try:
            waiter = Waiter.objects.get(code=waiter_code, is_active=True, branding=branding)
        except Waiter.DoesNotExist as exc:
            raise TransitionError(f"Mesero no encontrado o inactivo: {waiter_code}") from exc
        if actor.location not in {LocationType.BOTH, item.current_location}:
            raise TransitionError("Este usuario no puede vender pizzas de ese local")

        if item.status == PizzaStatus.LISTA:
            item.status = PizzaStatus.VENDIDA
        elif override_pin == settings.ADMIN_OVERRIDE_PIN:
            item.status = PizzaStatus.VENDIDA
        else:
            raise TransitionError("Solo se puede vender una pizza en estado LISTA")
    else:
        raise TransitionError(f"Modo invalido: {mode}")

    _set_transition_fields(item, item.status, actor.name)
    if mode == "SALES" and waiter:
        item.sold_by = waiter.name
        item.sold_location = item.current_location
    item.save()
    event = _create_event(
        item=item,
        actor=actor,
        from_location=from_location,
        to_location=item.current_location,
        from_status=from_status,
        to_status=item.status,
        mode=mode,
        waiter_code=waiter.code if mode == "SALES" else "",
        waiter_name=waiter.name if mode == "SALES" else "",
        note="override" if override_pin == settings.ADMIN_OVERRIDE_PIN else "",
    )
    return item, event


@transaction.atomic
def admin_set_status(
    *,
    pizza_id: str,
    to_status: str,
    actor: Actor,
    pin: str,
    branding: str = "FESTIVAL",
) -> tuple[PizzaItem, ScanEvent]:
    if pin != settings.ADMIN_ACTIONS_PIN:
        raise TransitionError("PIN admin invalido")

    if to_status not in {PizzaStatus.CANCELADA, PizzaStatus.MERMA}:
        raise TransitionError("Estado admin invalido")

    try:
        item = PizzaItem.objects.select_for_update().get(pk=pizza_id, branding=branding)
    except PizzaItem.DoesNotExist as exc:
        raise TransitionError(f"ID no encontrado: {pizza_id}") from exc

    from_status = item.status
    from_location = item.current_location
    item.status = to_status
    if to_status != PizzaStatus.VENDIDA:
        item.sold_location = ""
    _set_transition_fields(item, to_status, actor.name)
    item.save()
    event = _create_event(
        item=item,
        actor=actor,
        from_location=from_location,
        to_location=item.current_location,
        from_status=from_status,
        to_status=to_status,
        mode="ADMIN",
    )
    return item, event


@transaction.atomic
def undo_last(*, pin: str, actor: Actor, branding: str = "FESTIVAL") -> tuple[PizzaItem, ScanEvent]:
    if pin != settings.ADMIN_ACTIONS_PIN:
        raise TransitionError("PIN admin invalido")

    last = ScanEvent.objects.select_for_update().filter(undone=False, branding=branding).first()
    if not last:
        raise TransitionError("No hay eventos para deshacer")

    item = PizzaItem.objects.select_for_update().get(pk=last.pizza_id, branding=branding)
    item.status = last.from_status
    if last.from_location:
        item.current_location = last.from_location
    if item.status != PizzaStatus.VENDIDA:
        item.sold_location = ""
    _set_transition_fields(item, item.status, actor.name)
    item.save()

    last.undone = True
    last.save(update_fields=["undone"])

    rollback = _create_event(
        item=item,
        actor=actor,
        from_location=last.to_location,
        to_location=last.from_location,
        from_status=last.to_status,
        to_status=last.from_status,
        mode="UNDO",
        note=f"Deshace evento #{last.id}",
    )
    return item, rollback


@transaction.atomic
def create_batch(
    *,
    day_code: str,
    flavor_prefix: str,
    flavor: str,
    quantity: int,
    price: Decimal,
    size: str,
    actor_name: str,
    start_number: Optional[int] = None,
    notes: str = "",
    branding: str = "FESTIVAL",
) -> tuple[Batch, list[PizzaItem]]:
    prefix = flavor_prefix.strip().upper()
    day_code = day_code.strip().upper()
    batch_code = f"{day_code}-{prefix}" if day_code else prefix

    batch, _ = Batch.objects.get_or_create(
        code=batch_code,
        defaults={
            "branding": branding,
            "day": timezone.localdate(),
            "notes": notes,
            "created_by": actor_name,
        },
    )
    if batch.branding != branding:
        raise TransitionError(f"El lote {batch_code} ya existe para otro branding")

    if start_number is None:
        last_id = (
            PizzaItem.objects.filter(id__startswith=f"{batch_code}-", branding=branding)
            .aggregate(last=Max("id"))
            .get("last")
        )
        if last_id and last_id.rsplit("-", 1)[-1].isdigit():
            start_number = int(last_id.rsplit("-", 1)[-1]) + 1
        else:
            start_number = 1

    created: list[PizzaItem] = []
    for n in range(start_number, start_number + quantity):
        code = f"{batch_code}-{n:04d}"
        item = PizzaItem(
            id=code,
            branding=branding,
            flavor=flavor.strip().upper(),
            size=size.strip().upper(),
            price=price,
            current_location=LocationType.MAIN,
            status=PizzaStatus.PREPARACION,
            batch=batch,
            created_by=actor_name,
        )
        item.save()
        created.append(item)

    return batch, created


@transaction.atomic
def create_waiter(*, name: str, actor_name: str, branding: str = "FESTIVAL") -> Waiter:
    cleaned = (name or "").strip().upper()
    if not cleaned:
        raise TransitionError("Nombre de mesero requerido")

    next_number = 1
    for existing_code in Waiter.objects.filter(branding=branding).values_list("code", flat=True):
        raw_code = (existing_code or "").strip().upper()
        numeric_part = raw_code
        if raw_code.startswith("W-"):
            numeric_part = raw_code.rsplit("-", 1)[-1]
        if numeric_part.isdigit():
            next_number = max(next_number, int(numeric_part) + 1)
    code = f"{next_number:04d}"
    return Waiter.objects.create(code=code, name=cleaned, created_by=actor_name, branding=branding)


@transaction.atomic
def create_flavor(*, name: str, prefix: str, actor_name: str, branding: str = "FESTIVAL") -> Flavor:
    cleaned_name = (name or "").strip().upper()
    cleaned_prefix = (prefix or "").strip().upper()
    if not cleaned_name:
        raise TransitionError("Nombre de sabor requerido")
    if not cleaned_prefix or not cleaned_prefix.isalnum():
        raise TransitionError("Prefijo invalido")
    if Flavor.objects.filter(branding=branding, name=cleaned_name).exists():
        raise TransitionError("Ese sabor ya existe")
    if Flavor.objects.filter(branding=branding, prefix=cleaned_prefix).exists():
        raise TransitionError("Ese prefijo ya existe")
    next_order = (Flavor.objects.filter(branding=branding).aggregate(last=Max("sort_order")).get("last") or 0) + 10
    return Flavor.objects.create(
        branding=branding,
        name=cleaned_name,
        prefix=cleaned_prefix,
        is_active=True,
        sort_order=next_order,
        created_by=actor_name,
    )


@transaction.atomic
def update_flavor(
    *,
    flavor_id: int,
    name: str,
    prefix: str,
    actor_name: str,
    branding: str = "FESTIVAL",
) -> Flavor:
    cleaned_name = (name or "").strip().upper()
    cleaned_prefix = (prefix or "").strip().upper()
    if not cleaned_name:
        raise TransitionError("Nombre de sabor requerido")
    if not cleaned_prefix or not cleaned_prefix.isalnum():
        raise TransitionError("Prefijo invalido")
    try:
        flavor = Flavor.objects.select_for_update().get(pk=flavor_id, branding=branding)
    except Flavor.DoesNotExist as exc:
        raise TransitionError("Sabor no encontrado") from exc
    if Flavor.objects.filter(branding=branding, name=cleaned_name).exclude(pk=flavor.pk).exists():
        raise TransitionError("Ese sabor ya existe")
    if Flavor.objects.filter(branding=branding, prefix=cleaned_prefix).exclude(pk=flavor.pk).exists():
        raise TransitionError("Ese prefijo ya existe")
    flavor.name = cleaned_name
    flavor.prefix = cleaned_prefix
    flavor.created_by = actor_name
    flavor.save(update_fields=["name", "prefix", "created_by"])
    return flavor


@transaction.atomic
def deactivate_flavor(*, flavor_id: int, actor_name: str, branding: str = "FESTIVAL") -> Flavor:
    try:
        flavor = Flavor.objects.select_for_update().get(pk=flavor_id, branding=branding)
    except Flavor.DoesNotExist as exc:
        raise TransitionError("Sabor no encontrado") from exc
    flavor.is_active = False
    flavor.created_by = actor_name
    flavor.save(update_fields=["is_active", "created_by"])
    return flavor


@transaction.atomic
def reactivate_flavor(*, flavor_id: int, actor_name: str, branding: str = "FESTIVAL") -> Flavor:
    try:
        flavor = Flavor.objects.select_for_update().get(pk=flavor_id, branding=branding)
    except Flavor.DoesNotExist as exc:
        raise TransitionError("Sabor no encontrado") from exc
    flavor.is_active = True
    flavor.created_by = actor_name
    flavor.save(update_fields=["is_active", "created_by"])
    return flavor


@transaction.atomic
def delete_flavor(*, flavor_id: int, branding: str = "FESTIVAL") -> None:
    try:
        flavor = Flavor.objects.select_for_update().get(pk=flavor_id, branding=branding)
    except Flavor.DoesNotExist as exc:
        raise TransitionError("Sabor no encontrado") from exc
    flavor.delete()


def _parse_batch_range(start_id: str, end_id: str) -> tuple[str, int, int]:
    start = (start_id or "").strip().upper()
    end = (end_id or "").strip().upper()
    if not start or not end:
        raise TransitionError("IDs inicial y final requeridos")
    try:
        start_base, start_num = start.rsplit("-", 1)
        end_base, end_num = end.rsplit("-", 1)
    except ValueError as exc:
        raise TransitionError("Formato de ID invalido") from exc
    if start_base != end_base:
        raise TransitionError("Los IDs deben pertenecer al mismo lote/prefijo")
    if not start_num.isdigit() or not end_num.isdigit():
        raise TransitionError("Los IDs deben terminar en numero")
    start_n = int(start_num)
    end_n = int(end_num)
    if start_n > end_n:
        raise TransitionError("El ID inicial no puede ser mayor que el final")
    return start_base, start_n, end_n


@transaction.atomic
def bulk_mark_ready(*, start_id: str, end_id: str, actor: Actor, branding: str = "FESTIVAL") -> tuple[int, str, str]:
    if actor.location not in {LocationType.MAIN, LocationType.BOTH}:
        raise TransitionError("Solo el local principal puede marcar produccion")
    base, start_n, end_n = _parse_batch_range(start_id, end_id)
    count = 0
    first_done = ""
    last_done = ""
    event_ids: list[int] = []
    for number in range(start_n, end_n + 1):
        pizza_id = f"{base}-{number:04d}"
        item, event = process_scan(pizza_id=pizza_id, mode="KITCHEN", actor=actor, branding=branding)
        count += 1
        event_ids.append(event.id)
        if not first_done:
            first_done = item.id
        last_done = item.id
    if event_ids:
        bulk_note = f"bulk-ready|{first_done}|{last_done}|{count}"
        ScanEvent.objects.filter(id__in=event_ids).update(note=bulk_note)
    return count, first_done, last_done


@transaction.atomic
def transfer_items_to_secondary(
    *,
    start_id: str,
    end_id: str,
    actor: Actor,
    branding: str = "FESTIVAL",
    note: str = "",
) -> tuple[TransferRecord, int]:
    return transfer_items_between_locations(
        start_id=start_id,
        end_id=end_id,
        actor=actor,
        branding=branding,
        note=note,
        from_location=LocationType.MAIN,
        to_location=LocationType.SECONDARY,
    )


@transaction.atomic
def return_items_to_main(
    *,
    start_id: str,
    end_id: str,
    actor: Actor,
    branding: str = "FESTIVAL",
    note: str = "",
) -> tuple[TransferRecord, int]:
    return transfer_items_between_locations(
        start_id=start_id,
        end_id=end_id,
        actor=actor,
        branding=branding,
        note=note,
        from_location=LocationType.SECONDARY,
        to_location=LocationType.MAIN,
    )


@transaction.atomic
def transfer_items_between_locations(
    *,
    start_id: str,
    end_id: str,
    actor: Actor,
    branding: str = "FESTIVAL",
    note: str = "",
    from_location: str,
    to_location: str,
) -> tuple[TransferRecord, int]:
    base, start_n, end_n = _parse_batch_range(start_id, end_id)
    transferred = 0
    first_id = f"{base}-{start_n:04d}"
    last_id = f"{base}-{end_n:04d}"
    event_ids: list[int] = []
    for number in range(start_n, end_n + 1):
        pizza_id = f"{base}-{number:04d}"
        try:
            item = PizzaItem.objects.select_for_update().get(pk=pizza_id, branding=branding)
        except PizzaItem.DoesNotExist as exc:
            raise TransitionError(f"ID no encontrado: {pizza_id}") from exc
        if item.current_location != from_location:
            expected_label = "local principal" if from_location == LocationType.MAIN else "local secundario"
            raise TransitionError(f"{pizza_id} no esta en el {expected_label}")
        if item.status != PizzaStatus.LISTA:
            raise TransitionError(f"{pizza_id} debe estar LISTA para mover entre locales")
        item.current_location = to_location
        item.save(update_fields=["current_location"])
        event = _create_event(
            item=item,
            actor=actor,
            from_location=from_location,
            to_location=to_location,
            from_status=item.status,
            to_status=item.status,
            mode="TRANSFER",
            note=(note or "").strip(),
        )
        event_ids.append(event.id)
        transferred += 1
    if event_ids:
        bulk_note = f"transfer-range|{from_location}|{to_location}|{first_id}|{last_id}|{transferred}"
        if note:
            bulk_note = f"{bulk_note}|{note.strip()}"
        ScanEvent.objects.filter(id__in=event_ids).update(note=bulk_note)
    transfer = TransferRecord.objects.create(
        branding=branding,
        from_location=from_location,
        to_location=to_location,
        first_id=first_id,
        last_id=last_id,
        quantity=transferred,
        created_by=actor.name,
        note=(note or "").strip(),
    )
    return transfer, transferred
