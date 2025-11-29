from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from accounts.models import User
from accounts.permissions import ROLE_PER_LEVEL, Permissions
from expense.filters import ExpenseFilter
from .models import Expense, ApprovalStep, ValidationThreshold, Transaction
from accounts.decorators import permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from expense.models import Expense, AccountMoney, ExpenseCategory
from expense.forms import ExpenseForm
from accounts.decorators import permission_required
from django.db import models
from django.core.paginator import Paginator

# -------------------------
# Liste des dépenses
# -------------------------
@login_required
@permission_required(Permissions.VIEW_DEPENSES)
def expense_list(request):
    qs = Expense.objects.all().order_by('-created_at')
    expense_filter = ExpenseFilter(request.GET, queryset=qs)
    paginator = Paginator(expense_filter.qs, 10)  # 10 par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'filter': expense_filter,
        'expenses': page_obj
    }
    return render(request, 'expenses/expenses_list.html', context)

# -------------------------
# Ajouter une dépense
# -------------------------
@login_required
@permission_required(Permissions.MANAGE_TREASURY)
def expense_create(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.status = "PENDING"
            expense.save()

            amount = expense.amount

            # On récupère tous les niveaux configurés
            thresholds = ValidationThreshold.objects.all()

            print(thresholds)

            for t in thresholds:
                # Est-ce que le montant appartient à ce niveau ?
                if amount >= t.min_amount and (t.max_amount is None or amount <= t.max_amount):

                    # On crée l'étape correspondante à ce niveau
                    ApprovalStep.objects.create(
                        expense=expense,
                        level=t.level,
                        role=t.role,
                        approved=False,
                        rejected=False
                    )

            messages.success(
                request,
                "Dépense créée avec succès. Le workflow d’approbation va commencer."
            )
            return redirect("expenses:expense_list")

    else:
        form = ExpenseForm(user=request.user)

    return render(request, "expenses/expense_form.html", {
        "form": form,
        "title": "Nouvelle dépense"
    })

# -------------------------
# Modifier une dépense
# -------------------------
@login_required
@permission_required(Permissions.MANAGE_TREASURY)
def expense_update(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Dépense mise à jour avec succès !")
            return redirect('expenses:expense_list')
    else:
        form = ExpenseForm(instance=expense, user=request.user)
    return render(request, 'expenses/expense_form.html', {'form': form, 'title': 'Modifier dépense'})

# -------------------------
# Supprimer une dépense
# -------------------------
@login_required
@permission_required(Permissions.MANAGE_TREASURY)
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == "POST":
        expense.delete()
        messages.success(request, "Dépense supprimée avec succès !")
        return redirect('expenses:expense_list')
    return render(request, 'expenses/expense_confirm_delete.html', {'expense': expense})




@login_required
@permission_required(Permissions.VALIDATE_DEPENSES)
def pending_expenses_list(request):
    """
    Affiche les dépenses en attente ou en cours de validation
    """
    expenses = Expense.objects.filter(status__in=['PENDING', 'IN_REVIEW']).order_by('-created_at')
    context = {
        'expenses': expenses
    }
    return render(request, 'expenses/pending_list.html', context)


@login_required
@permission_required(Permissions.VALIDATE_DEPENSES)
def approve_expense(request, expense_id):
    """
    Approuve une dépense pour le niveau de l'utilisateur
    """
    expense = get_object_or_404(Expense, id=expense_id)

    # Récupération de la première étape non approuvée
    step = ApprovalStep.objects.filter(
        expense=expense, 
        approved=False
    ).first()

    if not step:
        messages.error(request, "Vous n'avez pas de validation à effectuer pour cette dépense.")
        return redirect('expenses:pending_expenses')

    # Approuver
    step.approved = True
    step.rejected = False
    step.validated_at = timezone.now()
    step.save()

    # Vérifier si tous les niveaux sont validés
    total_steps = ApprovalStep.objects.filter(expense=expense).count()
    approved_steps = ApprovalStep.objects.filter(expense=expense, approved=True).count()

    if approved_steps == total_steps:
        expense.status = 'APPROVED'
        # Créer la transaction correspondante
        Transaction.objects.create(
            account=expense.account,
            type='OUT',
            amount=expense.amount,
            expense=expense
        )
    else:
        expense.status = 'IN_REVIEW'

    expense.save()
    messages.success(request, f"Dépense '{expense.title}' approuvée avec succès !")
    return redirect('expenses:pending_expenses')


@login_required
@permission_required(Permissions.VALIDATE_DEPENSES)
def reject_expense(request, expense_id):
    """
    Rejette une dépense pour le niveau de l'utilisateur
    """
    expense = get_object_or_404(Expense, id=expense_id)

    # Récupération du niveau de validation correspondant à l'utilisateur
    try:
        step = ApprovalStep.objects.get(expense=expense, approver=request.user)
    except ApprovalStep.DoesNotExist:
        messages.error(request, "Vous n'avez pas de validation à effectuer pour cette dépense.")
        return redirect('expenses:pending_expenses')

    if step.rejected:
        messages.info(request, "Vous avez déjà rejeté cette dépense.")
        return redirect('expenses:pending_expenses')

    # Rejeter
    step.approved = False
    step.rejected = True
    step.validated_at = timezone.now()
    step.save()

    # Mettre à jour le statut global de la dépense
    expense.status = 'REJECTED'
    expense.save()

    messages.success(request, f"Dépense '{expense.title}' rejetée.")
    return redirect('expenses:pending_expenses')
