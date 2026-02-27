from datetime import date
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.core.paginator import Paginator, EmptyPage
from django.utils.html import escape
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth_utils import (
    ROLE_LABEL_MAP,
    bootstrap_default_operators,
    get_current_operator,
    login_operator,
    logout_operator,
    require_roles_api,
    require_roles_web,
)
from .models import PizzaItem, PizzaStatus, RoleType, ScanEvent, Waiter
from .qr_pdf import build_labels_pdf, build_waiters_labels_pdf
from .serializers import PizzaItemSerializer, ScanEventSerializer, WaiterSerializer
from .services import Actor, TransitionError, admin_set_status, create_batch, create_waiter, process_scan, undo_last


def _parse_iso_date(value: str, field_name: str) -> tuple[date | None, str | None]:
    raw = (value or "").strip()
    if not raw:
        return None, None
    try:
        return date.fromisoformat(raw), None
    except ValueError:
        return None, f"{field_name} invalida. Formato esperado: YYYY-MM-DD"


def login_view(request):
    bootstrap_default_operators()
    if get_current_operator(request):
        return redirect("/")

    error = ""
    next_url = request.GET.get("next", "/")
    if not next_url.startswith("/"):
        next_url = "/"
    denied = request.GET.get("denied") == "1"

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip().lower()
        pin = (request.POST.get("pin") or "").strip()
        next_url = (request.POST.get("next") or "/").strip()
        if not next_url.startswith("/"):
            next_url = "/"
        if not username or not pin:
            error = "Usuario y PIN requeridos."
        else:
            from .models import Operator

            try:
                operator = Operator.objects.get(username=username, is_active=True)
            except Operator.DoesNotExist:
                operator = None

            if not operator or not operator.check_pin(pin):
                error = "Credenciales invalidas."
            else:
                login_operator(request, operator)
                return redirect(next_url)

    return render(
        request,
        "festival/login.html",
        {"error": error, "next": next_url, "denied": denied},
    )


def logout_view(request):
    logout_operator(request)
    return redirect("/login/")


def home_view(request):
    operator = get_current_operator(request)
    if not operator:
        return redirect("/login/")
    if operator.role == "KITCHEN":
        return redirect("/kitchen/")
    if operator.role == "SALES":
        return redirect("/sales/")
    if operator.role == "BATCHES":
        return redirect("/batches/")
    return redirect("/dashboard/")


@require_roles_web(["KITCHEN", "ADMIN"])
def kitchen_view(request):
    return render(
        request,
        "festival/scan_station.html",
        {"mode": "KITCHEN", "title": "Modo Cocina", "operator": request.current_operator},
    )


@require_roles_web(["SALES", "ADMIN"])
def sales_view(request):
    return render(
        request,
        "festival/scan_station.html",
        {"mode": "SALES", "title": "Modo Ventas", "operator": request.current_operator},
    )


@require_roles_web(["SALES", "ADMIN"])
def dashboard_view(request):
    return render(request, "festival/dashboard.html", {"operator": request.current_operator})


@require_roles_web(["BATCHES", "ADMIN"])
def batches_view(request):
    return render(request, "festival/batches.html", {"operator": request.current_operator})


@require_roles_web(["ADMIN"])
def admin_ops_view(request):
    return render(request, "festival/admin_ops.html", {"operator": request.current_operator})


class ScanAPIView(APIView):
    def post(self, request):
        operator, error, error_status = require_roles_api(request, ["KITCHEN", "SALES", "ADMIN"])
        if error:
            return Response(error, status=error_status)

        pizza_id = (request.data.get("id") or "").strip().upper()
        mode = (request.data.get("mode") or "").strip().upper()
        flavor_if_empty = (request.data.get("flavor_if_empty") or "").strip().upper()
        override_pin = (request.data.get("override_pin") or "").strip()
        waiter_code = (request.data.get("waiter_code") or "").strip().upper()

        if not pizza_id:
            return Response({"ok": False, "error": "ID requerido"}, status=status.HTTP_400_BAD_REQUEST)

        if operator.role == "KITCHEN" and mode != "KITCHEN":
            return Response({"ok": False, "error": "Modo no permitido para este usuario"}, status=403)
        if operator.role == "SALES" and mode != "SALES":
            return Response({"ok": False, "error": "Modo no permitido para este usuario"}, status=403)
        if operator.role == "ADMIN" and mode not in {"KITCHEN", "SALES"}:
            return Response({"ok": False, "error": "Modo invalido"}, status=400)

        try:
            item, event = process_scan(
                pizza_id=pizza_id,
                mode=mode,
                actor=Actor(name=operator.username, role=ROLE_LABEL_MAP.get(operator.role, RoleType.ADMIN)),
                flavor_if_empty=flavor_if_empty,
                override_pin=override_pin,
                waiter_code=waiter_code,
            )
        except TransitionError as exc:
            return Response({"ok": False, "error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "ok": True,
                "message": f"OK {item.id} => {item.status}",
                "pizza": PizzaItemSerializer(item).data,
                "event": ScanEventSerializer(event).data,
            }
        )


