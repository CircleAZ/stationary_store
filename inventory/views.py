from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin # For CBVs
from django.contrib.auth.decorators import login_required # For FBVs
from django.contrib import messages
from django.db import transaction # For atomic operations (like saving order + items)

from .models import Product, Category, Customer, Order, OrderItem
from .forms import ProductForm, CategoryForm, CustomerForm, QuickCustomerForm, OrderForm, OrderItemFormSet

# --- Home View ---
class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_products'] = Product.objects.count()
        context['total_customers'] = Customer.objects.count()
        context['recent_orders'] = Order.objects.order_by('-order_date')[:5]
        # Add more dashboard stats as needed
        return context

# --- Category Views (Using CBVs) ---
class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'inventory/category_list.html'
    context_object_name = 'categories'

class CategoryDetailView(LoginRequiredMixin, DetailView):
    model = Category
    template_name = 'inventory/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.filter(category=self.object)
        return context

class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'inventory/category_form.html'
    success_url = reverse_lazy('category_list')

    def form_valid(self, form):
        messages.success(self.request, "Category created successfully.")
        return super().form_valid(form)

class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'inventory/category_form.html'
    success_url = reverse_lazy('category_list') # Or redirect to detail view

    def form_valid(self, form):
        messages.success(self.request, "Category updated successfully.")
        return super().form_valid(form)

class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'inventory/category_confirm_delete.html'
    success_url = reverse_lazy('category_list')

    def post(self, request, *args, **kwargs):
        # Optional: Add check here to prevent deletion if products exist,
        # even though models.PROTECT should handle it at DB level.
        category = self.get_object()
        if category.products.exists():
             messages.error(request, f"Cannot delete category '{category.name}' because it has associated products.")
             return redirect('category_list') # Or category detail

        messages.success(request, f"Category '{category.name}' deleted successfully.")
        return super().post(request, *args, **kwargs)


# --- Product Views (Using CBVs) ---
class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'inventory/product_list.html'
    context_object_name = 'products'
    paginate_by = 15 # Optional pagination

    def get_queryset(self):
        queryset = super().get_queryset().select_related('category').order_by('name')
        # Optional filtering:
        # category_filter = self.request.GET.get('category')
        # if category_filter:
        #     queryset = queryset.filter(category__id=category_filter)
        return queryset

class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'inventory/product_detail.html'
    context_object_name = 'product'

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    success_url = reverse_lazy('product_list')

    def form_valid(self, form):
        messages.success(self.request, "Product created successfully.")
        return super().form_valid(form)

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    success_url = reverse_lazy('product_list')

    def form_valid(self, form):
        messages.success(self.request, "Product updated successfully.")
        return super().form_valid(form)

class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = 'inventory/product_confirm_delete.html'
    success_url = reverse_lazy('product_list')

    def post(self, request, *args, **kwargs):
        product = self.get_object()
        # Basic check if product is in any NON-CANCELLED order items
        if OrderItem.objects.filter(product=product).exclude(order__status='CANCELLED').exists():
             messages.error(request, f"Cannot delete product '{product.name}' as it exists in past orders. Consider deactivating it instead.")
             return redirect('product_list') # Or product detail

        messages.success(request, f"Product '{product.name}' deleted successfully.")
        return super().post(request, *args, **kwargs)


# --- Customer Views (Using CBVs) ---
class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'inventory/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 20

class CustomerDetailView(LoginRequiredMixin, DetailView):
    model = Customer
    template_name = 'inventory/customer_detail.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['orders'] = Order.objects.filter(customer=self.object).order_by('-order_date')
        return context

class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm # Use the full form here
    template_name = 'inventory/customer_form.html'
    success_url = reverse_lazy('customer_list') # Redirect to list after creation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = "Add New Customer"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Customer created successfully.")
        return super().form_valid(form)

