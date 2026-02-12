from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import Antenne, User, Ville
from sales.models import Category, Product, Sale


class SaleCreateValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="gerant1",
            password="testpass123",
            role=User.Role.GERANT,
        )
        self.ville = Ville.objects.create(name="Kinshasa")
        self.antenne = Antenne.objects.create(nom="Antenne A", lieux=self.ville, gerant=self.user)
        self.user.antenne = self.antenne
        self.user.save(update_fields=["antenne"])

        category = Category.objects.create(name="Impression test", type="service", is_validated=True)
        self.product = Product.objects.create(
            category=category,
            name="Impression A4",
            standard_price=Decimal("200.00"),
            is_active=True,
            is_validated=True,
        )

    def test_sale_created_by_non_validator_is_auto_validated(self):
        self.client.login(username="gerant1", password="testpass123")
        response = self.client.post(
            reverse("sales:sale_create"),
            data={
                "product": self.product.pk,
                "quantity": 2,
                "customer": "Client Test",
                "payment_method": "Cash",
                "status": Sale.PENDING,
            },
        )

        self.assertEqual(response.status_code, 302)
        sale = Sale.objects.latest("id")
        self.assertEqual(sale.status, Sale.VALIDATED)
