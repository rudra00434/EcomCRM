from django .urls import path
from .import views 
urlpatterns=[
    path('login/',views.loginpage,name='login'),
    path('registration/',views.registerpage,name='registration'),
    path('logout/',views.logoutpage,name='logout'),
    path('',views.Home,name='home'),
    path('product/',views.Prod,name='product'),
    path('customer/',views.cust,name='customer'),
    path('customer/<int:pk>/', views.cust, name='customer'),
    path('customer_list/', views.cust_list, name='customer_list'),
    path('create_order/<int:pk>/',views.create_order,name='create_order'),
    path('create_orders/',views.create_orders,name='create_orders'),
    path('update_order/<int:pk>/',views.update_order,name='update_order'),
    path('delete_order/<int:pk>/',views.delete_order,name='delete_order'),
    path('order_list/',views.order_list,name='order_list'),
    path('create_customer/',views.create_customer,name='create_customer'),
    path('update_customer/<int:pk>/',views.update_customer,name='update_customer'),
    path('delete_customer/<int:pk>/',views.delete_customer,name='delete_customer'),
    path('update_product/<int:pk>/',views.update_product,name='update_product'),
    path('add_product/',views.add_product,name='add_product'),
    path('delete_product/<int:pk>/',views.delete_product,name='delete_product'),
    path('analytics/', views.analytics, name='analytics'),
    path('tag_list/',views.tag_list,name='tag_list'),
    path('import_tag_csv/',views.import_tag_csv,name='import_tag_csv')
    
]