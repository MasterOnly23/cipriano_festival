from functools import wraps
from typing import Iterable

from django.conf import settings
from django.shortcuts import redirect

from .models import BrandingType, Flavor, LocationType, Operator, OperatorRole


ROLE_LABEL_MAP = {
    OperatorRole.KITCHEN: "COCINA",
    OperatorRole.SALES: "VENTAS",
    OperatorRole.BATCHES: "LOTES",
    OperatorRole.OPERATOR: "OPERADOR",
    OperatorRole.SOCIO: "SOCIO",
    OperatorRole.ADMIN: "ADMIN",
}


def bootstrap_default_operators() -> None:
    username_renames = {
        "cipriano_cajalocal": "ciprianocajalocal",
        "cipriano_cajaoperacion": "ciprianocajaoperacion",
        "cipriano_administrador": "ciprianoadministrador",
        "cipriano_operador": "ciprianooperador",
        "cipriano_socio": "ciprianosocio",
        "don_cajalocal": "doncajalocal",
        "don_cajaoperacion": "doncajaoperacion",
        "don_administrador": "donadministrador",
        "don_operador": "donoperador",
        "don_socio": "donsocio",
    }
    for old_username, new_username in username_renames.items():
        if Operator.objects.filter(username=new_username).exists():
            continue
        try:
            op = Operator.objects.get(username=old_username)
        except Operator.DoesNotExist:
            continue
        op.username = new_username
        op.save(update_fields=["username"])

    defaults = [
        (
            "cocina",
            OperatorRole.KITCHEN,
            settings.DEFAULT_FESTIVAL_KITCHEN_PIN,
            BrandingType.FESTIVAL,
            LocationType.MAIN,
        ),
        (
            "ventas",
            OperatorRole.SALES,
            settings.DEFAULT_FESTIVAL_SALES_PIN,
            BrandingType.FESTIVAL,
            LocationType.MAIN,
        ),
        (
            "ventassec",
            OperatorRole.SALES,
            settings.DEFAULT_FESTIVAL_SECONDARY_SALES_PIN,
            BrandingType.FESTIVAL,
            LocationType.SECONDARY,
        ),
        (
            "ciprianocajalocal",
            OperatorRole.SALES,
            settings.DEFAULT_CIPRIANO_CAJALOCAL_PIN,
            BrandingType.FESTIVAL,
            LocationType.MAIN,
        ),
        (
            "ciprianocajaoperacion",
            OperatorRole.SALES,
            settings.DEFAULT_CIPRIANO_CAJAOPERACION_PIN,
            BrandingType.FESTIVAL,
            LocationType.SECONDARY,
        ),
        (
            "lotes",
            OperatorRole.BATCHES,
            settings.DEFAULT_FESTIVAL_BATCHES_PIN,
            BrandingType.FESTIVAL,
            LocationType.MAIN,
        ),
        (
            "ciprianoadministrador",
            OperatorRole.ADMIN,
            settings.DEFAULT_CIPRIANO_ADMINISTRADOR_PIN,
            BrandingType.FESTIVAL,
            LocationType.BOTH,
        ),
        (
            "ciprianooperador",
            OperatorRole.OPERATOR,
            settings.DEFAULT_CIPRIANO_OPERADOR_PIN,
            BrandingType.FESTIVAL,
            LocationType.BOTH,
        ),
        (
            "ciprianosocio",
            OperatorRole.SOCIO,
            settings.DEFAULT_CIPRIANO_SOCIO_PIN,
            BrandingType.FESTIVAL,
            LocationType.BOTH,
        ),
        (
            "cocinaburger",
            OperatorRole.KITCHEN,
            settings.DEFAULT_BURGERS_KITCHEN_PIN,
            BrandingType.BURGERS,
            LocationType.MAIN,
        ),
        (
            "ventasburger",
            OperatorRole.SALES,
            settings.DEFAULT_BURGERS_SALES_PIN,
            BrandingType.BURGERS,
            LocationType.MAIN,
        ),
        (
            "ventasburgersec",
            OperatorRole.SALES,
            settings.DEFAULT_BURGERS_SECONDARY_SALES_PIN,
            BrandingType.BURGERS,
            LocationType.SECONDARY,
        ),
        (
            "doncajalocal",
            OperatorRole.SALES,
            settings.DEFAULT_DON_CAJALOCAL_PIN,
            BrandingType.BURGERS,
            LocationType.MAIN,
        ),
        (
            "doncajaoperacion",
            OperatorRole.SALES,
            settings.DEFAULT_DON_CAJAOPERACION_PIN,
            BrandingType.BURGERS,
            LocationType.SECONDARY,
        ),
        (
            "lotesburger",
            OperatorRole.BATCHES,
            settings.DEFAULT_BURGERS_BATCHES_PIN,
            BrandingType.BURGERS,
            LocationType.MAIN,
        ),
        (
            "donadministrador",
            OperatorRole.ADMIN,
            settings.DEFAULT_DON_ADMINISTRADOR_PIN,
            BrandingType.BURGERS,
            LocationType.BOTH,
        ),
        (
            "donoperador",
            OperatorRole.OPERATOR,
            settings.DEFAULT_DON_OPERADOR_PIN,
            BrandingType.BURGERS,
            LocationType.BOTH,
        ),
        (
            "donsocio",
            OperatorRole.SOCIO,
            settings.DEFAULT_DON_SOCIO_PIN,
            BrandingType.BURGERS,
            LocationType.BOTH,
        ),
        ("admin", OperatorRole.ADMIN, settings.DEFAULT_ADMIN_LOGIN_PIN, BrandingType.BOTH, LocationType.BOTH),
    ]
    for username, role, pin, branding, location in defaults:
        op, created = Operator.objects.get_or_create(
            username=username,
            defaults={"role": role, "branding": branding, "location": location, "is_active": True},
        )
        updated_fields = []
        if op.role != role:
            op.role = role
            updated_fields.append("role")
        if op.branding != branding:
            op.branding = branding
            updated_fields.append("branding")
        if op.location != location:
            op.location = location
            updated_fields.append("location")
        if not op.is_active:
            op.is_active = True
            updated_fields.append("is_active")
        if created or not op.pin_hash:
            op.set_pin(pin)
            updated_fields.append("pin_hash")
        if updated_fields:
            op.save(update_fields=updated_fields)
    bootstrap_default_flavors()


def bootstrap_default_flavors() -> None:
    defaults = [
        (BrandingType.FESTIVAL, "DIAVOLA", "DIA", 10),
        (BrandingType.FESTIVAL, "DIAVOLA A MI MANERA", "DAM", 20),
        (BrandingType.FESTIVAL, "JAMON Y QUESO", "JYQ", 30),
        (BrandingType.BURGERS, "HAMBURGUESA CLASICA", "BUR", 10),
    ]
    for branding, name, prefix, sort_order in defaults:
        flavor, created = Flavor.objects.get_or_create(
            branding=branding,
            name=name,
            defaults={"prefix": prefix, "is_active": True, "sort_order": sort_order},
        )
        updates = []
        if flavor.prefix != prefix:
            flavor.prefix = prefix
            updates.append("prefix")
        if not flavor.is_active:
            flavor.is_active = True
            updates.append("is_active")
        if flavor.sort_order != sort_order:
            flavor.sort_order = sort_order
            updates.append("sort_order")
        if updates:
            flavor.save(update_fields=updates)


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
    request.session["operator_location"] = operator.location
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
                return redirect("/")
            if operator.role not in role_set:
                return redirect("/")
            if not get_active_branding(request):
                return redirect("/")
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
