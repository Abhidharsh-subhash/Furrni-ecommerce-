from django.db.models import Q, F
from xhtml2pdf import pisa
from django.template.loader import get_template
from datetime import datetime
import datetime
import calendar
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.functions import ExtractYear, ExtractMonth, ExtractDay
import os
import string
import random
from django.core.mail import send_mail
from django.db.models import Sum
import pyotp
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import render
import datetime
import openpyxl
from openpyxl import Workbook
import pytz
from io import StringIO
from datetime import datetime,time, timedelta
from django.views import View
# Create your views here.
from django.shortcuts import render, redirect, HttpResponse
from .models import user as usr, category as cat, product as pro, cart as car, cartitem as carit, banner as bn, order as ord, orderitems as ordit, address as add, wishlist as wish, wishlistitems as wishit, coupon as cp

def createpdf(request):
    if request.POST:
        fromdate = request.POST['fromdate']
        fromdt = datetime.strptime(fromdate, '%Y-%m-%d').date()
        todate = request.POST['todate']
        todt = datetime.strptime(todate, '%Y-%m-%d').date()
        currentdate = datetime.today().date()
        if (currentdate >= fromdt) and (currentdate >= todt) and (fromdt < todt):
            if 'pdf' in request.POST:
                data = ord.objects.filter(orderdate__range=[fromdate, todate + " 23:59:59"])
                template_path = 'sales.html'
                context = {'data': data,
                           'fromdate': fromdate, 'todate': todate}
                # Create a Django response object, and specify content_type as pdf
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="salesreport.pdf"'
                # find the template and render it.
                template = get_template(template_path)
                html = template.render(context)

                # create a pdf
                pisa_status = pisa.CreatePDF(
                    html, dest=response)
                # if error then show some funny view
                if pisa_status.err:
                    return HttpResponse('We had some errors <pre>' + html + '</pre>')
                return response
            elif 'excel' in request.POST:
                orders = ord.objects.filter(
                    orderdate__range=[fromdt, todt ]).order_by('orderdate')
                response = HttpResponse(
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename=Report.xlsx'
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.append(['Order Number', 'User', 'Order Status',
                          'Order Total', 'Order Date',])
                for order in orders:
                    date = order.orderdate.astimezone(
                        pytz.utc).replace(tzinfo=None)
                    ws.append([order.ordernumber, order.user.email,
                              order.status, order.totalamount, date,])
                file_name = "sales_report.xlsx"
                wb.save(file_name)
                with open(file_name, "rb") as f:
                    response = HttpResponse(f.read(
                    ), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    response["Content-Disposition"] = f"attachment; filename={file_name}"
                    return response

            else:
                messages.error(request, 'Invalid request detected')
                return redirect('orderlist')
        else:
            messages.warning(
                request, 'Please provide the date in a valid format')
            return redirect('orderlist')
    else:
        return redirect('orderlist')


def index(request):
    data = None
    datab = None
    if 'username' in request.session:
        id = request.session['id']
        datau = usr.objects.get(userid=id)
        if datau.role == 'admin':
            return redirect('adminhome')
        else:
            return redirect('userhome')
    else:
        try:
            datab = bn.objects.first()
        except Exception as identifier:
            pass
        try:
            data = pro.objects.all()
        except Exception as identifier:
            pass
        return render(request, "index.html", {'data': data, 'datab': datab})


def userlogin(request):
    if 'username' in request.session:
        if 'role' in request.session == 'admin':
            return redirect('adminhome')
        else:
            return redirect('userhome')
    else:
        return render(request, 'userlogin.html')


def shop(request):
    data = pro.objects.all()
    return render(request, 'shop.html', {'data': data})


def about(request):
    return render(request, 'about.html')


def blog(request):
    return render(request, 'blog.html')


def contact(request):
    return render(request, 'contact.html')


def error(request, exception):
    return render(request, '404.html')


def adprivacy(request):
    return render(request, 'adprivacy.html')


def cart(request):
    if 'username' in request.session:
        total = 0
        quantity = 0
        id = request.session['id']
        data = carit.objects.filter(cart__user=id)
        for d in data:
            x = int(d.product.discountprice)
            y = int(d.quantity)
            total += (x * y)
            quantity += d.quantity
        datap = {
            "total": total,
            "quantity": quantity
        }
        return render(request, 'cart.html', {'data': data, 'datap': datap})
    else:
        return redirect('userlogin')


def addtocart(request):
    use = request.session['id']
    user = usr.objects.get(userid=use)
    try:
        cart = car.objects.get(user=user)
    except car.DoesNotExist:
        cart = car.objects.create(user=user)

    pid = request.POST['pid']
    try:
        product = pro.objects.get(productid=pid)
    except pro.DoesNotExist:
        return redirect('userhome')

    try:
        cartitem = carit.objects.get(cart=cart, product=product)
        cartitem.quantity += 1
    except carit.DoesNotExist:
        cartitem = carit.objects.create(cart=cart, product=product, quantity=1)

    cartitem.save()
    return redirect('cart')


def delcartitem(request):
    id = request.GET['id']
    carit.objects.filter(cartitemid=id).delete()
    return redirect('cart')


def inccartitem(request):
    if request.method == 'POST':
        id = request.session['id']
        total = 0
        quantity = 0
        prod_id = request.POST['product_id']
        c = carit.objects.get(cart__user=id, cartitemid=prod_id)
        data = c.product.productid
        datac = pro.objects.get(productid=data)
        qty = int(datac.quantity)
        if int(c.quantity) == qty:
            pass
        else:
            c.quantity += 1
            c.save()
        datat = carit.objects.filter(cart__user=id)
        for d in datat:
            x = int(d.product.discountprice)
            y = int(d.quantity)
            total += (x * y)
            quantity += d.quantity
        return JsonResponse({'quantity': c.quantity, 'qty': qty, 'total': total, 'qt': quantity})
    return redirect('cart')


def deccartitem(request):
    if request.method == 'POST':
        id = request.session['id']
        total = 0
        quantity = 0
        prod_id = request.POST['product_id']
        c = carit.objects.get(cart__user=id, cartitemid=prod_id)
        if c.quantity >= 2:
            c.quantity -= 1
            c.save()
        data = carit.objects.filter(cart__user=id)
        for d in data:
            x = int(d.product.discountprice)
            y = int(d.quantity)
            total += (x * y)
            quantity += d.quantity
        data = {
            'quantity': c.quantity,
            'total': total,
            'qt': quantity
        }
        return JsonResponse(data)
    return redirect('cart')


def checkout(request):
    id = request.session['id']
    total = 0
    quantity = 0
    datap = None
    offer = None
    datacp = None
    datacp = None
    cop = None
    try:
        cart = car.objects.get(user=id)
    except Exception as identifier:
        pass
    try:
        data = cart.cartid
        datad = carit.objects.filter(cart=data).all()
    except Exception as e:
        messages.error(request, 'something went wrong')
    try:
        datac = carit.objects.filter(cart__user=id)
        for d in datac:
            x = int(d.product.discountprice)
            y = int(d.quantity)
            total += (x * y)
            quantity += d.quantity
        if request.POST:
            coupon = request.POST['coupon']
            try:
                datacp = cp.objects.get(couponcode=coupon)
                if datacp:
                    cop = coupon
                    datao = datacp.percentage
                    datada = datacp.expirytdate
                    currentdate = datetime.now().date()
                    if currentdate >= datada:
                        messages.error(request, "offer expired")
                    else:
                        dat = int(total)*(int(datao)/100)
                        offer = int(dat)
                        total -= int(dat)
                        messages.success(request, 'Coupon applied')
                else:
                    messages.warning(request, "Invalid coupon")
            except Exception as identifier:
                datacp = None
                messages.warning(request,"Invalid couponname")
                pass
        datap = {
            "total": total,
            "quantity": quantity,
        }
    except Exception as identifier:
        pass
    dataa = add.objects.filter(user=id).all()
    return render(request, 'checkout.html', {'datad': datad, 'datap': datap, 'dataa': dataa, 'offer': offer, 'datacp': datacp, 'cop': cop})


def generate_order_number():
    # Define the possible characters for the order number
    chars = string.digits + string.ascii_uppercase

    # Generate a random string of length 6 or more
    length = random.randint(6, 10)
    order_number = ''.join(random.choice(chars) for _ in range(length))

    return order_number


def paypal(request):
    id = request.session['id']
    user = usr.objects.get(userid=id)
    try:
        addr = add.objects.filter(user=id).count()
        if addr == 0:
            messages.warning(request, 'Add address to proceed')
            return redirect('checkout')
        else:
            pass
        if request.POST:
            cop = None
            if 'cod' in request.POST:
                address = request.POST['address']
                ordernotes = request.POST['ordernotes']
                total = request.POST['tid']
                coupon = request.POST['cid']
                discount = request.POST['did']
                try:
                    cop = cp.objects.get(couponcode=coupon)
                except Exception as identifier:
                    pass
                datac = add.objects.get(addressid=address)
                user = usr.objects.get(userid=id)
                order_number = generate_order_number()
                ord.objects.create(user=user, ordernumber=order_number, address=datac, coupon=cop, discount=discount,
                                   ordernotes=ordernotes, status='waiting', totalamount=total, paymentmode='cod')
                cart = car.objects.get(user=user)
                datad = carit.objects.filter(cart=cart.cartid).all()
                order = ord.objects.filter(user=user).last()
                for i in datad:
                    product = i.product.productid
                    orderproduct = pro.objects.get(productid=product)
                    datap = int(orderproduct.quantity)-int(i.quantity)
                    pro.objects.filter(
                        productid=product).update(quantity=datap)
                    ordit.objects.create(
                        order=order, product=i.product, quantity=i.quantity)
                carit.objects.filter(cart=cart.cartid).delete()
                car.objects.filter(user=user).delete()
                return redirect('thankyou')
            else:
                address = request.POST['address']
                ordernotes = request.POST['ordernotes']
                total = request.POST['tid']
                coupon = request.POST['cid']
                discount = request.POST['did']
                try:
                    cop = cp.objects.get(couponcode=coupon)
                except Exception as identifier:
                    pass
                datac = add.objects.get(addressid=address)
                user = usr.objects.get(userid=id)
                order_number = generate_order_number()
                ord.objects.create(user=user, ordernumber=order_number, address=datac, coupon=cop, discount=discount,
                                   ordernotes=ordernotes, status='waiting', totalamount=total, paymentmode='paypal')
                cart = car.objects.get(user=user)
                datad = carit.objects.filter(cart=cart.cartid).all()
                order = ord.objects.filter(user=user).last()
                for i in datad:
                    product = i.product.productid
                    orderproduct = pro.objects.get(productid=product)
                    datap = int(orderproduct.quantity)-int(i.quantity)
                    pro.objects.filter(
                        productid=product).update(quantity=datap)
                    ordit.objects.create(
                        order=order, product=i.product, quantity=i.quantity)
                carit.objects.filter(cart=cart.cartid).delete()
                car.objects.filter(user=user).delete()
                return redirect('thankyou')
        else:
            messages.warning(request, 'Error occured')
            return redirect('checkout')
    except Exception as e:
        messages.error(request, e)
        return redirect('checkout')


def address(request):
    if request.POST:
        id = request.session['id']
        data = usr.objects.get(userid=id)
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        street = request.POST['street']
        state = request.POST['state']
        postalcode = request.POST['postalcode']
        mail = request.POST['mail']
        phone = request.POST['phone']
        add.objects.create(user=data, firstname=firstname, lastname=lastname,
                           street=street, state=state, postalcode=postalcode, mail=mail, phone=phone)
        messages.success(request, 'New address added successfully')
        return redirect('checkout')
    else:
        messages.error(request, 'Operation failed')
        return redirect('checkout')


def deladdress(request):
    if request.POST:
        id = request.POST['aid']
        add.objects.filter(addressid=id).delete()
        messages.success(request, 'Address deleted successfully')
        return redirect('profile')
    else:
        messages.error(request, 'Error occured')
        return redirect('profile')


def editaddress(request):
    if request.POST:
        id = request.POST['aid']
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        street = request.POST['street']
        state = request.POST['state']
        postalcode = request.POST['postalcode']
        mail = request.POST['mail']
        phone = request.POST['phone']
        add.objects.filter(addressid=id).update(firstname=firstname, lastname=lastname,
                                                street=street, state=state, postalcode=postalcode, mail=mail, phone=phone)
        messages.success(request, 'Address updated successfully')
        return redirect('profile')
    else:
        messages.error(request, 'Error editing the address')
        return redirect('profile')


def newaddress(request):
    if request.POST:
        id = request.POST['uid']
        data = usr.objects.get(userid=id)
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        street = request.POST['street']
        state = request.POST['state']
        postalcode = request.POST['postalcode']
        mail = request.POST['mail']
        phone = request.POST['phone']
        add.objects.create(user=data, firstname=firstname, lastname=lastname,
                           street=street, state=state, postalcode=postalcode, mail=mail, phone=phone)
        messages.success(request, 'New address added successfully')
        return redirect('profile')
    else:
        messages.error(request, 'Error while adding new address')
        return redirect('profile')


def thankyou(request):
    return render(request, 'thankyou.html')


def usersignup(request):
    return render(request, 'usersignup.html')


def userhome(request):
    if 'username' in request.session:
        s = ''
        data = pro.objects.all()
        datac = cat.objects.all()
        if 'search' in request.POST:
            s = request.POST['search']
            data = pro.objects.filter(productname__icontains=s).all()
            return render(request, 'userhome.html', {'data': data, 's': s, 'datac': datac})
        if 'price_range' in request.GET:
            price_range = request.GET['price_range']
            if price_range == "low_to_high":
                data = data.order_by('discountprice')
                return render(request, 'userhome.html', {'data': data, 'datac': datac})
            elif price_range == "high_to_low":
                data = pro.objects.order_by('-discountprice')
                return render(request, 'userhome.html', {'data': data, 'datac': datac})
        if 'filter' in request.POST:
            min = request.POST['min']
            max = request.POST['max']
            if not max:
                data = pro.objects.filter(discountprice__gte=min)
                return render(request, 'userhome.html', {'data': data, 'datac': datac, 'min': min})
            elif not min:
                data = pro.objects.filter(discountprice__lte=max)
                return render(request, 'userhome.html', {'data': data, 'datac': datac, 'max': max})
            else:
                data = pro.objects.filter(
                    discountprice__gte=min, discountprice__lte=max).all()
                return render(request, 'userhome.html', {'data': data, 'datac': datac, "min": min, "max": max})
        return render(request, 'userhome.html', {'data': data, 'datac': datac})
    else:
        return redirect('userlogin')


def categorywise(request):
    if 'username' in request.session:
        data = cat.objects.all()
        datac = request.GET['datac']
        datap = pro.objects.filter(category=datac).all()
        return render(request, 'categorywise.html', {'data': data, 'datap': datap})
    else:
        return redirect('userlogin')


def productdetail(request):
    id = request.GET['id']
    data = pro.objects.get(productid=id)
    return render(request, 'productdetail.html', {'d': data})


def productdet(request):
    return render(request, 'productdet.html')


def adminhome(request):
    if 'username' in request.session:
        users = usr.objects.filter(
            (Q(role='user') | Q(role='blocked')) & Q(status='True')).count()
        products = pro.objects.count()
        orders = ord.objects.count()
        orders_months = ord.objects.annotate(month=ExtractMonth('orderdate')).values(
            'month').annotate(count=Count('orderid')).values('month', 'count')
        orders_days = ord.objects.annotate(day=ExtractDay('orderdate')).values(
            'day').annotate(count=Count('orderid')).values('day', 'count')
        months = []
        total_orders = []
        for i in orders_months:
            months.append(calendar.month_name[i['month']])
            total_orders.append(i['count'])
        order = ord.objects.order_by('orderdate')[:2]
        datac = ord.objects.filter(status='completed').count()
        dataca = ord.objects.filter(Q(status='cancelled by admin') | Q(
            status='cancelled by user') | Q(status='refunded')).count()
        datas = ord.objects.filter(status='shipped').count()
        dataw = ord.objects.filter(status='waiting').count()
        context = {
            'datac': datac,
            'dataw': dataw,
            'dataca': dataca,
            'datas': datas,
            'total_orders': total_orders,
            'months': months,
            'order': order,
            'users': users,
            'products': products,
            'orders': orders
        }
        return render(request, 'adminhome.html', context)
    else:
        return redirect('userlogin')


def userlist(request):
    if 'username' in request.session:
        if 'search' in request.POST:
            s = request.POST['search']
            data = usr.objects.filter((Q(username__icontains=s) | Q(email__icontains=s) | Q(
                phone__icontains=s)) & (Q(role='user') | Q(role='blocked')) & Q(status='True')).all()
            if len(data) == 0:
                messages.error(request, 'No result found')
            else:
                pass
        else:
            data = usr.objects.exclude(
                Q(role='admin') | Q(status='False')).all()
            paginator = Paginator(data, 6)
            page_number = request.GET.get('page')
            data = paginator.get_page(page_number)
        return render(request, 'userlist.html', {'data': data})
    else:
        return redirect('userlogin')


def categorylist(request):
    if 'username' in request.session:
        if 'search' in request.POST:
            s = request.POST['search']
            data = cat.objects.filter(categoryname__icontains=s).all()
            if len(data) == 0:
                pass
            else:
                return render(request, 'categorylist.html', {'data': data})
        else:
            data = cat.objects.all()
            paginator = Paginator(data, 6)
            page_number = request.GET.get('page')
            data = paginator.get_page(page_number)
            return render(request, 'categorylist.html', {'data': data})
    else:
        return redirect('userlogin')


def orderlist(request):
    if 'username' in request.session:
        if 'search' in request.POST:
            s = request.POST['search']
            data = ord.objects.filter(
                Q(user__username__icontains=s) | Q(ordernumber=s)).all()
            if len(data) == 0:
                pass
            else:
                return render(request, 'orderlist.html', {'data': data})
        else:
            data = ord.objects.all()
            paginator = Paginator(data, 6)
            page_number = request.GET.get('page')
            data = paginator.get_page(page_number)
            return render(request, 'orderlist.html', {'data': data})
    else:
        return redirect('userlogin')


def shipped(request):
    oid = request.POST['oid']
    ord.objects.filter(orderid=oid).update(status='shipped')
    messages.success(request, 'The order is marked as shipped')
    return redirect('orderlist')


def cancel(request):
    oid = request.POST['cid']
    ord.objects.filter(orderid=oid).update(status='cancelled by admin')
    messages.success(request, 'The order is cancelled')
    return redirect('orderlist')


def completed(request):
    id = request.POST['cid']
    ord.objects.filter(orderid=id).update(status='completed')
    messages.success(request, "Order marked as delivered")
    return redirect('orderlist')


def productlist(request):
    if 'username' in request.session:
        datac = cat.objects.all()
        if 'search' in request.POST:
            s = request.POST['search']
            data = pro.objects.filter(
                Q(productname__icontains=s) | Q(price__icontains=s)).all()
            if len(data) == 0:
                messages.error(request, 'No result found')
            else:
                return render(request, 'productlist.html', {'data': data, 'datac': datac})
        else:
            data = pro.objects.all()
            paginator = Paginator(data, 3)
            page_number = request.GET.get('page')
            data = paginator.get_page(page_number)
            return render(request, 'productlist.html', {'data': data, 'datac': datac})
    else:
        return redirect('userlogin')


def category(request):
    if 'username' in request.session:
        return render(request, 'category.html')
    else:
        return redirect('index')


def banner(request):
    if 'username' in request.session:
        if request.POST:
            banner = request.FILES['banner']
            bn.objects.create(banner=banner)
            messages.success(request, 'Banner added successfully')
            return render(request, 'banner.html')
        else:
            return render(request, 'banner.html')
    else:
        return redirect('index')


def bannerlist(request):
    if 'username' in request.session:
        data = bn.objects.all()
        paginator = Paginator(data, 6)
        page_number = request.GET.get('page')
        data = paginator.get_page(page_number)
        return render(request, 'bannerlist.html', {'data': data})
    else:
        return redirect('userlogin')


def delbanner(request):
    if request.POST:
        bid = request.POST['bid']
        ban = bn.objects.get(bannerid=bid)
        if len(ban.banner) > 0:
            os.remove(ban.banner.path)
        ban.delete()
        messages.success(request, 'Banner deleted successfully')
        return redirect('bannerlist')
    else:
        messages.error(request, 'Error occured while delting the banner')
        return redirect('bannerlist')


def caty(request):
    if request.POST:
        categoryname = request.POST['categoryname']
        datac = cat.objects.filter(categoryname=categoryname).count()
        if datac > 0:
            messages.error(request, "Category already exist")
            return redirect('category')
        else:
            cat.objects.create(categoryname=categoryname)
            messages.success(request, 'New category added successfully')
            return redirect('category')
    else:
        messages.warning(request, 'Somthing went wrong')
        return redirect('category')


def delcat(request):
    cid = request.POST['cid']
    cat.objects.filter(categoryid=cid).delete()
    messages.error(request, 'Category deleted')
    return redirect('categorylist')


def editcat(request):
    cid = request.POST['cid']
    categoryname = request.POST['categoryname']
    cat.objects.filter(categoryid=cid).update(categoryname=categoryname)
    messages.warning(request, 'Category updated')
    return redirect('categorylist')


def product(request):
    if 'username' in request.session:
        data = cat.objects.all()
        return render(request, 'product.html', {'data': data})
    else:
        return redirect('userlogin')


def adpro(request):
    if request.POST:
        productname = request.POST['productname']
        quantity = request.POST['quantity']
        provider = request.POST['provider']
        price = request.POST['price']
        description = request.POST['description']
        category = request.POST['category']
        image = request.FILES['image']
        datac = cat.objects.get(categoryid=category)
        pro.objects.create(productname=productname, quantity=quantity, provider=provider,
                           price=price, discountprice=price, description=description, category=datac, image=image)
        messages.success(request, 'New product added successfully')
        return redirect('product')
    else:
        messages.error(request, 'Operation failed')
        return redirect('product')


def delpro(request):
    pid = request.POST['cid']
    pro.objects.filter(productid=pid).delete()
    messages.error(request, 'Product deleted')
    return redirect('productlist')


def editpro(request):
    if request.POST:
        pid = request.POST['pid']
        productname = request.POST['productname']
        quantity = request.POST['quantity']
        price = request.POST['price']
        provider = request.POST['provider']
        category = request.POST['category']
        description = request.POST['description']
        datac = cat.objects.get(categoryid=category)
        product = pro.objects.get(productid=pid)
        if 'image' in request.FILES:
            # remove the existing image
            if product.image and os.path.isfile(product.image.path):
                os.remove(product.image.path)
            product.image = request.FILES['image']
        product.productname = productname
        product.quantity = quantity
        product.price = price
        product.provider = provider
        product.category = datac
        product.description = description
        product.save()
        messages.success(request, 'Product updated successfully')
        return redirect('productlist')
    else:
        messages.error(request, 'Product updation failed')
        return redirect('userhome')


def orderhistory(request):
    if 'username' in request.session:
        datap = None
        data = None
        try:
            id = request.session['id']
        except Exception as identifier:
            pass
        try:
            user = usr.objects.get(userid=id)
        except Exception as identifier:
            pass
        try:
            data = ord.objects.filter(user=user).first()
        except Exception as identifier:
            pass
        try:
            datap = ordit.objects.filter(order=data).all()
        except Exception as identifier:
            pass
        try:
            datac = Count(datap)
        except Exception as identifier:
            pass
        return render(request, 'orderhistory.html', {'datap': datap, 'datac': datac, 'data': data})
    else:
        return redirect('userlogin')


def invoice(request):
    order = request.GET['order']
    data = ord.objects.get(orderid=order)
    items = ordit.objects.filter(order=data).all()
    template = get_template('invoice.html')
    context = {'data': data, 'items': items}
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="FurrniInvoice.pdf"'

    pdf = pisa.CreatePDF(html, response)
    if not pdf.err:
        return response
    return HttpResponse('Error generating PDF: %s' % pdf.err, status=500)


def usorcan(request):
    if request.POST:
        id = request.POST['oid']
        ord.objects.filter(orderid=id).update(status='cancelled by user')
        messages.warning(request, "Order cancelled successfully")
        return redirect('orderhistory')
    else:
        messages.error(request, 'Erro occured')
        return render('orderhistory')


def ordreturn(request):
    if request.POST:
        id = request.POST['oid']
        ord.objects.filter(orderid=id).update(status='return requested')
        messages.warning(request, 'Order will get returned successfully')
        return redirect('orderhistory')
    else:
        messages.error(request, 'Error occured')
        return redirect('orderhistory')


def refund(request):
    if request.POST:
        id = request.POST['oid']
        ord.objects.filter(orderid=id).update(status='refunded')
        messages.warning(request, 'the amount is refunded')
        return redirect('orderlist')
    else:
        messages.error(request, 'Error occured')
        return redirect('orderlist')


def privacy(request):
    return render(request, 'privacy.html')


def profile(request):
    if 'username' in request.session:
        try:
            id = request.session['id']
        except Exception as identifier:
            messages.error(request, 'User not found')
            return redirect('userlogin')
        data = usr.objects.get(userid=id)
        dataa = add.objects.filter(user=data).all()
        return render(request, 'profile.html', {'d': data, 'dataa': dataa})
    else:
        return redirect('userlogin')


def updateprofile(request):
    if request.POST:
        id = request.POST['uid']
        username = request.POST['username']
        phone = request.POST['phone']
        try:
            if usr.objects.get(userid=id):
                usr.objects.filter(userid=id).update(
                    username=username, phone=phone)
                messages.success(request, "Profile updated successfully")
                return redirect('profile')
            else:
                messages.error(request, "Something went wrong")
                return redirect('profile')
        except Exception as identifier:
            pass
        return redirect('profile')
    else:
        return redirect('profile')


def updateprof(request):
    try:
        id = request.GET['uid']
    except Exception as identifier:
        messages.error(request, 'User not found')
        return redirect('userlogin')
    try:
        if request.POST:
            username = request.POST['username']
            phone = request.POST['phone']
            email = request.POST['email']
            usr.objects.filter(userid=id).update(
                username=username, phone=phone, email=email)
            messages.success(request, 'Profile updated successfully')
            return redirect('profile')
        else:
            messages.error(request, 'somthing went wrong')
            return redirect('profile')
    except Exception as e:
        messages.error(request, 'error occured', e)
        return redirect('profile')


def wishlist(request):
    return render(request, 'wishlist.html')


def wishlis(request):
    return render(request, 'wishlis.html')


def logout(request):
    try:
        del request.session['username']
        del request.session['role']
        del request.session['id']
        return redirect('index')
    except:
        return redirect('index')


def signup(request):
    if request.POST:
        username = request.POST['username']
        email = request.POST['email']
        phone = request.POST['phone']
        password = request.POST['password']
        repassword = request.POST['repassword']
        if password != repassword:
            messages.warning(request, "passwords are not matching")
            return redirect('usersignup')
        else:
            pass
        try:
            if usr.objects.get(email=email):
                messages.error(request, "E-mail already exist")
                return redirect('usersignup')
            else:
                pass
        except Exception as identifier:
            pass
        try:
            if usr.objects.get(username=username):
                messages.error(request, "Try another username")
                return redirect('usersignup')
            else:
                pass
        except Exception as identifier:
            pass
        try:
            if usr.objects.get(phone=phone):
                messages.error(request, "Phone number already exist")
                return redirect('usersignup')
            else:
                pass
        except Exception as identifier:
            pass
        try:
            if usr.objects.get(password=password):
                messages.warning(request, "Try another password")
                return redirect('usersignup')
            else:
                pass
        except Exception as identifier:
            pass
        user = usr.objects.create(
            email=email, phone=phone, username=username, password=password, role='user', status='False')
        user.save()
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret, interval=300)
        otp = totp.now()
        send_mail('Furni', 'Your OTP code is'+str(otp)+' .Please use this OTP to verify your account',
                  'abhidharsh6@gmail.com', [user.email], fail_silently=False)
        response = redirect(f'otpverification/{user.userid}/{secret}')
        response.set_cookie("can_otp_enter", True, max_age=300)
        messages.success(request, 'Otp send to yout E-mail address')
        return response
    else:
        return redirect('usersignup')


def otpverification(request, userid, secret):
    if request.POST:
        totp = pyotp.TOTP(secret, interval=300)
        print(totp.now())
        try:
            user = usr.objects.get(userid=userid)
        except usr.DoesNotExist:
            messages.error(request, 'user not found')
            return redirect('usersignup')
        code = request.POST['1']+request.POST['2']+request.POST['3'] + \
            request.POST['4']+request.POST['5']+request.POST['6']
        if request.COOKIES.get('can_otp_enter') != None:
            if (totp.verify(code)):
                if (user.status != True):
                    user.status = True
                    user.save()
                    response = redirect('userlogin')
                    response.set_cookie('verified', True)
                    messages.success(request, 'Otp verified you can login now')
                    return response
                else:
                    messages.error(request, 'wrong otp')
                    return redirect('userlogin')
            else:
                messages.error(request, 'Wrong Otp')
                return redirect('userlogin')
        else:
            messages.error(request, 'Otp expired')
            return redirect('userlogin')
    else:
        return render(request, 'otpverification.html')


def forgot(request):
    return render(request, 'forgot.html')


def forg(request):
    if request.POST:
        email = request.POST['email']
        datac = usr.objects.filter(email=email).count()
        if datac == 1:
            user = usr.objects.get(email=email)
            secret = pyotp.random_base32()
            link = 'http://127.0.0.1:8000/newpwd?userid={}&secret={}'.format(
                user.userid, secret)
            send_mail('Furni', 'Click on this link to reset your password' +
                      link, 'abhidharsh6@gmail.com', [user.email], fail_silently=False)
            response = redirect('forgot')
            response.set_cookie("secretkey", secret, max_age=300)
            messages.success(
                request, 'Take a look on yout e-mail to reset the password')
            return response
        else:
            messages.warning(request, 'Invalid E-mail address')
            return redirect('forgot')
    else:
        messages.error(request, 'Something went wrong')
        return redirect('forgot')


def verification(request, userid, secret):
    if request.POST:
        totp = pyotp.TOTP(secret, interval=300)
        try:
            user = usr.objects.get(userid=userid)
        except usr.DoesNotExist:
            messages.error(request, 'user not found')
            return redirect('userlogin')
        code = request.POST['1']+request.POST['2']+request.POST['3'] + \
            request.POST['4']+request.POST['5']+request.POST['6']
        if request.COOKIES.get('can_otp_enter') != None:
            if (totp.verify(code)):
                userid = userid
                response = redirect('newpwd', {'userid': userid})
                response.set_cookie('verified', True)
                messages.success(request, 'Otp verified change your password')
                return response
            else:
                messages.error(request, 'enter your otp')
                return redirect('forgot')
        else:
            messages.error(request, 'something went wrong')
            return redirect('forgot')
    else:
        return render(request, 'verification.html')


def newpwd(request):
    usrid = request.GET.get('userid')
    sec = request.GET.get('secret')
    if request.POST:
        secretkey = request.COOKIES.get("secretkey")
        if secretkey == sec:
            password = request.POST['password']
            repassword = request.POST['repassword']
            if password != repassword:
                messages.warning(request, 'Password mismatch')
                return redirect('/newpwd')
            try:
                if usr.objects.get(password=password):
                    messages.warning(request, 'Try another password')
                    return redirect('newpwd')
                else:
                    pass
            except Exception as identifier:
                pass
            else:
                usr.objects.filter(userid=usrid).update(password=password)
                messages.success(
                    request, 'Password changed successfully Login now')
                return redirect('login')
        else:
            messages.error(request, 'invalid access or link expired')
            return redirect('newpwd')
    return render(request, 'newpwd.html')


def aprivacy(request):
    if request.POST:
        id = request.session['id']
        password = request.POST['password']
        repassword = request.POST['repassword']
        if password != repassword:
            messages.warning(request, 'Password mismatch')
            return redirect('adprivacy')
        else:
            pass
        try:
            if usr.objects.get(password=password):
                messages.warning(request, 'Try another password')
                return redirect('adprivacy')
            else:
                pass
        except Exception as identifier:
            pass
        try:
            user = usr.objects.get(userid=id)
        except usr.DoesNotExist:
            messages.warning(request, 'something went wrong')
            return redirect('adprivacy')
        try:
            if user.role == 'admin':
                usr.objects.filter(userid=id).update(password=password)
                messages.success(request, 'Password update successfully')
                return redirect('adprivacy')
            else:
                messages.error(request, 'you are fake')
                return redirect('adprivacy')
        except Exception as e:
            messages.error('Error occured:', e)
            return redirect('adprivacy')
    else:
        return redirect('adprivacy')


def uprivacy(request):
    if request.POST:
        id = request.session['id']
        password = request.POST['password']
        repassword = request.POST['repassword']
        if password != repassword:
            messages.warning(request, 'Password mismatch')
            return redirect('privacy')
        else:
            pass
        try:
            if usr.objects.get(password=password):
                messages.warning(request, 'Try another password')
                return redirect('privacy')
            else:
                pass
        except Exception as identifier:
            pass
        try:
            user = usr.objects.get(userid=id)
        except usr.DoesNotExist:
            messages.warning(request, 'something went wrong')
            return redirect('privacy')
        try:
            usr.objects.filter(userid=id).update(password=password)
            messages.success(request, 'Password update successfully')
            return redirect('privacy')
        except Exception as e:
            messages.error('Error occured:', e)
            return redirect('privacy')
    else:
        return redirect('privacy')


def logi(request):
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']
        datac = usr.objects.filter(
            username=username, password=password, status=True).count()
        if datac == 1:
            data = usr.objects.get(username=username, password=password)
            if data.role == 'user':
                request.session['username'] = data.username
                request.session['role'] = data.role
                request.session['id'] = data.userid
                return redirect('userhome')
            elif data.role == 'admin':
                request.session['username'] = data.username
                request.session['role'] = data.role
                request.session['id'] = data.userid
                return redirect('adminhome')
            elif data.role == 'blocked':
                messages.error(request, 'You are blocked by the admin')
                return redirect('userlogin')
            else:
                messages.warning(request, 'Invalid credentials')
                return redirect('userlogin')
        else:
            messages.warning(request, 'Invalid username or password')
            return redirect('userlogin')
    else:
        messages.warning(request, 'somthing went wrong')
        return redirect('userlogin')


def blockusr(request):
    uid = request.POST['uid']
    usr.objects.filter(userid=uid).update(role='blocked')
    messages.error(request, 'User blocked')
    return redirect('userlist')


def unblockusr(request):
    uid = request.POST['uid']
    usr.objects.filter(userid=uid).update(role='user')
    messages.success(request, 'User unblocked')
    return redirect('userlist')


def offer(request):
    if 'username' in request.session:
        return render(request, 'offer.html')
    else:
        return redirect('userlogin')


def addoffer(request):
    if request.POST:
        offername = request.POST['offername']
        offercode = request.POST['offercode']
        expirydate = request.POST['expirydate']
        offerpercentage = request.POST['offerpercentage']
        currentdate = datetime.now().date()
        expirydate1 = datetime.strptime(expirydate, '%Y-%m-%d').date()
        if expirydate1 <= currentdate:
            messages.error(
                request, "Expiry date should be beyond the current date")
            return redirect('offer')
        else:
            cp.objects.create(couponname=offername, couponcode=offercode,
                              expirytdate=expirydate, percentage=offerpercentage)
            messages.success(request, "Offer added successfully")
            return redirect('offer')
    else:
        return redirect('offer')


def offerlist(request):
    if 'username' in request.session:
        if 'search' in request.POST:
            s = request.POST['search']
            data = cp.objects.filter(
                Q(couponname__contains=s) | Q(couponcode__contains=s))
            if len(data) == 0:
                pass
            else:
                return render(request, 'offerlist.html', {'data': data})
        else:
            data = cp.objects.all()
            paginator = Paginator(data, 6)
            page_number = request.GET.get('page')
            data = paginator.get_page(page_number)
            return render(request, 'offerlist.html', {'data': data})
    else:
        return redirect('userlogin')


def deloffer(request):
    if request.POST:
        id = request.POST['cid']
        cp.objects.filter(couponid=id).delete()
        messages.success(request, "Offer deleted successffully")
        return redirect('offerlist')
    else:
        messages.error(request, "Operation failed")
        return redirect('offerlist')


def updateoffer(request):
    if request.POST:
        id = request.POST['cid']
        offername = request.POST['offername']
        offercode = request.POST['offercode']
        expirydate = request.POST['expirydate']
        offerpercentage = request.POST['offerpercentage']
        if not expirydate:
            cp.objects.filter(couponid=id).update(
                couponname=offername, couponcode=offercode, percentage=offerpercentage)
            return redirect('offerlist')
        else:
            expirydate1 = datetime.strptime(
                expirydate, '%Y-%m-%d').date()
            currentdate = datetime.now().date()
            if expirydate1 <= currentdate:
                messages.error(
                    request, "Expiry date should be beyond the current date")
                return redirect('offerlist')
            else:
                cp.objects.filter(couponid=id).update(
                    couponname=offername, couponcode=offercode, expirytdate=expirydate, percentage=offerpercentage)
                messages.success(request, "Offer updated successfully")
                return redirect('offerlist')
    else:
        messages.error(request, 'Operation failed')
        return redirect('offerlist')


def catoffer(request):
    if request.POST:
        id = request.POST['cid']
        offerpercentage = request.POST['offerpercentage']
        cat.objects.filter(categoryid=id).update(
            offerpercentage=offerpercentage)
        datac = pro.objects.filter(category=id).all()
        for i in datac:
            datap = i.price
            datad = int(datap)*(int(offerpercentage)/100)
            datao = int(datap)-int(datad)
            i.offerpercentage = offerpercentage
            i.discountprice = datao
            i.save()
        messages.success(
            request, "Offer added successfully and applied to the products")
        return redirect('categorylist')
    else:
        messages.error(request, "Operation failed")
        return redirect('categorylist')


def delcatoffer(request):
    if request.POST:
        id = request.POST['cid']
        cat.objects.filter(categoryid=id).update(offerpercentage=0)
        datac = pro.objects.filter(category=id).all()
        for i in datac:
            datao = i.price
            i.offerpercentage = 0
            i.discountprice = datao
            i.save()
        messages.success(request, "Offer removed")
        return redirect('categorylist')
    else:
        messages.success(request, "Operation failed")
        return redirect('categorylist')


def proffer(request):
    if request.POST:
        id = request.POST['pid']
        data = pro.objects.get(productid=id)
        datap = data.price
        offerpercentage = request.POST['offerpercentage']
        datad = int(datap)*(int(offerpercentage)/100)
        datao = int(datap)-int(datad)
        pro.objects.filter(productid=id).update(
            discountprice=datao, offerpercentage=offerpercentage)
        messages.success(request, 'Offer applied')
        return redirect('productlist')
    else:
        messages.error(request, 'Operation failed')
        return redirect('productlist')


def reproffer(request):
    if request.POST:
        id = request.POST['pid']
        data = pro.objects.get(productid=id)
        datad = data.price
        pro.objects.filter(productid=id).update(
            offerpercentage=0, discountprice=datad)
        messages.success(request, 'Offer removed')
        return redirect('productlist')
    else:
        messages.error(request, 'Operation failed')
        return redirect('productlist')
    

#extra
class wishlist(View):
    def get(self,request):
        return render(request,'')

