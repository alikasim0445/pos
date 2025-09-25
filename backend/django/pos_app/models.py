from django.db import models

class Warehouse(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    capacity = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    warehouse = models.ForeignKey(Warehouse, related_name='products', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Sale(models.Model):
    product = models.ForeignKey(Product, related_name='sales', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    sale_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Sale of {self.quantity} {self.product.name}(s) on {self.sale_date}'