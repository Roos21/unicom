from django.db import migrations

def create_products(apps, schema_editor):
    Category = apps.get_model('sales', 'Category')
    Product = apps.get_model('sales', 'Product')

    # Services
    services = [
        ("Photocopie NB", 50, "page", "Photocopie"),
        ("Impression NB", 100, "page", "Impression"),
        ("Saisie document", 200, "page", "Saisie"),
        ("Scan simple", 300, "document", "Scan"),
        ("Plastification", 500, "document", "Plastification"),
        ("Reliure", 400, "document", "Reliure"),
        ("Connexion PC", 150, "heure", "Connexion PC"),
        ("Impression Photo", 200, "photo", "Impression Photo"),
    ]

    for name, price, unit, cat_name in services:
        category = Category.objects.get(name=cat_name)
        Product.objects.create(name=name, price=price, unit=unit, category=category)

    # Biens
    biens = [
        ("Ticket 1h", 500, "ticket", "Tickets abonnement"),
        ("Ticket 5h", 2000, "ticket", "Tickets abonnement"),
        ("Feuille A4", 50, "feuille", "Feuille A4"),
        ("Feuille A3", 100, "feuille", "Feuille A3"),
        ("Enveloppe", 150, "unité", "Enveloppe"),
        ("Clé USB 8Go", 3000, "unité", "Clé USB"),
        ("Stylo bille", 100, "unité", "Stylo")
    ]

    for name, price, unit, cat_name in biens:
        category = Category.objects.get(name=cat_name)
        Product.objects.create(name=name, price=price, unit=unit, category=category)


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_products),
    ]
