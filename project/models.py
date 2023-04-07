from django.db import models
from django.contrib.auth.hashers import make_password

class user(models.Model):
    userid = models.AutoField(primary_key=True)
    email = models.EmailField('email',max_length=40)
    username = models.CharField('username',max_length=30)
    password = models.CharField('password',max_length=30)
    phone = models.CharField('phone',max_length=10)
    role = models.CharField('role',max_length=20)
    status = models.CharField('status',max_length=20)

    # def create(self, validated_data):
    #     # Hash the password before saving it
    #     validated_data['password'] = make_password(validated_data['password'])
    #     return super().create(validated_data)

class category(models.Model):
    categoryid = models.AutoField(primary_key=True)
    categoryname = models.CharField('categoryname',max_length=20)
    offerpercentage = models.IntegerField('offerpercentage',null=True,default=0)
    def __str__(self):
        return self.categoryname

class coupon(models.Model):
    couponid = models.AutoField(primary_key=True)
    couponname = models.CharField('couponname',max_length=30)
    couponcode = models.CharField('couponcode',max_length=20,unique=True)
    expirytdate = models.DateField('expirydate')
    percentage = models.IntegerField('percentage')

class product(models.Model):
    productid = models.AutoField(primary_key=True)
    productname = models.CharField('productname',max_length=30)
    quantity = models.CharField('quantity',max_length=20)
    price = models.CharField('price',max_length=10)
    discountprice =models.IntegerField('discountprice',)
    offerpercentage = models.IntegerField('offerpercentage',null=True,default=0)
    category = models.ForeignKey(category,on_delete=models.CASCADE,null=False)
    provider = models.CharField('provider',max_length=20)
    image = models.ImageField('image',upload_to="products/")
    description = models.TextField('description')

class cart(models.Model):
    cartid = models.AutoField(primary_key=True)
    user = models.ForeignKey(user,on_delete=models.CASCADE,null=False)

class cartitem(models.Model):
    cartitemid = models.AutoField(primary_key=True)
    cart = models.ForeignKey(cart,on_delete=models.CASCADE,null=False)
    product = models.ForeignKey(product,on_delete=models.CASCADE,null=False)
    quantity = models.PositiveBigIntegerField()

    def subtotal(self):
        return int(self.product.price)*int(self.quantity)

class address(models.Model):
    addressid = models.AutoField(primary_key=True)
    user = models.ForeignKey(user,on_delete=models.CASCADE,null=False) 
    firstname = models.CharField('firstname',max_length=20)
    lastname = models.CharField('lastname',max_length=20)
    street = models.CharField('street',max_length=100)
    state = models.CharField('state',max_length=30)
    postalcode = models.CharField('postalcode',max_length=10)
    mail = models.EmailField('mail',max_length=30)
    phone = models.CharField('phone',max_length=30)

class order(models.Model):
    orderid = models.AutoField(primary_key=True)
    ordernumber = models.CharField(max_length=20,unique=True)
    user = models.ForeignKey(user,on_delete=models.CASCADE,null=False)
    address = models.ForeignKey(address,on_delete=models.CASCADE,null=False)
    orderdate = models.DateTimeField(auto_now_add=True)
    coupon = models.ForeignKey(coupon,on_delete=models.CASCADE,null=True)
    discount = models.CharField('discount',max_length=20,null=False,default=None)
    ordernotes = models.CharField('ordernotes',max_length=255,null=True)
    status = models.CharField('status',max_length=20,default='waiting')
    totalamount = models.CharField('totalamount',max_length=20)
    paymentmode = models.CharField('paymentmode',max_length=30)

class orderitems(models.Model):
    orderitemid = models.AutoField(primary_key=True)
    product = models.ForeignKey(product,on_delete=models.CASCADE,null=True)
    order = models.ForeignKey(order,on_delete=models.CASCADE,null=False)
    quantity = models.CharField(max_length=20,null=False)

    def subtotal(self):
        return (self.price * self.quantity)

class wishlist(models.Model):
    wishlistid = models.AutoField(primary_key=True)
    user = models.ForeignKey(user,on_delete=models.CASCADE,null=False)

class wishlistitems(models.Model):
    wishlistitemsid = models.AutoField(primary_key=True)
    wishlist = models.ForeignKey(wishlist,on_delete=models.CASCADE,null=False)
    product = models.ForeignKey(product,on_delete=models.CASCADE,null=False)

class banner(models.Model):
    bannerid = models.AutoField(primary_key=True)
    banner = models.FileField('banner',upload_to="banners/")

# Create your models here.
