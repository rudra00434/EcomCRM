from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=200)
    address = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    profile_image = models.ImageField(upload_to='profile/', null=True, blank=True)

    # NEW FIELDS
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Customer name is :{self.name}"

class Tag(models.Model):
    name=models.CharField(max_length=200,null=True)
    
    def __str__(self):
        return self.name
    
      
class Product(models.Model):
    CATAGORY=(
        ('Indoor','Indoor'),
        ('Outdoor','Outdoor'),
    )
    name=models.CharField(max_length=200,null=True)
    price=models.FloatField(max_length=200,null=True)
    category=models.CharField(max_length=200,null=True,choices=CATAGORY)
    description=models.CharField(max_length=200,null=True,blank=True)
    date_created=models.DateTimeField(auto_now_add=True,null=True)
    pic=models.ImageField(upload_to='product_image/',null=True,blank=True)
    tags=models.ManyToManyField(Tag)
    
    def __str__(self):
        return self.name
class order(models.Model):
    STATUS=(
        ('Pending','Pending'),
        ('Out for delivery','Out for delivery'),
        ('Delivered','Delivered'),
    )
    customer=models.ForeignKey(Customer,null=True,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,null=True,on_delete=models.CASCADE)
    status=models.CharField(max_length=200,null=True,choices=STATUS)
    date_created=models.DateTimeField(auto_now_add=True,null=True)
    def __str__(self):
        return f"Order of {self.product.name} for {self.customer.name}"