from django.forms import ModelForm
from .models import order , Customer,Product
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
class OrderForm(ModelForm):
    class Meta:
        model = order
        fields = '__all__'
        
class updateOrderForm(ModelForm):
    class Meta:
        model = order
        exclude=['customer']

class CustomerForm(ModelForm):
    class Meta:
        model = Customer
        fields='__all__'
class updateCustomerForm(ModelForm):
    class Meta:
        model=Customer
        exclude=['date_created']
class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        
        # Use .values() to get the field objects directly
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control-custom',
                'placeholder': f'Enter {field.label.lower()}...'
            })
class createUserForm(UserCreationForm):
    class Meta:
        model=User
        fields=['username','email','password1','password2']