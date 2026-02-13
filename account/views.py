from multiprocessing import context
import json
from pickle import GET 
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render,redirect
from .models import Customer,Tag,Product,order
from .forms import OrderForm,updateOrderForm,CustomerForm,ProductForm
from django.db.models import Count
from django.db.models.functions import TruncDate
from .filters import OrderFilter
import csv
from .forms import createUserForm
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required

def registerpage(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    form = createUserForm() # Initialize for GET request
    
    if request.method == 'POST':
        form = createUserForm(request.POST)
        if form.is_valid():
            form.save()
            user_name = form.cleaned_data.get('username')
            messages.success(request, f"Account was created for {user_name}")
            # IMPORTANT: Redirect to login or home after success
            return redirect('login') 
            
    context = {'form': form}
    return render(request, 'account/registration.html', context)
       
def logoutpage(request):
    logout(request)
    return redirect('login')


def loginpage(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method=="POST":
            username=request.POST.get('username')
            password=request.POST.get('password')

            user=authenticate(request,username=username,password=password)

            if user is not None:
                login(request,user)
                return redirect('home')
            else:
                messages.info(request,"username or password is incoorrect...!")
        return render(request,'account/login.html')

            
@login_required(login_url='login')    
def Home(request):
    orders=order.objects.all()
    customers=Customer.objects.all()
    total_customers=customers.count()
    total_orders=orders.count()
    delivered=orders.filter(status='Delivered').count()
    pending=orders.filter(status='Pending').count()
    out_for_delivery=orders.filter(status='Out for delivery').count()
    status_data = orders.values('status').annotate(count=Count('status'))

    # Orders per day
    orders_per_day = (
        orders
        .annotate(date=TruncDate('date_created'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    context={'customers':customers,
             'orders':orders,
             'total_customers':total_customers,
              'total_orders':total_orders,
             'delivered':delivered,
             'pending':pending,
              'out_for_delivery':out_for_delivery,
              'status_data':list(status_data),
              'orders_per_day':list(orders_per_day),
    }
    return render(request, 'account/dashboard.html',context)

@login_required(login_url='login')
def Prod(request):
    products=Product.objects.all()
    context={'products':products}
    return render(request, 'account/product.html',context)

@login_required(login_url='login')
def cust(request, pk):
    customer=Customer.objects.get(id=pk)
    orders=customer.order_set.all()
    total_orders=orders.count()
    myFilter=OrderFilter(request.GET,queryset=orders)
    orders=myFilter.qs
    context={'customer':customer,
             'orders':orders,
             'total_orders':total_orders,
             'myFilter':myFilter
    }
    return render(request, 'account/customer.html', context)

@login_required(login_url='login')
def cust_list(request):
    customers=Customer.objects.all()
    context={'customers':customers}
    return render(request, 'account/customer_list.html', context)

@login_required(login_url='login')
def create_orders(request):
    form=OrderForm()
    if request.method=='POST':
        form=OrderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')
    context={'form':form}
    return render(request, 'account/orders_form.html', context) 

@login_required(login_url='login')
def create_order(request, pk):
    customer = Customer.objects.get(id=pk)
    form = OrderForm(initial={'customer': customer})
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.customer = customer
            order.save()
            return redirect('customer', pk=customer.id)

    context = {'form': form}
    return render(request, 'account/order_form.html', context)


''''def update_order(request,pk):
    orders=order.objects.get(id=pk)
    form=OrderForm(instance=orders)
    if request.method=='POST':
        form=OrderForm(request.POST,instance=orders)
        froms=updateOrderForm(request.POST,instance=orders)
        if form.is_valid():
            form.save()
            froms.save()
            return redirect('/')
    context={'form':form,'froms':froms}
    return render(request,'account/order_form.html',context)'''
    
@login_required(login_url='login')    
def update_order(request,pk):
        orders=order.objects.get(id=pk)
        #form=updateOrderForm(instance=orders)
        if request.method=='POST':
            form=updateOrderForm(request.POST,instance=orders)
            if form.is_valid():
               instance =form.save(commit=False)
               instance.customer = orders.customer
               instance.save()
            return redirect('/')
        else:
            form=updateOrderForm(instance=orders)
        context={'form':form,
                 'orders':orders,
                 'customer_name':orders.customer.name
                 }
        return render(request,'account/update_order.html',context)
    
@login_required(login_url='login')   
def delete_order(request,pk):
    orders=order.objects.get(id=pk)
    if(request.method=='POST'):
        orders.delete()
        return redirect('/')
    context={'orders':orders}
    return render(request,'account/delete_order.html',context)

@login_required(login_url='login')
def order_list(request):
    orders=order.objects.all()
    context={'orders':orders}
    return render(request,'account/order_list.html',context)

@login_required(login_url='login')
def create_customer(request):
    form = CustomerForm()

    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES)  # IMPORTANT
        if form.is_valid():
            form.save()
            return redirect('/')

    context = {'form': form}
    return render(request, 'account/create_customer.html', context)


@login_required(login_url='login')
def update_customer(request,pk):
    customers=Customer.objects.get(id=pk)
    form=CustomerForm(instance=customers)
    if request.method=='POST':
        form=CustomerForm(request.POST,instance=customers)
        if form.is_valid():
            form.save()
            return redirect('/')
    context={'form':form}
    return render(request,'account/update_customer.html',context)

@login_required(login_url='login')
def delete_customer(request,pk):
    customers=Customer.objects.get(id=pk)
    if(request.method=='POST'):
        customers.delete()
        return redirect('/')
    context={'customers':customers}
    return render(request,'account/delete_customer.html',context)

@login_required(login_url='login')
def update_product(request,pk):
    products=Product.objects.get(id=pk)
    form=ProductForm(instance=products)
    if request.method=='POST':
        form=ProductForm(request.POST,instance=products)
        if form.is_valid():
            form.save()
            return redirect('/')
    context={'form':form}
    return render(request,'account/update_product.html',context)

@login_required(login_url='login')
def add_product(request):
    form = ProductForm()
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            # Step 2: Add the success message here
            messages.success(request, 'Product added successfully! It is now live in your inventory.')
            return redirect('/')
            
    context = {'form': form}
    return render(request, 'account/add_product.html', context)

@login_required(login_url='login')
def delete_product(request,pk):
    products=Product.objects.get(id=pk)
    if(request.method=='POST'):
        products.delete()
        return redirect('/')
    context={'products':products}
    return render(request,'account/delete_product.html',context)

@login_required(login_url='login')
def analytics(request):
    orders = order.objects.all()

    status_data = orders.values('status').annotate(count=Count('status'))

    orders_per_day = (
        orders
        .annotate(date=TruncDate('date_created'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )


    context = {
        'status_data': json.dumps(list(status_data), default=str),
        'orders_per_day': json.dumps(list(orders_per_day), default=str),
    }

    return render(request, 'account/analytics.html', context)

@login_required(login_url='login')
def tag_list(request):
    tags=Tag.objects.all()
    context={'tags':tags}
    return render(request,'account/tag_list.html',context)

@login_required(login_url='login')
def import_tag_csv(request):
    if request.method=="POST":
        csv_file=request.FILES.get("csv_file")

        if not csv_file:    
            return HttpResponse("No file uploaded", status=400)
        
        decoded_file=csv_file.read().decode("utf-8").splitlines()
        reader=csv.DictReader(decoded_file)

        for row in reader:
            Tag.objects.get_or_create(name=row["name"])
        return redirect('tag_list')
    
    return render(request,'account/managing_tag.html')


