from functools import wraps
from typing import Iterable

from django.conf import settings
from django.shortcuts import redirect

from .models import Operator, OperatorRole


ROLE_LABEL_MAP = {
    OperatorRole.KITCHEN: "COCINA",
    OperatorRole.SALES: "VENTAS",
    OperatorRole.BATCHES: "ADMIN",
    OperatorRole.ADMIN: "ADMIN",
}


def bootstrap_default_operators() -> None:
    if Operator.objects.exists():
        return

    defaults = [
        ("cocina", OperatorRole.KITCHEN, settings.DEFAULT_KITCHEN_PIN),
        ("ventas", OperatorRole.SALES, settings.DEFAULT_SALES_PIN),
        ("lotes", OperatorRole.BATCHES, settings.DEFAULT_BATCHES_PIN),
        ("admin", OperatorRole.ADMIN, settings.DEFAULT_ADMIN_LOGIN_PIN),
    ]
    for username, role, pin in defaults:
        op = Operator(username=username, role=role, is_active=True)
        op.set_pin(pin)
        op.save()


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
    request.session.set_expiry(settings.AUTH_SESSION_MINUTES * 60)


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
            request.current_operator = operator
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
    return operator, None, None
