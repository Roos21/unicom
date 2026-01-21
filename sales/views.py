from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# Si vous voulez le jour courant, sinon vous passerez la date en paramètre
from datetime import date, timedelta, timezone
from expense.models import AccountMoney, Expense
from sales.filters import SaleFilter
from .models import Category, Product, Sale
from .forms import CategoryForm, ProductForm, ReportingPeriodForm, SaleForm
from accounts.permissions import Permissions
# Import des décorateurs
from accounts.decorators import role_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Sum
from django.utils import timezone
from collections import defaultdict
# --- Categories ---


@login_required
# Exemple de rôle nécessaire pour accéder à cette vue
@role_required('admin', 'manager')
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'sales/category_list.html', {'categories': categories})


@login_required
# Permission nécessaire pour créer une catégorie
@permission_required(Permissions.MANAGE_ANTENNES)
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie créée avec succès.")
            return redirect('sales:category_list')
    else:
        form = CategoryForm(user=request.user)
    return render(request, 'sales/category_form.html', {'form': form})


@login_required
# Permission nécessaire pour mettre à jour une catégorie
@permission_required(Permissions.MANAGE_ANTENNES)
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(
                request, f"Catégorie '{category.name}' mise à jour.")
            return redirect('sales:category_list')
    else:
        form = CategoryForm(instance=category, user=request.user)
    return render(request, 'sales/category_form.html', {'form': form})


