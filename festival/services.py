from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from .models import Batch, PizzaItem, PizzaStatus, RoleType, ScanEvent


class TransitionError(Exception):
    pass


@dataclass
class Actor:
    name: str
    role: str


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
    note: str = "",
) -> ScanEvent:
    return ScanEvent.objects.create(
        pizza=item,
        mode=mode,
        actor_name=actor.name,
        actor_role=actor.role,
        from_status=from_status,
        to_status=to_status,
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
) -> tuple[PizzaItem, ScanEvent]:
    try:
        item = PizzaItem.objects.select_for_update().get(pk=pizza_id)
    except PizzaItem.DoesNotExist as exc:
        raise TransitionError(f"ID no encontrado: {pizza_id}") from exc

    from_status = item.status
    mode = mode.upper()

    if flavor_if_empty and not item.flavor:
        item.flavor = flavor_if_empty.strip().upper()

    if mode == "KITCHEN":
        if item.status == PizzaStatus.PREPARACION:
            item.status = PizzaStatus.LISTA
        elif item.status == PizzaStatus.LISTA:
            pass
        else:
            raise TransitionError(f"No se puede pasar a LISTA desde {item.status}")
    elif mode == "SALES":
        if item.status == PizzaStatus.LISTA:
            item.status = PizzaStatus.VENDIDA
        elif override_pin == settings.ADMIN_OVERRIDE_PIN:
            item.status = PizzaStatus.VENDIDA
        else:
            raise TransitionError("Solo se puede vender una pizza en estado LISTA")
    else:
        raise TransitionError(f"Modo invalido: {mode}")

    _set_transition_fields(item, item.status, actor.name)
    item.save()
    event = _create_event(
        item=item,
        actor=actor,
        from_status=from_status,
        to_status=item.status,
        mode=mode,
        note="override" if override_pin == settings.ADMIN_OVERRIDE_PIN else "",
    )
    return item, event


@transaction.atomic
def admin_set_status(*, pizza_id: str, to_status: str, actor: Actor, pin: str) -> tuple[PizzaItem, ScanEvent]:
    if pin != settings.ADMIN_ACTIONS_PIN:
        raise TransitionError("PIN admin invalido")

    if to_status not in {PizzaStatus.CANCELADA, PizzaStatus.MERMA}:
        raise TransitionError("Estado admin invalido")

    try:
        item = PizzaItem.objects.select_for_update().get(pk=pizza_id)
    except PizzaItem.DoesNotExist as exc:
        raise TransitionError(f"ID no encontrado: {pizza_id}") from exc

    from_status = item.status
    item.status = to_status
    _set_transition_fields(item, to_status, actor.name)
    item.save()
    event = _create_event(
        item=item,
        actor=actor,
        from_status=from_status,
        to_status=to_status,
        mode="ADMIN",
    )
    return item, event


@transaction.atomic
def undo_last(*, pin: str, actor: Actor) -> tuple[PizzaItem, ScanEvent]:
    if pin != settings.ADMIN_ACTIONS_PIN:
        raise TransitionError("PIN admin invalido")

    last = ScanEvent.objects.select_for_update().filter(undone=False).first()
    if not last:
        raise TransitionError("No hay eventos para deshacer")

    item = PizzaItem.objects.select_for_update().get(pk=last.pizza_id)
    item.status = last.from_status
    _set_transition_fields(item, item.status, actor.name)
    item.save()

    last.undone = True
    last.save(update_fields=["undone"])

    rollback = _create_event(
        item=item,
        actor=actor,
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
) -> tuple[Batch, list[PizzaItem]]:
    prefix = flavor_prefix.strip().upper()
    day_code = day_code.strip().upper()
    batch_code = f"{day_code}-{prefix}" if day_code else prefix

    batch, _ = Batch.objects.get_or_create(
        code=batch_code,
        defaults={"day": timezone.localdate(), "notes": notes, "created_by": actor_name},
    )

    if start_number is None:
        last_id = (
            PizzaItem.objects.filter(id__startswith=f"{batch_code}-")
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
            flavor=flavor.strip().upper(),
            size=size.strip().upper(),
            price=price,
            status=PizzaStatus.PREPARACION,
            batch=batch,
            created_by=actor_name,
        )
        item.save()
        created.append(item)

    return batch, created
