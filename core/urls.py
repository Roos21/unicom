
from decimal import Decimal

from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.urls import include, path
from django.utils import timezone

from accounts.models import User
from expense.models import Expense
from sales.models import Product, Sale

@login_required
def index(request):
    """
    Page d'accueil / tableau de bord de l'ERP
    """
    now = timezone.localtime(timezone.now())
    start_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    sales_qs = Sale.objects.filter(date__range=[start_day, end_day])
    expenses_qs = Expense.objects.filter(created_at__range=[start_day, end_day])

    # Scope: un gerant voit ses chiffres du jour, les autres profils voient l'ensemble.
    if request.user.role == User.Role.GERANT:
        sales_qs = sales_qs.filter(created_by=request.user)
        expenses_qs = expenses_qs.filter(created_by=request.user)

    validated_sales = sales_qs.filter(status=Sale.VALIDATED)
    pending_sales = sales_qs.filter(status=Sale.PENDING)

    approved_expenses = expenses_qs.filter(status="APPROVED")
    paid_expenses = expenses_qs.filter(status="PAID")
    pending_expenses = expenses_qs.filter(status__in=["PENDING", "IN_REVIEW"])

    total_sales_amount = validated_sales.aggregate(total=Sum("total_price"))["total"] or Decimal("0")
    cash_sales_amount = validated_sales.filter(payment_method="Cash").aggregate(total=Sum("total_price"))["total"] or Decimal("0")
    credit_sales_amount = validated_sales.filter(payment_method="Credit").aggregate(total=Sum("total_price"))["total"] or Decimal("0")
    total_expenses_amount = approved_expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    paid_expenses_amount = paid_expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    context = {
        "today": now,
        "total_sales_amount": total_sales_amount,
        "cash_sales_amount": cash_sales_amount,
        "credit_sales_amount": credit_sales_amount,
        "total_expenses_amount": total_expenses_amount,
        "paid_expenses_amount": paid_expenses_amount,
        "net_day_amount": total_sales_amount - total_expenses_amount,
        "sales_count": validated_sales.count(),
        "pending_sales_count": pending_sales.count(),
        "expenses_count": approved_expenses.count(),
        "pending_expenses_count": pending_expenses.count(),
        "active_products_count": Product.objects.filter(is_active=True).count(),
        "users_count": User.objects.filter(is_deleted=False).count(),
        "recent_sales": sales_qs.select_related("product", "created_by").order_by("-date")[:8],
        "recent_expenses": expenses_qs.select_related("account", "created_by").order_by("-created_at")[:8],
    }

    return render(request, "index.html", context)
urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/", include("accounts.urls", namespace="accounts")),  # <--- Ici
    path("sales/", include("sales.urls", namespace="sales")),  # <--- Ici
    path("expenses/", include("expense.urls", namespace="expenses")),  # <--- Ici
    
    path('', index, name='index'),
]
