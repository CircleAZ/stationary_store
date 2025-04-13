from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator
from django.conf import settings # To link to the User model

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories" # Fix pluralization in admin

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'pk': self.pk})

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products') # Prevent deleting category if products exist
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    stock_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    # Add image field later if needed: image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'pk': self.pk})

    def is_in_stock(self):
        return self.stock_quantity > 0

class Customer(models.Model):
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(help_text="Full address for delivery")
    # For location: Simple text field for now.
    # Alternatively, use separate lat/lon DecimalFields or a dedicated GeoDjango field later.
    location_notes = models.CharField(max_length=255, blank=True, null=True, help_text="Optional: Landmarks, specific instructions, or Lat/Lon")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('customer_detail', kwargs={'pk': self.pk})

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('PARTIAL', 'Partially Paid'),
        ('PAID', 'Paid'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders') # Protect customer data
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0.00)])
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='PENDING')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_orders') # Track who created the order
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Order #{self.pk} for {self.customer.name} on {self.order_date.strftime('%Y-%m-%d')}"

    def get_absolute_url(self):
        return reverse('order_detail', kwargs={'pk': self.pk})

    def calculate_total(self):
        """Calculates the total amount based on order items."""
        total = sum(item.get_item_total() for item in self.items.all())
        # Only update if the calculated total is different to avoid unnecessary saves
        if self.total_amount != total:
             self.total_amount = total
             # Consider saving here or letting the view handle the save
             # self.save(update_fields=['total_amount'])
        return self.total_amount

    def get_amount_due(self):
        return self.total_amount - self.amount_paid

    def update_status(self):
        """Updates the order status based on payment."""
        if self.status in ['DELIVERED', 'CANCELLED']: # Don't automatically change these statuses
             return
        if self.amount_paid <= 0:
            self.status = 'PENDING'
        elif self.amount_paid < self.total_amount:
            self.status = 'PARTIAL'
        else:
            self.status = 'PAID'
        # Again, consider saving here or letting the view handle it.
        # self.save(update_fields=['status'])

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT) # Protect product data
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    # Store the price at the time of order, as product price might change later
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('order', 'product') # Prevent adding the same product twice to one order

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order #{self.order.pk}"

    def get_item_total(self):
        return self.quantity * self.price_at_order

    def save(self, *args, **kwargs):
        # Automatically set the price when creating the item
        if not self.pk and not self.price_at_order: # If new instance and price not set
            self.price_at_order = self.product.price
        super().save(*args, **kwargs)
        # Optional: Recalculate order total after saving an item
        # self.order.calculate_total()
        # self.order.save() # Be careful about recursion or multiple saves