class WaiterAPIView(APIView):
    def get(self, request):
        operator, error, error_status = require_roles_api(request, ["BATCHES", "ADMIN", "SALES"])
        if error:
            return Response(error, status=error_status)
        waiters = Waiter.objects.filter(is_active=True).order_by("name")
        return Response({"ok": True, "waiters": WaiterSerializer(waiters, many=True).data})

    def post(self, request):
        operator, error, error_status = require_roles_api(request, ["BATCHES", "ADMIN"])
        if error:
            return Response(error, status=error_status)

        name = (request.data.get("name") or "").strip()
        try:
            waiter = create_waiter(name=name, actor_name=operator.username)
        except TransitionError as exc:
            return Response({"ok": False, "error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "ok": True,
                "waiter": WaiterSerializer(waiter).data,
                "labels_pdf_url": f"/api/waiters/labels.pdf?codes={waiter.code}",
            }
        )


class WaiterLabelsAPIView(APIView):
    def get(self, request):
        operator, error, error_status = require_roles_api(request, ["BATCHES", "ADMIN"])
        if error:
            return Response(error, status=error_status)

        codes_raw = (request.GET.get("codes") or "").strip().upper()
        if not codes_raw:
            return Response({"ok": False, "error": "codes requerido"}, status=status.HTTP_400_BAD_REQUEST)
        codes = [code.strip() for code in codes_raw.split(",") if code.strip()]
        waiters = list(Waiter.objects.filter(code__in=codes, is_active=True).order_by("name", "code"))
        if not waiters:
            return Response({"ok": False, "error": "Meseros no encontrados"}, status=status.HTTP_404_NOT_FOUND)

        pdf_data = build_waiters_labels_pdf(waiters)
        response = HttpResponse(pdf_data, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="waiters-labels.pdf"'
        return response


class BatchGenerateAPIView(APIView):
    def post(self, request):
        operator, error, error_status = require_roles_api(request, ["BATCHES", "ADMIN"])
        if error:
            return Response(error, status=error_status)

        day_code = (request.data.get("day_code") or "").strip().upper()
        flavor_prefix = (request.data.get("flavor_prefix") or "").strip().upper()
        flavor = (request.data.get("flavor") or "").strip().upper()
        size = (request.data.get("size") or "").strip().upper()
        actor_name = operator.username
        notes = (request.data.get("notes") or "").strip()

        try:
            quantity = int(request.data.get("quantity", 0))
            if quantity <= 0:
                raise ValueError("Cantidad invalida")
        except ValueError:
            return Response(
                {"ok": False, "error": "quantity debe ser entero positivo"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            price = Decimal(str(request.data.get("price", "0")))
        except (InvalidOperation, TypeError):
            return Response({"ok": False, "error": "price invalido"}, status=status.HTTP_400_BAD_REQUEST)

        start_raw = request.data.get("start_number")
        admin_actions_pin = (request.data.get("admin_actions_pin") or "").strip()
        try:
            start_number = int(start_raw) if start_raw not in (None, "", "auto") else None
        except ValueError:
            return Response({"ok": False, "error": "start_number invalido"}, status=status.HTTP_400_BAD_REQUEST)

        if start_number is not None and admin_actions_pin != settings.ADMIN_ACTIONS_PIN:
            return Response(
                {"ok": False, "error": "PIN admin invalido para definir Nro inicial manual"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not flavor_prefix:
            return Response(
                {"ok": False, "error": "flavor_prefix es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            batch, items = create_batch(
                day_code=day_code,
                flavor_prefix=flavor_prefix,
                flavor=flavor,
                quantity=quantity,
                price=price,
                size=size,
                actor_name=actor_name,
                start_number=start_number,
                notes=notes,
            )
        except Exception as exc:  # pragma: no cover - defensive path
            return Response({"ok": False, "error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "ok": True,
                "batch_code": batch.code,
                "count": len(items),
                "first_id": items[0].id if items else None,
                "last_id": items[-1].id if items else None,
                "labels_pdf_url": (
                    f"/api/batches/{batch.code}/labels.pdf"
                    f"?from_id={items[0].id}&to_id={items[-1].id}"
                    if items
                    else f"/api/batches/{batch.code}/labels.pdf"
                ),
            }
        )


class BatchLabelsAPIView(APIView):
    def get(self, request, batch_code: str):
        operator, error, error_status = require_roles_api(request, ["BATCHES", "ADMIN"])
        if error:
            return Response(error, status=error_status)

        queryset = PizzaItem.objects.filter(batch__code=batch_code).order_by("id")
        from_id = (request.GET.get("from_id") or "").strip().upper()
        to_id = (request.GET.get("to_id") or "").strip().upper()
        if from_id:
            queryset = queryset.filter(id__gte=from_id)
        if to_id:
            queryset = queryset.filter(id__lte=to_id)
        items = list(queryset)
        if not items:
            return Response({"ok": False, "error": "Lote no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        pdf_data = build_labels_pdf(items)
        response = HttpResponse(pdf_data, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="labels-{batch_code}.pdf"'
        return response


class DashboardDataAPIView(APIView):
    def get(self, request):
        operator, error, error_status = require_roles_api(request, ["SALES", "ADMIN"])
        if error:
            return Response(error, status=error_status)

        try:
            page = max(1, int(request.GET.get("page", 1)))
        except ValueError:
            page = 1
        try:
            page_size = int(request.GET.get("page_size", 20))
        except ValueError:
            page_size = 20
        page_size = min(30, max(5, page_size))
        mode = (request.GET.get("mode") or "").strip().upper()
        to_status = (request.GET.get("to_status") or "").strip().upper()
        pizza_id = (request.GET.get("pizza_id") or "").strip().upper()
        flavor = (request.GET.get("flavor") or "").strip().upper()
        waiter_name = (request.GET.get("waiter_name") or "").strip().upper()
        date_from, date_from_error = _parse_iso_date(request.GET.get("date_from"), "date_from")
        date_to, date_to_error = _parse_iso_date(request.GET.get("date_to"), "date_to")
        if date_from_error:
            return Response({"ok": False, "error": date_from_error}, status=status.HTTP_400_BAD_REQUEST)
        if date_to_error:
            return Response({"ok": False, "error": date_to_error}, status=status.HTTP_400_BAD_REQUEST)
        if date_from and date_to and date_from > date_to:
            return Response(
                {"ok": False, "error": "date_from no puede ser mayor que date_to"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sales_filter_active = bool(flavor or waiter_name or date_from or date_to)
        if sales_filter_active and not mode:
            mode = "SALES"
        if sales_filter_active and not to_status:
            to_status = PizzaStatus.VENDIDA

        counts = {
            row["status"]: row["total"] for row in PizzaItem.objects.values("status").annotate(total=Count("id"))
        }
        for key in PizzaStatus.values:
            counts.setdefault(key, 0)
        revenue_qs = PizzaItem.objects.filter(status=PizzaStatus.VENDIDA)
        if flavor:
            revenue_qs = revenue_qs.filter(flavor=flavor)
        if waiter_name:
            revenue_qs = revenue_qs.filter(sold_by__icontains=waiter_name)
        if date_from:
            revenue_qs = revenue_qs.filter(sold_at__date__gte=date_from)
        if date_to:
            revenue_qs = revenue_qs.filter(sold_at__date__lte=date_to)
        revenue = revenue_qs.aggregate(total=Sum("price")).get("total")

        latest_qs = ScanEvent.objects.select_related("pizza").all()
        if mode:
            latest_qs = latest_qs.filter(mode=mode)
        if to_status:
            latest_qs = latest_qs.filter(to_status=to_status)
        if pizza_id:
            latest_qs = latest_qs.filter(pizza__id__icontains=pizza_id)
        if flavor:
            latest_qs = latest_qs.filter(pizza__flavor=flavor)
        if waiter_name:
            latest_qs = latest_qs.filter(waiter_name__icontains=waiter_name)
        if date_from:
            latest_qs = latest_qs.filter(pizza__sold_at__date__gte=date_from)
        if date_to:
            latest_qs = latest_qs.filter(pizza__sold_at__date__lte=date_to)

        paginator = Paginator(latest_qs, page_size)
        if paginator.count == 0:
            latest_items = []
            pagination = {
                "page": 1,
                "page_size": page_size,
                "total_pages": 1,
                "total_items": 0,
                "has_next": False,
                "has_previous": False,
            }
        else:
            try:
                latest_page = paginator.page(page)
            except EmptyPage:
                latest_page = paginator.page(paginator.num_pages)
            latest_items = list(latest_page.object_list)
            pagination = {
                "page": latest_page.number,
                "page_size": page_size,
                "total_pages": paginator.num_pages,
                "total_items": paginator.count,
                "has_next": latest_page.has_next(),
                "has_previous": latest_page.has_previous(),
            }

        return Response(
            {
                "ok": True,
                "counts": counts,
                "revenue_sold": str(revenue or "0"),
                "latest": ScanEventSerializer(latest_items, many=True).data,
                "pagination": pagination,
                "filters": {
                    "mode": mode,
                    "to_status": to_status,
                    "pizza_id": pizza_id,
                    "flavor": flavor,
                    "waiter_name": waiter_name,
                    "date_from": date_from.isoformat() if date_from else "",
                    "date_to": date_to.isoformat() if date_to else "",
                },
            }
        )


class SalesExportXLSAPIView(APIView):
    def get(self, request):
        operator, error, error_status = require_roles_api(request, ["SALES", "ADMIN"])
        if error:
            return Response(error, status=error_status)

        flavor = (request.GET.get("flavor") or "").strip().upper()
        waiter_name = (request.GET.get("waiter_name") or "").strip().upper()
        date_from, date_from_error = _parse_iso_date(request.GET.get("date_from"), "date_from")
        date_to, date_to_error = _parse_iso_date(request.GET.get("date_to"), "date_to")
        if date_from_error:
            return Response({"ok": False, "error": date_from_error}, status=status.HTTP_400_BAD_REQUEST)
        if date_to_error:
            return Response({"ok": False, "error": date_to_error}, status=status.HTTP_400_BAD_REQUEST)
        if date_from and date_to and date_from > date_to:
            return Response(
                {"ok": False, "error": "date_from no puede ser mayor que date_to"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sales_qs = PizzaItem.objects.filter(status=PizzaStatus.VENDIDA).order_by("sold_at", "id")
        if flavor:
            sales_qs = sales_qs.filter(flavor=flavor)
        if waiter_name:
            sales_qs = sales_qs.filter(sold_by__icontains=waiter_name)
        if date_from:
            sales_qs = sales_qs.filter(sold_at__date__gte=date_from)
        if date_to:
            sales_qs = sales_qs.filter(sold_at__date__lte=date_to)

        filename = "ventas"
        if date_from or date_to:
            filename += f"-{date_from.isoformat() if date_from else 'inicio'}-{date_to.isoformat() if date_to else 'hoy'}"
        if flavor:
            filename += f"-{flavor}"
        if waiter_name:
            filename += f"-{waiter_name}"
        flavor_label = flavor if flavor else "TODOS LOS SABORES"
        waiter_label = waiter_name if waiter_name else "TODOS LOS MESEROS"
        from_label = date_from.isoformat() if date_from else "INICIO"
        to_label = date_to.isoformat() if date_to else "HOY"
        total_revenue = Decimal("0")
        total_items = 0
        rows_html: list[str] = []

        for idx, item in enumerate(sales_qs, start=1):
            total_items += 1
            total_revenue += item.price or Decimal("0")
            sold_date = item.sold_at.date().isoformat() if item.sold_at else ""
            sold_time = item.sold_at.strftime("%H:%M:%S") if item.sold_at else ""
            bg = "#FFF7EA" if idx % 2 == 0 else "#FFFFFF"
            rows_html.append(
                f"<tr style='background:{bg}'>"
                f"<td>{escape(item.id)}</td>"
                f"<td>{escape(item.flavor)}</td>"
                f"<td>{escape(item.size)}</td>"
                f"<td style='mso-number-format:\"#,##0.00\"'>{item.price:.2f}</td>"
                f"<td>{escape(sold_date)}</td>"
                f"<td>{escape(sold_time)}</td>"
                f"<td>{escape(item.sold_by or '')}</td>"
                "</tr>"
            )

        html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
</head>
<body>
  <table border="1" cellspacing="0" cellpadding="6" style="border-collapse:collapse;font-family:Calibri,Arial,sans-serif;font-size:11pt;">
    <tr>
      <td colspan="7" style="background:#924E37;color:#FFFFFF;font-size:16pt;font-weight:bold;text-align:center;">CIPRIANO - REPORTE DE VENTAS</td>
    </tr>
    <tr>
      <td colspan="7" style="background:#F4E8CD;color:#1B3240;font-weight:bold;text-align:center;">Filtro sabor: {escape(flavor_label)} | Mesero: {escape(waiter_label)} | Periodo: {escape(from_label)} a {escape(to_label)}</td>
    </tr>
    <tr><td colspan="7" style="background:#FFFFFF;"></td></tr>
    <tr style="background:#1B3240;color:#FFFFFF;font-weight:bold;text-align:center;">
      <td>ID</td>
      <td>Sabor</td>
      <td>Tamano</td>
      <td>Precio</td>
      <td>Fecha venta</td>
      <td>Hora venta</td>
      <td>Mesero</td>
    </tr>
    {''.join(rows_html)}
    <tr><td colspan="7" style="background:#FFFFFF;"></td></tr>
    <tr>
      <td style="background:#F4E8CD;color:#1B3240;font-weight:bold;">TOTAL VENTAS</td>
      <td style="background:#F4E8CD;color:#1B3240;font-weight:bold;">{total_items}</td>
      <td colspan="5"></td>
    </tr>
    <tr>
      <td style="background:#F4E8CD;color:#1B3240;font-weight:bold;">TOTAL FACTURADO</td>
      <td style="background:#F4E8CD;color:#1B3240;font-weight:bold;mso-number-format:'#,##0.00';">{total_revenue:.2f}</td>
      <td colspan="5"></td>
    </tr>
  </table>
</body>
</html>"""

        response = HttpResponse(
            html,
            content_type="application/vnd.ms-excel; charset=utf-8",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}.xls"'
        return response


class AdminStatusAPIView(APIView):
    def post(self, request):
        operator, error, error_status = require_roles_api(request, ["ADMIN"])
        if error:
            return Response(error, status=error_status)

        pizza_id = (request.data.get("id") or "").strip().upper()
        to_status = (request.data.get("to_status") or "").strip().upper()
        pin = (request.data.get("pin") or "").strip()
        actor = Actor(name=operator.username, role=RoleType.ADMIN)

        try:
            item, event = admin_set_status(pizza_id=pizza_id, to_status=to_status, actor=actor, pin=pin)
        except TransitionError as exc:
            return Response({"ok": False, "error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"ok": True, "pizza": PizzaItemSerializer(item).data, "event": ScanEventSerializer(event).data}
        )


class UndoAPIView(APIView):
    def post(self, request):
        operator, error, error_status = require_roles_api(request, ["ADMIN"])
        if error:
            return Response(error, status=error_status)

        pin = (request.data.get("pin") or "").strip()
        actor = Actor(name=operator.username, role=RoleType.ADMIN)

        try:
            item, event = undo_last(pin=pin, actor=actor)
        except TransitionError as exc:
            return Response({"ok": False, "error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "ok": True,
                "message": f"Deshecho: {item.id} => {item.status}",
                "pizza": PizzaItemSerializer(item).data,
                "event": ScanEventSerializer(event).data,
            }
        )


class AdminVerifyPinAPIView(APIView):
    def post(self, request):
        operator, error, error_status = require_roles_api(request, ["ADMIN"])
        if error:
            return Response(error, status=error_status)

        pin = (request.data.get("pin") or "").strip()
        if pin != settings.ADMIN_ACTIONS_PIN:
            return Response({"ok": False, "error": "PIN admin invalido"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"ok": True, "message": "PIN valido"})
