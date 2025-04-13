from django.contrib import admin
from .models import Category, Product, Customer, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock_quantity', 'is_in_stock', 'updated_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description', 'category__name')
    list_editable = ('price', 'stock_quantity') # Allow quick edits in the list view

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'email', 'address', 'created_at')
    search_fields = ('name', 'phone_number', 'email', 'address')

class OrderItemInline(admin.TabularInline): # Display order items directly within the order admin page
    model = OrderItem
    extra = 1 # Number of empty forms to display
    readonly_fields = ('price_at_order',) # Don't allow editing historical price here
    # Add autocomplete for product selection if you have many products
    # autocomplete_fields = ['product']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'order_date', 'status', 'total_amount', 'amount_paid', 'get_amount_due', 'created_by')
    list_filter = ('status', 'order_date', 'customer')
    search_fields = ('id', 'customer__name', 'customer__phone_number', 'items__product__name')
    readonly_fields = ('order_date', 'total_amount') # Total amount calculated automatically
    inlines = [OrderItemInline] # Add the inline items
    list_editable = ('status', 'amount_paid')

    # If using autocomplete_fields in OrderItemInline
    # search_fields = ProductAdmin.search_fields # Make products searchable for autocomplete

    def save_model(self, request, obj, form, change):
        """Assign current user when creating an order in admin."""
        if not obj.pk: # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        """Recalculate total and update status after saving related items (OrderItems)."""
        super().save_related(request, form, formsets, change)
        order = form.instance
        order.calculate_total()
        order.update_status()
        order.save() # Save the updated total and status


# Note: OrderItem doesn't usually need its own admin registration
# if it's handled effectively via the OrderAdmin inline.
# @admin.register(OrderItem)
# class OrderItemAdmin(admin.ModelAdmin):
#     list_display = ('order', 'product', 'quantity', 'price_at_order', 'get_item_total')
#     list_filter = ('order__customer', 'product__category')
#     search_fields = ('order__id', 'product__name')