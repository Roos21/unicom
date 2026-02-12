from collections import defaultdict
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import permission_required, role_required
from accounts.models import Antenne, User
from accounts.permissions import Permissions
from expense.models import AccountMoney, Expense
from sales.filters import SaleFilter

from .forms import (
    CategoryForm,
    ProductByAntenneForm,
    ProductForm,
    ReportingPeriodForm,
    SaleForm,
)
from .models import Category, Credit, Product, ProductByAntenne, Sale


def _get_period_bounds(selected_period):
    now = timezone.localtime(timezone.now())
    end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if selected_period == "week":
        start_date -= timedelta(days=7)
    elif selected_period == "month":
        start_date = start_date.replace(day=1)
    elif selected_period == "quarter":
        current_month = start_date.month
        start_month = ((current_month - 1) // 3) * 3 + 1
        start_date = start_date.replace(month=start_month, day=1)
    elif selected_period == "year":
        start_date = start_date.replace(month=1, day=1)

    return start_date, end_date


def _apply_antenne_scope(user, sales_qs, expenses_qs):
    if user.role == User.Role.GERANT:
        sales_qs = sales_qs.filter(created_by=user)
        expenses_qs = expenses_qs.filter(created_by=user)
    return sales_qs, expenses_qs


def _build_accounting_context(form, selected_period, start_date, end_date, sales_qs, expenses_qs, selected_antenne=None):
    ventes_validees = sales_qs.filter(status=Sale.VALIDATED)

    ventes_detaillees = defaultdict(
        lambda: {"total_par_type": 0, "categories": defaultdict(lambda: {"total": 0, "details": []})}
    )
    for vente in ventes_validees.select_related("product", "product__category"):
        category_type = vente.product.category.get_type_display()
        category_name = vente.product.category.name
        quantite = vente.quantity or 0
        prix_unitaire = (vente.total_price / quantite) if quantite else 0

        ventes_detaillees[category_type]["categories"][category_name]["details"].append(
            {
                "produit": vente.product.name,
                "quantite": vente.quantity,
                "prix_unitaire": prix_unitaire,
                "total_vente": vente.total_price,
                "methode_paiement": vente.get_payment_method_display(),
                "client": vente.customer if vente.customer else "N/A",
            }
        )
        ventes_detaillees[category_type]["categories"][category_name]["total"] += vente.total_price
        ventes_detaillees[category_type]["total_par_type"] += vente.total_price

    final_ventes_structure = {}
    for type_vente, data_type in ventes_detaillees.items():
        data_type["categories"] = dict(data_type["categories"])
        final_ventes_structure[type_vente] = data_type

    ventes_cash_total = ventes_validees.filter(payment_method="Cash").aggregate(Sum("total_price"))["total_price__sum"] or 0
    ventes_credit_total = ventes_validees.filter(payment_method="Credit").aggregate(Sum("total_price"))["total_price__sum"] or 0
    total_ventes = ventes_cash_total + ventes_credit_total

    depenses_approuvees = expenses_qs.filter(status="APPROVED")
    depenses_regroupees = depenses_approuvees.values("category__name").annotate(total_depense=Sum("amount")).order_by("category__name")
    total_depenses_global = depenses_approuvees.aggregate(Sum("amount"))["amount__sum"] or 0
    solde_net = ventes_cash_total - total_depenses_global

    sales_by_antenne = (
        ventes_validees.values("created_by__antenne__nom")
        .annotate(total_sales=Sum("total_price"))
        .order_by("created_by__antenne__nom")
    )
    expenses_by_antenne = (
        depenses_approuvees.values("antenne__nom")
        .annotate(total_expenses=Sum("amount"))
        .order_by("antenne__nom")
    )

    antenna_summary = {}
    for row in sales_by_antenne:
        name = row["created_by__antenne__nom"] or "Sans antenne"
        antenna_summary.setdefault(name, {"sales": 0, "expenses": 0})
        antenna_summary[name]["sales"] = row["total_sales"] or 0

    for row in expenses_by_antenne:
        name = row["antenne__nom"] or "Sans antenne"
        antenna_summary.setdefault(name, {"sales": 0, "expenses": 0})
        antenna_summary[name]["expenses"] = row["total_expenses"] or 0

    for name, metrics in antenna_summary.items():
        metrics["net"] = (metrics["sales"] or 0) - (metrics["expenses"] or 0)

    credits_impayes = Credit.objects.filter(status=Credit.PENDING)
    if selected_antenne:
        credits_impayes = credits_impayes.filter(sale__created_by__antenne=selected_antenne)

    return {
        "form": form,
        "start_date": start_date,
        "end_date": end_date,
        "selected_period": selected_period,
        "selected_antenne": selected_antenne,
        "ventes_detaillees_par_categorie": final_ventes_structure,
        "ventes_cash": ventes_cash_total,
        "ventes_credit": ventes_credit_total,
        "total_ventes": total_ventes,
        "depenses_par_section": depenses_regroupees,
        "total_depenses_global": total_depenses_global,
        "solde_net": solde_net,
        "antenna_summary": antenna_summary,
        "credits_impayes_total": credits_impayes.count(),
        "credits_impayes_montant": credits_impayes.aggregate(Sum("sale__total_price"))["sale__total_price__sum"] or 0,
    }


@login_required
@role_required("admin", "directeur", "superviseur", "gerant")
def category_list(request):
    categories = Category.objects.all()
    return render(request, "sales/category_list.html", {"categories": categories})


@login_required
@permission_required(Permissions.MANAGE_ANTENNES)
def category_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Categorie creee avec succes.")
            return redirect("sales:category_list")
    else:
        form = CategoryForm(user=request.user)
    return render(request, "sales/category_form.html", {"form": form})


@login_required
@permission_required(Permissions.MANAGE_ANTENNES)
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Categorie '{category.name}' mise a jour.")
            return redirect("sales:category_list")
    else:
        form = CategoryForm(instance=category, user=request.user)
    return render(request, "sales/category_form.html", {"form": form})


@login_required
@role_required("admin")
def category_validate(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.is_validated = True
    category.save(update_fields=["is_validated"])
    messages.success(request, f"Categorie '{category.name}' validee.")
    return redirect("sales:category_list")


@login_required
def product_list(request):
    products = Product.objects.all().order_by("name")
    paginator = Paginator(products, 15)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "sales/product_list.html", {"page_obj": page_obj})


@login_required
@permission_required(Permissions.MANAGE_TREASURY)
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit cree avec succes.")
            return redirect("sales:product_list")
    else:
        form = ProductForm(user=request.user)
    return render(request, "sales/product_form.html", {"form": form})


@login_required
@permission_required(Permissions.MANAGE_TREASURY)
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Produit '{product.name}' mis a jour.")
            return redirect("sales:product_list")
    else:
        form = ProductForm(instance=product, user=request.user)
    return render(request, "sales/product_form.html", {"form": form})


@login_required
@role_required("admin")
def product_validate(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_validated = True
    product.save(update_fields=["is_validated"])
    messages.success(request, f"Produit '{product.name}' valide.")
    return redirect("sales:product_list")


@login_required
@permission_required(Permissions.MANAGE_CATEGORIES)
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        category.delete()
        messages.success(request, f"Categorie '{category.name}' supprimee.")
        return redirect("sales:category_list")
    return render(request, "sales/category_confirm_delete.html", {"category": category})


@login_required
@permission_required(Permissions.MANAGE_PRODUCTS)
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, f"Produit '{product.name}' supprime.")
        return redirect("sales:product_list")
    return render(request, "sales/product_confirm_delete.html", {"product": product})


@login_required
@permission_required(Permissions.MANAGE_ANTENNES)
def antenna_pricing_list(request):
    qs = ProductByAntenne.objects.select_related("product", "antenne").order_by("antenne__nom", "product__name")
    if request.user.role == User.Role.GERANT and request.user.antenne:
        qs = qs.filter(antenne=request.user.antenne)
    return render(request, "sales/antenna_pricing_list.html", {"prices": qs})


@login_required
@permission_required(Permissions.MANAGE_ANTENNES)
def antenna_pricing_create(request):
    if request.method == "POST":
        form = ProductByAntenneForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.is_validated = True
            item.save()
            messages.success(request, "Tarification antenne enregistree.")
            return redirect("sales:antenna_pricing_list")
    else:
        form = ProductByAntenneForm()
    return render(request, "sales/antenna_pricing_form.html", {"form": form})


@login_required
@permission_required(Permissions.MANAGE_ANTENNES)
def antenna_pricing_update(request, pk):
    pricing = get_object_or_404(ProductByAntenne, pk=pk)
    if request.method == "POST":
        form = ProductByAntenneForm(request.POST, instance=pricing)
        if form.is_valid():
            form.save()
            messages.success(request, "Tarification antenne mise a jour.")
            return redirect("sales:antenna_pricing_list")
    else:
        form = ProductByAntenneForm(instance=pricing)
    return render(request, "sales/antenna_pricing_form.html", {"form": form, "pricing": pricing})


@login_required
def sale_create(request):
    if request.method == "POST":
        form = SaleForm(request.POST, user=request.user)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.created_by = request.user
            unit_price = sale.product.get_price_for_antenne(request.user.antenne)
            sale.total_price = unit_price * sale.quantity
            # Toute nouvelle vente est automatiquement validee, quel que soit le role.
            sale.status = Sale.VALIDATED
            sale.save()

            if sale.payment_method == "Credit":
                Credit.objects.update_or_create(
                    sale=sale,
                    defaults={
                        "nom": form.cleaned_data.get("credit_nom") or sale.customer or "Client credit",
                        "telephone": form.cleaned_data.get("credit_telephone") or "N/A",
                        "date": timezone.now(),
                        "status": Credit.PENDING,
                    },
                )
            else:
                Credit.objects.filter(sale=sale).delete()

            messages.success(request, f"Vente enregistree et validee. Prix unitaire applique: {unit_price} FCFA")
            return redirect("sales:sale_list")
    else:
        form = SaleForm(user=request.user)

    return render(request, "sales/sale_form.html", {"form": form})


@login_required
def sale_update(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == "POST":
        form = SaleForm(request.POST, instance=sale, user=request.user)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.last_total_price = sale.total_price
            antenne = sale.created_by.antenne if sale.created_by else request.user.antenne
            unit_price = sale.product.get_price_for_antenne(antenne)
            sale.total_price = unit_price * sale.quantity
            sale.status = Sale.PENDING
            sale.save()

            if sale.payment_method == "Credit":
                Credit.objects.update_or_create(
                    sale=sale,
                    defaults={
                        "nom": form.cleaned_data.get("credit_nom") or sale.customer or "Client credit",
                        "telephone": form.cleaned_data.get("credit_telephone") or "N/A",
                        "date": timezone.now(),
                        "status": Credit.PENDING,
                    },
                )
            else:
                Credit.objects.filter(sale=sale).delete()

            messages.success(request, "Vente mise a jour et remise en attente de validation.")
            return redirect("sales:sale_list")
    else:
        form = SaleForm(instance=sale, user=request.user)

    return render(request, "sales/sale_form.html", {"form": form})


@login_required
@permission_required(Permissions.VALIDATE_UPDATE_SALES)
def sale_validate(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if sale.status == Sale.PENDING:
        sale.status = Sale.VALIDATED
        sale.save(update_fields=["status"])
        messages.success(request, "La vente a ete validee.")
    else:
        messages.info(request, "Cette vente n'est pas en attente de validation.")
    return redirect("sales:sale_list")


@login_required
@permission_required(Permissions.VALIDATE_UPDATE_SALES)
def sale_reject(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if sale.status == Sale.PENDING:
        sale.status = Sale.REJECTED
        sale.save(update_fields=["status"])
        messages.success(request, "La modification de la vente a ete rejetee.")
    else:
        messages.info(request, "Cette vente n'est pas en attente de validation.")
    return redirect("sales:sale_list")


@login_required
def sale_list(request):
    queryset = Sale.objects.select_related("product", "created_by", "created_by__antenne").order_by("-created_at")
    if request.user.role == User.Role.GERANT:
        queryset = queryset.filter(created_by=request.user)

    sale_filter = SaleFilter(request.GET, queryset=queryset)
    page_obj = Paginator(sale_filter.qs, 10).get_page(request.GET.get("page"))

    solde_caisse = AccountMoney.objects.filter(type="CAISSE").first()
    solde_banque = AccountMoney.objects.filter(type="BANQUE").first()

    context = {
        "page_obj": page_obj,
        "filter": sale_filter,
        "solde_caisse": solde_caisse,
        "solde_banque": solde_banque,
    }
    return render(request, "sales/sale_list.html", context)


@login_required
def credit_list(request):
    qs = Credit.objects.select_related("sale", "sale__product", "sale__created_by", "sale__created_by__antenne").order_by("-date")
    if request.user.role == User.Role.GERANT:
        qs = qs.filter(sale__created_by=request.user)

    status = request.GET.get("status")
    if status in [Credit.PENDING, Credit.PAID]:
        qs = qs.filter(status=status)

    return render(request, "sales/credit_list.html", {"credits": qs, "selected_status": status})


@login_required
@permission_required(Permissions.MANAGE_TREASURY)
def credit_mark_paid(request, pk):
    credit = get_object_or_404(Credit, pk=pk)
    credit.status = Credit.PAID
    credit.save(update_fields=["status"])
    messages.success(request, "Credit marque comme paye.")
    return redirect("sales:credit_list")


@login_required
@permission_required(Permissions.VIEW_REPORTS)
def rapport_periodique(request):
    antennes_qs = Antenne.objects.all().order_by("nom")
    form = ReportingPeriodForm(request.GET or {"period": "day"}, antennes_qs=antennes_qs)

    selected_period = "day"
    selected_antenne = None
    if form.is_valid():
        selected_period = form.cleaned_data["period"]
        selected_antenne = form.cleaned_data.get("antenne")

    start_date, end_date = _get_period_bounds(selected_period)

    sales_qs = Sale.objects.filter(date__range=[start_date, end_date])
    expenses_qs = Expense.objects.filter(created_at__range=[start_date, end_date])
    sales_qs, expenses_qs = _apply_antenne_scope(request.user, sales_qs, expenses_qs)

    if selected_antenne:
        sales_qs = sales_qs.filter(created_by__antenne=selected_antenne)
        expenses_qs = expenses_qs.filter(Q(antenne=selected_antenne) | Q(created_by__antenne=selected_antenne))

    contexte = _build_accounting_context(
        form=form,
        selected_period=selected_period,
        start_date=start_date,
        end_date=end_date,
        sales_qs=sales_qs,
        expenses_qs=expenses_qs,
        selected_antenne=selected_antenne,
    )
    contexte["report_action"] = "sales:rapport_periodique"

    return render(request, "sales/accounting.html", contexte)


@login_required
def mon_rapport_periodique(request):
    antennes_qs = Antenne.objects.filter(pk=request.user.antenne_id) if request.user.antenne_id else Antenne.objects.none()
    form = ReportingPeriodForm(request.GET or {"period": "day"}, antennes_qs=antennes_qs)

    selected_period = "day"
    if form.is_valid():
        selected_period = form.cleaned_data["period"]

    start_date, end_date = _get_period_bounds(selected_period)

    sales_qs = Sale.objects.filter(date__range=[start_date, end_date], created_by=request.user)
    expenses_qs = Expense.objects.filter(created_at__range=[start_date, end_date], created_by=request.user)

    contexte = _build_accounting_context(
        form=form,
        selected_period=selected_period,
        start_date=start_date,
        end_date=end_date,
        sales_qs=sales_qs,
        expenses_qs=expenses_qs,
        selected_antenne=request.user.antenne,
    )
    contexte["report_action"] = "sales:mon_rapport_periodique"

    return render(request, "sales/accounting.html", contexte)