# View specifically for quick customer creation (e.g., from order page)
@login_required
def quick_customer_create(request):
    if request.method == 'POST':
        form = QuickCustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f"Quick Customer '{customer.name}' created.")
            # Redirect back to where they came from, or maybe the new customer's detail page
            # Or potentially redirect to order creation with this customer pre-selected
            # For simplicity, redirect to customer list for now
            return redirect('customer_list')
    else:
        form = QuickCustomerForm()

    return render(request, 'inventory/quick_customer_form.html', {'form': form})


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'inventory/customer_form.html'
    # success_url = reverse_lazy('customer_list') # Or detail view

    def get_success_url(self):
        return reverse('customer_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = "Edit Customer"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Customer updated successfully.")
        return super().form_valid(form)

class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    template_name = 'inventory/customer_confirm_delete.html'
    success_url = reverse_lazy('customer_list')

    def post(self, request, *args, **kwargs):
         customer = self.get_object()
         # Prevent deleting customer if they have orders (use PROTECT in model)
         if customer.orders.exists():
             messages.error(request, f"Cannot delete customer '{customer.name}' because they have existing orders.")
             return redirect('customer_detail', pk=customer.pk)

         messages.success(request, f"Customer '{customer.name}' deleted successfully.")
         return super().post(request, *args, **kwargs)


# --- Order Views (More complex, using FBVs might be easier for create/update) ---
class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'inventory/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        # Improve performance by prefetching related customer and user
        return Order.objects.select_related('customer', 'created_by').order_by('-order_date')


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'inventory/order_detail.html' # This will be the "Bill"
    context_object_name = 'order'

    def get_queryset(self):
        # Prefetch items and their products for efficiency
        return super().get_queryset().prefetch_related('items__product')

# Order Creation (using FBV for handling formset)
@login_required
@transaction.atomic # Ensure order and items are saved together or not at all
def order_create(request):
    if request.method == 'POST':
        order_form = OrderForm(request.POST)
        # Pass prefix to distinguish item forms in the request POST data
        item_formset = OrderItemFormSet(request.POST, prefix='items')

        if order_form.is_valid() and item_formset.is_valid():
            # Create the order object but don't save to DB yet
            order = order_form.save(commit=False)
            order.created_by = request.user # Assign the logged-in user
            # Initial save to get an ID for linking items
            order.save()

            # Now save the items linked to this order
            items = item_formset.save(commit=False)
            for item in items:
                item.order = order
                # Ensure price_at_order is set (redundant if model save does it, but safe)
                if not item.price_at_order:
                     item.price_at_order = item.product.price
                item.save()
                # *** Important: Update product stock quantity ***
                product = item.product
                product.stock_quantity -= item.quantity
                # Add validation here: check if stock is sufficient before saving!
                # if product.stock_quantity < 0:
                #     raise forms.ValidationError(f"Not enough stock for {product.name}") # This should ideally be in formset clean
                product.save(update_fields=['stock_quantity'])


            # Save the formset (handles deletions if any)
            item_formset.save_m2m()

            # Recalculate total and update status after items are saved
            order.calculate_total() # Calculate based on saved items
            order.update_status()   # Update status based on amount_paid
            order.save()            # Final save with correct total and status

            messages.success(request, f"Order #{order.pk} created successfully.")
            return redirect('order_detail', pk=order.pk)
        else:
             messages.error(request, "Please correct the errors below.")
    else:
        order_form = OrderForm()
        item_formset = OrderItemFormSet(prefix='items', queryset=OrderItem.objects.none()) # Empty formset for GET

    context = {
        'order_form': order_form,
        'item_formset': item_formset,
        'form_title': 'Create New Order'
    }
    return render(request, 'inventory/order_form.html', context)

# Order Update (similar structure to create, but with instance)
@login_required
@transaction.atomic
def order_update(request, pk):
    order = get_object_or_404(Order, pk=pk)
    # Store initial quantities before form processing to calculate stock changes
    initial_quantities = {item.product.id: item.quantity for item in order.items.all()}

    if request.method == 'POST':
        order_form = OrderForm(request.POST, instance=order)
        item_formset = OrderItemFormSet(request.POST, instance=order, prefix='items')

        if order_form.is_valid() and item_formset.is_valid():
            # Save the main order form changes (customer, amount paid, status, notes)
            order = order_form.save(commit=False) # Don't commit yet

            # Process formset items (new, changed, deleted)
            # Handle stock adjustments BEFORE saving formset
            # Deleted items: stock should be added back
            for form in item_formset.deleted_forms:
                 if form.instance.pk: # If it's an existing item being deleted
                     product = form.instance.product
                     product.stock_quantity += form.instance.quantity
                     product.save(update_fields=['stock_quantity'])

            # New/Changed items: adjust stock based on difference
            items_to_save = []
            for form in item_formset.forms:
                 if form.is_valid() and form.has_changed() and not form.cleaned_data.get('DELETE', False):
                     item = form.save(commit=False)
                     product = item.product
                     new_quantity = item.quantity
                     original_quantity = initial_quantities.get(product.id, 0)
                     stock_change = new_quantity - original_quantity

                     # Check stock availability ONLY IF quantity increased or it's a new item
                     if stock_change > 0:
                          if product.stock_quantity < stock_change:
                               # Not enough stock, add form error and stop
                               form.add_error('quantity', f"Not enough stock for {product.name}. Available: {product.stock_quantity}")
                               messages.error(request, f"Insufficient stock for {product.name}.")
                               # Re-render the form with errors
                               context = {'order_form': order_form, 'item_formset': item_formset, 'order': order, 'form_title': 'Edit Order'}
                               return render(request, 'inventory/order_form.html', context)

                     # Adjust stock (can be negative if quantity decreased)
                     product.stock_quantity -= stock_change
                     product.save(update_fields=['stock_quantity'])

                     # Ensure price_at_order is set for NEW items
                     if not item.pk:
                         item.price_at_order = product.price

                     items_to_save.append(item)


            # Now save the order and the processed items
            order.save() # Save changes to order fields
            for item in items_to_save:
                item.order = order # Ensure link is set
                item.save()

            # Officially save the formset (handles actual deletions)
            item_formset.save()


            # Recalculate total and update status
            order.calculate_total()
            order.update_status()
            order.save()

            messages.success(request, f"Order #{order.pk} updated successfully.")
            return redirect('order_detail', pk=order.pk)
        else:
            messages.error(request, "Please correct the errors below.")

    else: # GET request
        order_form = OrderForm(instance=order)
        item_formset = OrderItemFormSet(instance=order, prefix='items')

    context = {
        'order_form': order_form,
        'item_formset': item_formset,
        'order': order, # Pass the order object for context in the template
        'form_title': f'Edit Order #{order.pk}'
    }
    return render(request, 'inventory/order_form.html', context)


# Simple Order Delete View (Consider if you really want to delete orders)
# Maybe an 'archive' or 'cancel' status is better.
class OrderDeleteView(LoginRequiredMixin, DeleteView):
    model = Order
    template_name = 'inventory/order_confirm_delete.html'
    success_url = reverse_lazy('order_list')

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        order = self.get_object()
        # Add stock back for items in the deleted order
        for item in order.items.all():
            product = item.product
            product.stock_quantity += item.quantity
            product.save(update_fields=['stock_quantity'])

        messages.success(request, f"Order #{order.pk} deleted and stock restored.")
        # Use super().post() AFTER adjusting stock
        return super().post(request, *args, **kwargs)