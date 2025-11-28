# identity.py
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from auth.models import SoftDeleteModel, SoftDeleteManager
import json
from decimal import Decimal

class BusinessType(SoftDeleteModel):
    """Type de business (Cybercafé, Restaurant, Boutique, etc.)"""
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icone = models.CharField(max_length=50, default='fas fa-store')
    couleur_principale = models.CharField(max_length=7, default='#007bff')
    
    def __str__(self):
        return self.nom
    
    class Meta:
        verbose_name = "Type de Business"
        verbose_name_plural = "Types de Business"

class ConfigurationBusiness(SoftDeleteModel):
    """Configuration spécifique par type de business"""
    business_type = models.ForeignKey(BusinessType, on_delete=models.CASCADE)
    cle = models.CharField(max_length=100)
    valeur = models.TextField()
    type_valeur = models.CharField(max_length=20, choices=[
        ('entier', 'Entier'),
        ('decimal', 'Décimal'),
        ('texte', 'Texte'),
        ('booleen', 'Booléen'),
        ('json', 'JSON'),
    ])
    description = models.TextField(blank=True)
    
    def get_valeur_typede(self):
        if self.type_valeur == 'entier':
            return int(self.valeur)
        elif self.type_valeur == 'decimal':
            return Decimal(self.valeur)
        elif self.type_valeur == 'booleen':
            return self.valeur.lower() == 'true'
        elif self.type_valeur == 'json':
            return json.loads(self.valeur)
        return self.valeur
    
    class Meta:
        unique_together = ['business_type', 'cle']
        verbose_name = "Configuration Business"
        verbose_name_plural = "Configurations Business"

class Business(SoftDeleteModel):
    """Entreprise/établissement principal"""
    nom = models.CharField(max_length=200)
    type_business = models.ForeignKey(BusinessType, on_delete=models.PROTECT)
    slogan = models.CharField(max_length=255, blank=True)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    
    # Informations de contact
    telephone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    adresse = models.TextField()
    ville = models.CharField(max_length=100)
    pays = models.CharField(max_length=100, default='Tchad')
    
    # Informations légales
    registre_commerce = models.CharField(max_length=100, blank=True)
    id_fiscal = models.CharField(max_length=100, blank=True)
    
    # Configuration
    devise = models.CharField(max_length=10, default='FCFA')
    fuseau_horaire = models.CharField(max_length=50, default='Africa/Ndjamena')
    langue = models.CharField(max_length=10, default='fr')
    
    # Statut
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nom} ({self.type_business.nom})"
    
    def get_configuration(self, cle, defaut=None):
        try:
            config = ConfigurationBusiness.objects.get(
                business_type=self.type_business,
                cle=cle,
                is_deleted=False
            )
            return config.get_valeur_typede()
        except ConfigurationBusiness.DoesNotExist:
            return defaut
    
    @property
    def nombre_etablissements(self):
        return self.etablissements.filter(is_deleted=False).count()
    
    @property
    def nombre_utilisateurs(self):
        return self.utilisateurs.filter(is_deleted=False, actif=True).count()
    
    class Meta:
        verbose_name = "Business"
        verbose_name_plural = "Businesses"

class Etablissement(SoftDeleteModel):
    """Établissement physique (succursale, antenne)"""
    STATUT_ETABLISSEMENT = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('maintenance', 'En Maintenance'),
        ('construction', 'En Construction'),
    ]
    
    TYPE_ETABLISSEMENT = [
        ('principal', 'Établissement Principal'),
        ('succursale', 'Succursale'),
        ('kiosque', 'Kiosque'),
        ('mobile', 'Unité Mobile'),
        ('entrepot', 'Entrepôt'),
    ]
    
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='etablissements')
    nom = models.CharField(max_length=100)
    type_etablissement = models.CharField(max_length=50, choices=TYPE_ETABLISSEMENT, default='succursale')
    
    # Localisation
    adresse = models.TextField()
    ville = models.CharField(max_length=100)
    quartier = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Contact
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Gestion
    gerant = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='etablissements_geres')
    capacite_clients = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    statut = models.CharField(max_length=15, choices=STATUT_ETABLISSEMENT, default='actif')
    date_ouverture = models.DateField(null=True, blank=True)
    
    # Configuration spécifique
    horaires_ouverture = models.JSONField(default=dict, blank=True)
    services_disponibles = models.JSONField(default=list, blank=True)
    
    # Métriques
    surface = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Surface en m²")
    
    def __str__(self):
        return f"{self.nom} - {self.business.nom}"
    
    @property
    def est_ouvert(self):
        from datetime import datetime
        now = datetime.now()
        jour_semaine = now.strftime('%A').lower()
        heure_actuelle = now.strftime('%H:%M')
        
        horaires = self.horaires_ouverture.get(jour_semaine, {})
        ouverture = horaires.get('ouverture')
        fermeture = horaires.get('fermeture')
        
        if ouverture and fermeture:
            return ouverture <= heure_actuelle <= fermeture
        return False
    
    @property
    def nombre_employes(self):
        return self.utilisateurs.filter(is_deleted=False, actif=True).count()
    
    def get_horaires_jour(self, jour):
        """Retourne les horaires pour un jour spécifique"""
        return self.horaires_ouverture.get(jour, {})
    
    class Meta:
        verbose_name = "Établissement"
        verbose_name_plural = "Établissements"
        ordering = ['business', 'nom']