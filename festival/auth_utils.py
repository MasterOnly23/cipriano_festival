from functools import wraps
from typing import Iterable

from django.conf import settings
from django.shortcuts import redirect

from .models import BrandingType, Operator, OperatorRole


ROLE_LABEL_MAP = {
    OperatorRole.KITCHEN: "COCINA",
    OperatorRole.SALES: "VENTAS",
    OperatorRole.BATCHES: "ADMIN",
    OperatorRole.ADMIN: "ADMIN",
}


def bootstrap_default_operators() -> None:
    defaults = [
        ("cocina", OperatorRole.KITCHEN, settings.DEFAULT_FESTIVAL_KITCHEN_PIN, BrandingType.FESTIVAL),
        ("ventas", OperatorRole.SALES, settings.DEFAULT_FESTIVAL_SALES_PIN, BrandingType.FESTIVAL),
        ("lotes", OperatorRole.BATCHES, settings.DEFAULT_FESTIVAL_BATCHES_PIN, BrandingType.FESTIVAL),
        ("cocinaburger", OperatorRole.KITCHEN, settings.DEFAULT_BURGERS_KITCHEN_PIN, BrandingType.BURGERS),
        ("ventasburger", OperatorRole.SALES, settings.DEFAULT_BURGERS_SALES_PIN, BrandingType.BURGERS),
        ("lotesburger", OperatorRole.BATCHES, settings.DEFAULT_BURGERS_BATCHES_PIN, BrandingType.BURGERS),
        ("admin", OperatorRole.ADMIN, settings.DEFAULT_ADMIN_LOGIN_PIN, BrandingType.BOTH),
    ]
    for username, role, pin, branding in defaults:
        op, created = Operator.objects.get_or_create(
            username=username,
            defaults={"role": role, "branding": branding, "is_active": True},
        )
        updated_fields = []
        if op.role != role:
            op.role = role
            updated_fields.append("role")
        if op.branding != branding:
            op.branding = branding
            updated_fields.append("branding")
        if not op.is_active:
            op.is_active = True
            updated_fields.append("is_active")
        if created or not op.pin_hash:
            op.set_pin(pin)
            updated_fields.append("pin_hash")
        if updated_fields:
            op.save(update_fields=updated_fields)


def get_current_operator(request):
    operator_id = request.session.get("operator_id")
    if not operator_id:
        return None
    try:
        return Operator.objects.get(pk=operator_id, is_active=True)
    except Operator.DoesNotExist:
        return None


def login_operator(request, operator: Operator) -> None:
    request.session["operator_id"] = operator.id
    request.session["operator_username"] = operator.username
    request.session["operator_role"] = operator.role
    request.session["operator_branding"] = operator.branding
    if operator.branding in {BrandingType.FESTIVAL, BrandingType.BURGERS}:
        request.session["active_branding"] = operator.branding
    else:
        request.session.setdefault("active_branding", BrandingType.FESTIVAL)
    request.session.set_expiry(settings.AUTH_SESSION_MINUTES * 60)


def get_allowed_brandings(operator: Operator) -> list[str]:
    if operator.branding == BrandingType.BOTH:
        return [BrandingType.FESTIVAL, BrandingType.BURGERS]
    return [operator.branding]


def get_active_branding(request) -> str | None:
    operator = get_current_operator(request)
    if not operator:
        return None
    allowed = get_allowed_brandings(operator)
    current = (request.session.get("active_branding") or "").upper()
    if current not in allowed:
        current = allowed[0]
        request.session["active_branding"] = current
    return current


def logout_operator(request) -> None:
    request.session.flush()


def require_roles_web(roles: Iterable[str]):
    role_set = set(roles)

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            operator = get_current_operator(request)
            if not operator:
                return redirect(f"/login/?next={request.path}")
            if operator.role not in role_set:
                return redirect("/login/?denied=1")
            if not get_active_branding(request):
                return redirect(f"/branding/select?next={request.path}")
            request.current_operator = operator
            request.current_branding = request.session.get("active_branding")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


def require_roles_api(request, roles: Iterable[str]):
    role_set = set(roles)
    operator = get_current_operator(request)
    if not operator:
        return None, {"ok": False, "error": "No autenticado"}, 401
    if operator.role not in role_set:
        return None, {"ok": False, "error": "No autorizado"}, 403
    branding = get_active_branding(request)
    if not branding:
        return None, {"ok": False, "error": "Branding no seleccionado"}, 400
    return operator, None, None
