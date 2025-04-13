from django import forms
from .models import Product, Category, Customer, Order, OrderItem

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price', 'stock_quantity']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone_number', 'email', 'address', 'location_notes']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
             'location_notes': forms.Textarea(attrs={'rows': 2}),
        }

# Quick Customer form (maybe fewer fields initially)
class QuickCustomerForm(forms.ModelForm):
     class Meta:
        model = Customer
        fields = ['name', 'phone_number', 'address'] # Start with essential fields
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
        }

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer', 'amount_paid', 'status', 'notes'] # Total is calculated, date is auto
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    # Optional: Customize the customer field widget if needed (e.g., using Select2)
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['customer'].queryset = Customer.objects.order_by('name')


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']

    # Optional: Filter product choices, e.g., show only in-stock items
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['product'].queryset = Product.objects.filter(stock_quantity__gt=0).order_by('name')


# Formset for handling multiple OrderItems within an Order view
OrderItemFormSet = forms.inlineformset_factory(
    Order,       # Parent model
    OrderItem,   # Child model
    form=OrderItemForm, # Form to use for each item
    fields=('product', 'quantity'), # Fields to include in the formset
    extra=1,      # Number of empty forms to display
    can_delete=True # Allow deleting items from the order
)