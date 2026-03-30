from multiprocessing import context
from datetime import date
import json
from pickle import GET 
import mimetypes
from pathlib import Path
from django.contrib import messages
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import render,redirect
from django.conf import settings
from .models import Customer,Tag,Product,order
from .media_utils import resolve_local_media_path
from .forms import OrderForm,updateOrderForm,CustomerForm,ProductForm
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from .filters import OrderFilter
import csv
from .forms import createUserForm
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST

from .ai_assistant import (
    clear_chat_history,
    generate_ai_chat_response,
    get_ask_ai_page_context,
    get_chat_history,
    save_chat_history,
)

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
            return redirect('home')      
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
        form=CustomerForm(request.POST, request.FILES, instance=customers)
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
        form=ProductForm(request.POST, request.FILES, instance=products)
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
def revenue(request):
    today = timezone.localdate()
    start_of_year = date(today.year, 1, 1)
    days_elapsed = (today - start_of_year).days + 1

    delivered_orders = order.objects.filter(
        status='Delivered',
        product__price__isnull=False,
        date_created__year=today.year,
    )

    daily_revenue_queryset = (
        delivered_orders
        .annotate(date=TruncDate('date_created'))
        .values('date')
        .annotate(
            revenue=Sum('product__price'),
            orders=Count('id'),
        )
        .order_by('date')
    )

    daily_revenue_rows = [
        {
            'date': item['date'],
            'revenue': float(item['revenue'] or 0),
            'orders': item['orders'],
        }
        for item in daily_revenue_queryset
    ]

    ytd_realized_revenue = sum(item['revenue'] for item in daily_revenue_rows)
    average_daily_revenue = ytd_realized_revenue / days_elapsed if days_elapsed else 0
    projected_annual_revenue = average_daily_revenue * 365
    remaining_projection = projected_annual_revenue - ytd_realized_revenue

    pipeline_revenue = (
        order.objects.filter(
            status__in=['Pending', 'Out for delivery'],
            product__price__isnull=False,
        ).aggregate(total=Sum('product__price'))['total'] or 0
    )

    best_revenue_day = max(daily_revenue_rows, key=lambda item: item['revenue'], default=None)

    revenue_chart_data = [
        {
            'date': item['date'].isoformat(),
            'revenue': item['revenue'],
            'orders': item['orders'],
        }
        for item in daily_revenue_rows
    ]

    context = {
        'today': today,
        'current_year': today.year,
        'days_elapsed': days_elapsed,
        'daily_revenue_rows': daily_revenue_rows,
        'revenue_chart_data': json.dumps(revenue_chart_data),
        'ytd_realized_revenue': ytd_realized_revenue,
        'average_daily_revenue': average_daily_revenue,
        'projected_annual_revenue': projected_annual_revenue,
        'remaining_projection': remaining_projection,
        'pipeline_revenue': float(pipeline_revenue),
        'best_revenue_day': best_revenue_day,
        'delivered_orders_count': delivered_orders.count(),
    }

    return render(request, 'account/revenue.html', context)

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


@login_required(login_url='login')
def about_page(request):
    context = {
        'platform_pillars': [
            {
                'title': 'Customer Memory',
                'copy': 'Keep profiles, orders, and relationship history tied together so your team always has context.',
                'url_name': 'customer_list',
                'url_label': 'Explore Customers',
                'icon': 'bi-people',
            },
            {
                'title': 'Operational Control',
                'copy': 'Track product inventory, tag structure, and order progress from one operational workspace.',
                'url_name': 'order_list',
                'url_label': 'View Orders',
                'icon': 'bi-box-seam',
            },
            {
                'title': 'Revenue Visibility',
                'copy': 'Move from fulfillment activity into analytics and projected revenue without switching tools.',
                'url_name': 'revenue',
                'url_label': 'Open Revenue',
                'icon': 'bi-graph-up-arrow',
            },
        ]
    }
    return render(request, 'account/about.html', context)


@login_required(login_url='login')
def contact_page(request):
    context = {
        'contact_methods': [
            {
                'eyebrow': 'Phone',
                'value': '+91 8371817646',
                'copy': 'Call for implementation help, workflow questions, or quick operational support.',
                'href': 'tel:+918371817646',
                'cta': 'Call Now',
                'icon': 'bi-telephone',
            },
            {
                'eyebrow': 'Email',
                'value': 'rudranilgoswami2005@gmail.com',
                'copy': 'Use email for support requests, onboarding questions, or collaboration enquiries.',
                'href': 'mailto:rudranilgoswami2005@gmail.com',
                'cta': 'Send Email',
                'icon': 'bi-envelope',
            },
            {
                'eyebrow': 'Location',
                'value': 'Asansol, West Bengal, India',
                'copy': 'Serving commerce operations with a practical product and support mindset.',
                'href': 'https://maps.google.com/?q=Asansol,West+Bengal,India',
                'cta': 'Open Map',
                'icon': 'bi-geo-alt',
            },
        ],
    }
    return render(request, 'account/contact.html', context)


@login_required(login_url='login')
def media_fallback(request, file_path):
    media_root = Path(settings.MEDIA_ROOT).resolve()
    local_path = resolve_local_media_path(file_path)
    if not local_path:
        raise Http404("File not found.")

    resolved_path = local_path.resolve()

    if media_root not in resolved_path.parents and resolved_path != media_root:
        raise Http404("File not found.")

    extension_types = {
        ".webp": "image/webp",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
    }
    content_type = extension_types.get(resolved_path.suffix.lower())
    if not content_type:
        content_type = mimetypes.guess_type(str(resolved_path))[0] or "application/octet-stream"

    return FileResponse(resolved_path.open("rb"), content_type=content_type)


@login_required(login_url='login')
def ask_to_ai_page(request):
    context = get_ask_ai_page_context()
    context['ai_history'] = get_chat_history(request.session)
    return render(request, 'account/ask_ai.html', context)


@login_required(login_url='login')
@require_POST
def ask_to_ai_message(request):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request payload.'}, status=400)

    message = (payload.get('message') or '').strip()
    if not message:
        return JsonResponse({'error': 'Please enter a message.'}, status=400)

    history = get_chat_history(request.session)
    result = generate_ai_chat_response(message, history)

    updated_history = history + [
        {'role': 'user', 'content': message},
        {
            'role': 'assistant',
            'content': result['reply'],
            'sources': result.get('sources', []),
        },
    ]
    save_chat_history(request.session, updated_history)

    return JsonResponse(result)


@login_required(login_url='login')
@require_POST
def ask_to_ai_reset(request):
    clear_chat_history(request.session)
    return JsonResponse({'ok': True})