@login_required
@role_required('admin')  # Seul un administrateur peut valider
def category_validate(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.is_validated = True
    category.save()
    messages.success(request, f"Catégorie '{category.name}' validée.")
    return redirect('sales:category_list')

# --- Products ---


@login_required
def product_list(request):
    products = Product.objects.all()  # Récupérer tous les produits
    paginator = Paginator(products, 15)  # Afficher 10 produits par page

    page_number = request.GET.get('page')  # Récupérer le numéro de la page
    page_obj = paginator.get_page(page_number)  # Obtenir la page actuelle

    return render(request, 'sales/product_list.html', {'page_obj': page_obj})


@login_required
# Permission nécessaire pour créer un produit
@permission_required(Permissions.MANAGE_TREASURY)
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit créé avec succès.")
            return redirect('sales:product_list')
    else:
        form = ProductForm(user=request.user)
    return render(request, 'sales/product_form.html', {'form': form})


@login_required
# Permission nécessaire pour mettre à jour un produit
@permission_required(Permissions.MANAGE_TREASURY)
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Produit '{product.name}' mis à jour.")
            return redirect('sales:product_list')
    else:
        form = ProductForm(instance=product, user=request.user)
    return render(request, 'sales/product_form.html', {'form': form})


@login_required
@role_required('admin')  # Seul un administrateur peut valider
def product_validate(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_validated = True
    product.save()
    messages.success(request, f"Produit '{product.name}' validé.")
    return redirect('sales:product_list')

# --- CATEGORY DELETE ---


@login_required
# Permission nécessaire pour supprimer une catégorie
@permission_required(Permissions.MANAGE_CATEGORIES)
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == "POST":
        category.delete()
        messages.success(
            request, f"Catégorie '{category.name}' supprimée avec succès.")
        return redirect("sales:category_list")

    return render(request, "sales/category_confirm_delete.html", {"category": category})

# --- PRODUCT DELETE ---


@login_required
# Permission nécessaire pour supprimer un produit
@permission_required(Permissions.MANAGE_PRODUCTS)
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        product.delete()
        messages.success(
            request, f"Produit '{product.name}' supprimé avec succès.")
        return redirect("sales:product_list")

    return render(request, "sales/product_confirm_delete.html", {"product": product})


@login_required
def sale_create(request):
    if request.method == 'POST':
        form = SaleForm(request.POST, user=request.user)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.status = Sale.VALIDATED  
            sale.created_by=request.user
            sale.save()
            messages.success(request, "La vente a été créée ")
            return redirect('sales:sale_list')
    else:
        form = SaleForm(user=request.user)

    return render(request, 'sales/sale_form.html', {'form': form})


@login_required
def sale_update(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        form = SaleForm(request.POST, instance=sale, user=request.user)
        if form.is_valid():
            # Mettre à jour le statut à "Pending" avant de sauvegarder
            sale.last_total_price = sale.total_price
            sale.save()

            sale = form.save(commit=False)
            sale.status = Sale.PENDING  # Forcer le statut à "Pending" pour la mise à jour
            # Calculer le total_price basé sur le produit et la quantité
            sale.total_price = sale.product.price * sale.quantity
            sale.save()
            messages.success(
                request, "La vente a été mise à jour et est toujours en attente de validation.")
            return redirect('sales:sale_list')
    else:
        form = SaleForm(instance=sale, user=request.user)

    return render(request, 'sales/sale_form.html', {'form': form})


@login_required
@permission_required(Permissions.VALIDATE_UPDATE_SALES)
def sale_validate(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    # Valider la vente
    if sale.status == Sale.PENDING:
        sale.status = Sale.VALIDATED
        sale.save()
        messages.success(request, "La vente a été validée avec succès.")
    else:
        messages.info(
            request, "Cette vente n'est pas en attente de validation.")

    return redirect('sales:sale_list')


@login_required
@permission_required(Permissions.VALIDATE_UPDATE_SALES)
def sale_reject(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    # Rejeter la vente
    if sale.status == Sale.PENDING:
        sale.status = Sale.REJECTED
        sale.save()
        messages.success(request, "La modification de la vente a été rejetée.")
    else:
        messages.info(
            request, "Cette vente n'est pas en attente de validation.")

    return redirect('sales:sale_list')


@login_required
def sale_list(request):

    queryset = Sale.objects.filter(
        created_by=request.user).order_by('-created_at')

    sale_filter = SaleFilter(request.GET, queryset=queryset)
    filtered_qs = sale_filter.qs

    solde_caisse = AccountMoney.objects.get_or_create(type='CAISSE', name='Caisse Principale')
    solde_banque = AccountMoney.objects.get_or_create(type='BANQUE')

    paginator = Paginator(filtered_qs, 10)  # 10 ventes par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'filter': sale_filter,
        'solde_caisse': solde_caisse,
        'solde_banque': solde_banque

    }
    return render(request, 'sales/sale_list.html', context)


def rapport_periodique(request):
    
    # 1. Traitement du Formulaire et Détermination des Dates
    
    now = timezone.localtime(timezone.now())
    selected_period = 'day'
    
    # Date de fin par défaut (maintenant, mais arrondie à la fin de la journée pour inclure toutes les transactions)
    # L'heure de fin est ajustée si on ne filtre pas par jour
    end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    # Date de début par défaut (début de la journée)
    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

    form = ReportingPeriodForm(request.GET or {'period': 'day'}) # Si pas de GET, utilise 'day'

    if form.is_valid():
        selected_period = form.cleaned_data['period']

        if selected_period == 'day':
            pass # Les dates par défaut sont déjà le jour actuel
            
        elif selected_period == 'week':
            # Les 7 derniers jours (la semaine passée)
            start_date = start_date - timedelta(days=7)
            
        elif selected_period == 'month':
            # Début du mois actuel
            start_date = start_date.replace(day=1)
            
        elif selected_period == 'quarter':
            # Début du trimestre actuel (logique plus précise)
            current_month = start_date.month
            start_month = ((current_month - 1) // 3) * 3 + 1
            start_date = start_date.replace(month=start_month, day=1)
            
        elif selected_period == 'year':
            # Début de l'année actuelle
            start_date = start_date.replace(month=1, day=1)

    # --- 2. Récupération et Structuration des Ventes ---

    # Utilisation du filtre __range sur le champ date (DateTimeField)
    ventes_validees_de_la_periode = Sale.objects.filter(
        date__range=[start_date, end_date], # Application du filtre de période
        status=Sale.VALIDATED 
    ).select_related('product', 'product__category').order_by('product__category__type', 'product__category__name') 
    
    
    # Le reste de la logique de structuration des ventes reste inchangée
    ventes_detaillees_par_categorie = defaultdict(lambda: {
        'total_par_type': 0,
        'categories': defaultdict(lambda: {
            'total': 0,
            'details': []
        })
    })
    
    for vente in ventes_validees_de_la_periode:
        category_type = vente.product.category.get_type_display() 
        category_name = vente.product.category.name 
        
        ventes_detaillees_par_categorie[category_type]['categories'][category_name]['details'].append({
            'produit': vente.product.name,
            'quantite': vente.quantity,
            'prix_unitaire': vente.product.price, 
            'total_vente': vente.total_price,
            'methode_paiement': vente.get_payment_method_display(),
            'client': vente.customer if vente.customer else 'N/A'
        })
        
        montant = vente.total_price
        ventes_detaillees_par_categorie[category_type]['categories'][category_name]['total'] += montant
        ventes_detaillees_par_categorie[category_type]['total_par_type'] += montant

    final_ventes_structure = {}
    for type_vente, data_type in ventes_detaillees_par_categorie.items():
        data_type['categories'] = dict(data_type['categories']) 
        final_ventes_structure[type_vente] = data_type


    # --- 3. Calculs Agrégés (Totaux Cash/Credit) ---

    ventes_cash_total = ventes_validees_de_la_periode.filter(
        payment_method='Cash'
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    ventes_credit_total = ventes_validees_de_la_periode.filter(
        payment_method='Credit'
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    total_ventes = ventes_cash_total + ventes_credit_total

    # --- 4. Calcul et Regroupement des Dépenses (Sorties) ---
    
    # Utilisation du filtre __range sur le champ created_at (DateTimeField)
    depenses_de_la_periode = Expense.objects.filter(
        created_at__range=[start_date, end_date], # Application du filtre de période
        status='APPROVED' 
    )
    
    depenses_regroupees = depenses_de_la_periode.values(
        'category__name' 
    ).annotate(
        total_depense=Sum('amount')
    ).order_by('category__name')

    total_depenses_global = depenses_de_la_periode.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Le solde net n'inclut que les ventes qui ont été encaissées (Cash)
    solde_net = ventes_cash_total - total_depenses_global 
    
    # --- 5. Préparation du Contexte Final ---

    contexte = {
        # Dates de la période sélectionnée
        'form': form,
        'start_date': start_date, 
        'end_date': end_date,
        'selected_period': selected_period,
        
        # Structure détaillée corrigée
        'ventes_detaillees_par_categorie': final_ventes_structure, 
        
        # Données agrégées 
        'ventes_cash': ventes_cash_total,
        'ventes_credit': ventes_credit_total,
        'total_ventes': total_ventes,
        
        # Dépenses
        'depenses_par_section': depenses_regroupees,
        'total_depenses_global': total_depenses_global,
        
        # Solde
        'solde_net': solde_net,
    }

    return render(request, 'sales/accounting.html', contexte)


def mon_rapport_periodique(request):
    
    # 1. Traitement du Formulaire et Détermination des Dates
    
    now = timezone.localtime(timezone.now())
    selected_period = 'day'
    
    # Date de fin par défaut (maintenant, mais arrondie à la fin de la journée pour inclure toutes les transactions)
    # L'heure de fin est ajustée si on ne filtre pas par jour
    end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    # Date de début par défaut (début de la journée)
    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

    form = ReportingPeriodForm(request.GET or {'period': 'day'}) # Si pas de GET, utilise 'day'

    if form.is_valid():
        selected_period = form.cleaned_data['period']

        if selected_period == 'day':
            pass # Les dates par défaut sont déjà le jour actuel
            
        elif selected_period == 'week':
            # Les 7 derniers jours (la semaine passée)
            start_date = start_date - timedelta(days=7)
            
        elif selected_period == 'month':
            # Début du mois actuel
            start_date = start_date.replace(day=1)
            
        elif selected_period == 'quarter':
            # Début du trimestre actuel (logique plus précise)
            current_month = start_date.month
            start_month = ((current_month - 1) // 3) * 3 + 1
            start_date = start_date.replace(month=start_month, day=1)
            
        elif selected_period == 'year':
            # Début de l'année actuelle
            start_date = start_date.replace(month=1, day=1)

    # --- 2. Récupération et Structuration des Ventes ---

    # Utilisation du filtre __range sur le champ date (DateTimeField)
    ventes_validees_de_la_periode = Sale.objects.filter(
        date__range=[start_date, end_date], # Application du filtre de période
        status=Sale.VALIDATED,
        created_by=request.user
    ).select_related('product', 'product__category').order_by('product__category__type', 'product__category__name') 
    
    
    # Le reste de la logique de structuration des ventes reste inchangée
    ventes_detaillees_par_categorie = defaultdict(lambda: {
        'total_par_type': 0,
        'categories': defaultdict(lambda: {
            'total': 0,
            'details': []
        })
    })
    
    for vente in ventes_validees_de_la_periode:
        category_type = vente.product.category.get_type_display() 
        category_name = vente.product.category.name 
        
        ventes_detaillees_par_categorie[category_type]['categories'][category_name]['details'].append({
            'produit': vente.product.name,
            'quantite': vente.quantity,
            'prix_unitaire': vente.product.price, 
            'total_vente': vente.total_price,
            'methode_paiement': vente.get_payment_method_display(),
            'client': vente.customer if vente.customer else 'N/A'
        })
        
        montant = vente.total_price
        ventes_detaillees_par_categorie[category_type]['categories'][category_name]['total'] += montant
        ventes_detaillees_par_categorie[category_type]['total_par_type'] += montant

    final_ventes_structure = {}
    for type_vente, data_type in ventes_detaillees_par_categorie.items():
        data_type['categories'] = dict(data_type['categories']) 
        final_ventes_structure[type_vente] = data_type


    # --- 3. Calculs Agrégés (Totaux Cash/Credit) ---

    ventes_cash_total = ventes_validees_de_la_periode.filter(
        payment_method='Cash'
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    ventes_credit_total = ventes_validees_de_la_periode.filter(
        payment_method='Credit'
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    total_ventes = ventes_cash_total + ventes_credit_total

    # --- 4. Calcul et Regroupement des Dépenses (Sorties) ---
    
    # Utilisation du filtre __range sur le champ created_at (DateTimeField)
    depenses_de_la_periode = Expense.objects.filter(
        created_at__range=[start_date, end_date], # Application du filtre de période
        status='APPROVED',
        created_by=request.user
    )
    
    depenses_regroupees = depenses_de_la_periode.values(
        'category__name' 
    ).annotate(
        total_depense=Sum('amount')
    ).order_by('category__name')

    total_depenses_global = depenses_de_la_periode.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Le solde net n'inclut que les ventes qui ont été encaissées (Cash)
    solde_net = ventes_cash_total - total_depenses_global 
    
    # --- 5. Préparation du Contexte Final ---

    contexte = {
        # Dates de la période sélectionnée
        'form': form,
        'start_date': start_date, 
        'end_date': end_date,
        'selected_period': selected_period,
        
        # Structure détaillée corrigée
        'ventes_detaillees_par_categorie': final_ventes_structure, 
        
        # Données agrégées 
        'ventes_cash': ventes_cash_total,
        'ventes_credit': ventes_credit_total,
        'total_ventes': total_ventes,
        
        # Dépenses
        'depenses_par_section': depenses_regroupees,
        'total_depenses_global': total_depenses_global,
        
        # Solde
        'solde_net': solde_net,
    }

    return render(request, 'sales/accounting.html', contexte)