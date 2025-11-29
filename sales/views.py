from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from sales.filters import SaleFilter
from .models import Category, Product, Sale
from .forms import CategoryForm, ProductForm, SaleForm
from accounts.permissions import Permissions
from accounts.decorators import role_required, permission_required  # Import des décorateurs
from django.core.paginator import Paginator
# --- Categories ---

@login_required
@role_required('admin', 'manager')  # Exemple de rôle nécessaire pour accéder à cette vue
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'sales/category_list.html', {'categories': categories})

@login_required
@permission_required(Permissions.MANAGE_ANTENNES)  # Permission nécessaire pour créer une catégorie
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
@permission_required(Permissions.MANAGE_ANTENNES)  # Permission nécessaire pour mettre à jour une catégorie
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Catégorie '{category.name}' mise à jour.")
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
@permission_required(Permissions.MANAGE_TREASURY)  # Permission nécessaire pour créer un produit
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
@permission_required(Permissions.MANAGE_TREASURY)  # Permission nécessaire pour mettre à jour un produit
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
@permission_required(Permissions.MANAGE_CATEGORIES)  # Permission nécessaire pour supprimer une catégorie
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == "POST":
        category.delete()
        messages.success(request, f"Catégorie '{category.name}' supprimée avec succès.")
        return redirect("sales:category_list")

    return render(request, "sales/category_confirm_delete.html", {"category": category})

# --- PRODUCT DELETE ---

@login_required
@permission_required(Permissions.MANAGE_PRODUCTS)  # Permission nécessaire pour supprimer un produit
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        product.delete()
        messages.success(request, f"Produit '{product.name}' supprimé avec succès.")
        return redirect("sales:product_list")

    return render(request, "sales/product_confirm_delete.html", {"product": product})


@login_required
def sale_create(request):
    if request.method == 'POST':
        form = SaleForm(request.POST, user=request.user)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.status = Sale.VALIDATED  # Définir le statut à "Pending"
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
            messages.success(request, "La vente a été mise à jour et est toujours en attente de validation.")
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
        messages.info(request, "Cette vente n'est pas en attente de validation.")

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
        messages.info(request, "Cette vente n'est pas en attente de validation.")

    return redirect('sales:sale_list')


@login_required
def sale_list(request):

    queryset = Sale.objects.all().order_by('-created_at')

    sale_filter = SaleFilter(request.GET, queryset=queryset)
    filtered_qs = sale_filter.qs

    paginator = Paginator(filtered_qs, 10)  # 10 ventes par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'filter': sale_filter,
    }
    return render(request, 'sales/sale_list.html', {'page_obj': page_obj, 'filter': sale_filter,})

