from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import connection, IntegrityError
from django.db.models import ProtectedError, Sum, F, Value
from django.db.models.functions import Coalesce
from decimal import Decimal
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.conf import settings
from apps.forms import *
from apps.models import *
from authentication.decorators import role_required


def _ctx(request, segment, crud, menu_id, **extra):
    """Context dasar halaman master (role + tombol aksi per menu)."""
    ctx = {
        'segment': segment,
        'group_segment': 'master',
        'crud': crud,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id=menu_id)
        if not request.user.is_superuser else Auth.objects.all(),
    }
    ctx.update(extra)
    return ctx


@login_required(login_url='/login/')
def home(request):
    # KPI Dashboard Pergudangan (Fase 1: master + saldo)
    total_sku = Item.objects.filter(is_active=True).count()
    total_gudang = Warehouse.objects.filter(is_active=True).count()
    total_lokasi = StorageLocation.objects.filter(is_active=True).count()
    total_mitra = Partner.objects.filter(is_active=True).count()
    total_stok = StockBalance.objects.aggregate(t=Sum('on_hand'))['t'] or 0
    di_bawah_minimum = Item.objects.filter(is_active=True).annotate(
        onhand=Coalesce(Sum('balances__on_hand'), Value(Decimal('0')))
    ).filter(minimum_stock__gt=0, onhand__lt=F('minimum_stock')).count()

    context = {
        'segment': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'kpi': {
            'sku': total_sku,
            'gudang': total_gudang,
            'lokasi': total_lokasi,
            'mitra': total_mitra,
            'stok': total_stok,
            'below_min': di_bawah_minimum,
        },
    }
    return render(request, 'home/index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def user_index(request):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT user_id, username, email, position_name FROM apps_user INNER JOIN apps_position ON apps_user.position_id = apps_position.position_id")
        users = cursor.fetchall()

    context = {
        'data': users,
        'segment': 'user',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/user_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def user_add(request):
    position = Position.objects.all()
    if request.POST:
        form = FormUser(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            if not settings.DEBUG and form.instance.signature:
                user = User.objects.get(user_id=form.instance.user_id)
                my_file = user.signature
                filename = '../../www/aqiqahon/apps/media/' + my_file.name
                with open(filename, 'wb+') as temp_file:
                    for chunk in my_file.chunks():
                        temp_file.write(chunk)

            return HttpResponseRedirect(reverse('user-view', args=[form.instance.user_id, ]))
        else:
            message = form.errors
            context = {
                'form': form,
                'position': position,
                'segment': 'user',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/user_add.html', context)
    else:
        form = FormUser()
        context = {
            'form': form,
            'position': position,
            'segment': 'user',
            'group_segment': 'master',
            'crud': 'add',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/user_add.html', context)


# View User
@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def user_view(request, _id):
    users = User.objects.get(user_id=_id)
    auth = Auth.objects.filter(user_id=_id)
    form = FormUserView(instance=users)
    position = Position.objects.all()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_menu.menu_id, menu_name, q_auth.menu_id FROM apps_menu LEFT JOIN (SELECT * FROM apps_auth WHERE user_id = '" + str(_id) + "') AS q_auth ON apps_menu.menu_id = q_auth.menu_id WHERE q_auth.menu_id IS NULL")
        menu = cursor.fetchall()

    if request.POST:
        check = request.POST.getlist('checks[]')
        for i in menu:
            if str(i[0]) in check:
                try:
                    auth = Auth(user_id=_id, menu_id=i[0])
                    auth.save()
                except IntegrityError:
                    continue
            else:
                Auth.objects.filter(user_id=_id, menu_id=i[0]).delete()

        return HttpResponseRedirect(reverse('user-view', args=[_id, ]))

    context = {
        'form': form,
        'formAuth': form,
        'data': users,
        'auth': auth,
        'menu': menu,
        'positions': position,
        'segment': 'user',
        'group_segment': 'master',
        'tab': 'auth',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/user_view.html', context)


# Update Auth
@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def auth_update(request, _id, _menu):
    auth = Auth.objects.get(user=_id, menu=_menu)

    if request.POST:
        auth.add = 1 if request.POST.get('add') else 0
        auth.edit = 1 if request.POST.get('edit') else 0
        auth.delete = 1 if request.POST.get('delete') else 0
        auth.save()

        return HttpResponseRedirect(reverse('user-view', args=[_id, ]))

    return render(request, 'home/user_view.html')


# Delete Auth
@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def auth_delete(request, _id, _menu):
    auth = Auth.objects.filter(user=_id, menu=_menu)

    auth.delete()
    return HttpResponseRedirect(reverse('user-view', args=[_id, ]))


# Remove Signature
@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def remove_signature(request, _id):
    users = User.objects.get(user_id=_id)
    users.signature = None
    users.save()
    return HttpResponseRedirect(reverse('user-view', args=[_id, ]))


# Update User
@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def user_update(request, _id):
    users = User.objects.get(user_id=_id)
    position = Position.objects.all()
    auth = Auth.objects.filter(user_id=_id)

    if request.POST:
        form = FormUserUpdate(request.POST, request.FILES, instance=users)
        if form.is_valid():
            form.save()
            if not settings.DEBUG and users.signature:
                my_file = users.signature
                filename = '../../www/aqiqahon/apps/media/' + my_file.name
                with open(filename, 'wb+') as temp_file:
                    for chunk in my_file.chunks():
                        temp_file.write(chunk)
            return HttpResponseRedirect(reverse('user-view', args=[_id, ]))
    else:
        form = FormUserUpdate(instance=users)

    message = form.errors
    context = {
        'form': form,
        'data': users,
        'positions': position,
        'auth': auth,
        'segment': 'user',
        'group_segment': 'master',
        'crud': 'update',
        'tab': 'auth',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/user_view.html', context)


# Delete User
@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def user_delete(request, _id):
    users = User.objects.get(user_id=_id)

    users.delete()
    return HttpResponseRedirect(reverse('user-index'))


@login_required(login_url='/login/')
def change_password(request):
    if request.POST:
        form = FormChangePassword(data=request.POST, user=request.user)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return HttpResponseRedirect(reverse('home'))
    else:
        form = FormChangePassword(user=request.user)

    message = form.errors
    context = {
        'form': form,
        'data': request.user,
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
    }
    return render(request, 'home/user_change_password.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def set_password(request, _id):
    users = User.objects.get(user_id=_id)
    if request.POST:
        form = FormSetPassword(data=request.POST, user=users)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return HttpResponseRedirect(reverse('user-view', args=[_id, ]))
    else:
        form = FormSetPassword(user=users)

    message = form.errors
    context = {
        'form': form,
        'data': users,
        'segment': 'user',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/user_set_password.html', context)


# ------------------------------------------------------------------
# Posisi
# ------------------------------------------------------------------
@login_required(login_url='/login/')
@role_required(allowed_roles='POSITION')
def position_add(request):
    if request.POST:
        form = FormPosition(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('position-index'))
        else:
            message = form.errors
            context = {
                'form': form,
                'segment': 'position',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='POSITION') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/position_add.html', context)
    else:
        form = FormPosition()
        context = {
            'form': form,
            'segment': 'position',
            'group_segment': 'master',
            'crud': 'add',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='POSITION') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/position_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='POSITION')
def position_index(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT position_id, position_name FROM apps_position")
        positions = cursor.fetchall()

    context = {
        'data': positions,
        'segment': 'position',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='POSITION') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/position_index.html', context)


# Update Position
@login_required(login_url='/login/')
@role_required(allowed_roles='POSITION')
def position_update(request, _id):
    positions = Position.objects.get(position_id=_id)
    if request.POST:
        form = FormPositionUpdate(
            request.POST, request.FILES, instance=positions)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('position-view', args=[_id, ]))
    else:
        form = FormPositionUpdate(instance=positions)

    message = form.errors
    context = {
        'form': form,
        'data': positions,
        'segment': 'position',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='POSITION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/position_view.html', context)


# Delete Position
@login_required(login_url='/login/')
@role_required(allowed_roles='POSITION')
def position_delete(request, _id):
    positions = Position.objects.get(position_id=_id)

    positions.delete()
    return HttpResponseRedirect(reverse('position-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='POSITION')
def position_view(request, _id):
    positions = Position.objects.get(position_id=_id)
    form = FormPositionView(instance=positions)

    context = {
        'form': form,
        'data': positions,
        'segment': 'position',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='POSITION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/position_view.html', context)


# ------------------------------------------------------------------
# Menu
# ------------------------------------------------------------------
@login_required(login_url='/login/')
@role_required(allowed_roles='MENU')
def menu_add(request):
    if request.POST:
        form = FormMenu(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('menu-index'))
        else:
            message = form.errors
            context = {
                'form': form,
                'segment': 'menu',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='MENU') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/menu_add.html', context)
    else:
        form = FormMenu()
        context = {
            'form': form,
            'segment': 'menu',
            'group_segment': 'master',
            'crud': 'add',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='MENU') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/menu_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='MENU')
def menu_index(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT menu_id, menu_name, menu_remark FROM apps_menu")
        menus = cursor.fetchall()

    context = {
        'data': menus,
        'segment': 'menu',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='MENU') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/menu_index.html', context)


# Update Menu
@login_required(login_url='/login/')
@role_required(allowed_roles='MENU')
def menu_update(request, _id):
    menus = Menu.objects.get(menu_id=_id)
    if request.POST:
        form = FormMenuUpdate(request.POST, request.FILES, instance=menus)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('menu-view', args=[_id, ]))
    else:
        form = FormMenuUpdate(instance=menus)

    message = form.errors
    context = {
        'form': form,
        'data': menus,
        'segment': 'menu',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='MENU') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/menu_view.html', context)


# Delete Menu
@login_required(login_url='/login/')
@role_required(allowed_roles='MENU')
def menu_delete(request, _id):
    menus = Menu.objects.get(menu_id=_id)

    menus.delete()
    return HttpResponseRedirect(reverse('menu-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='MENU')
def menu_view(request, _id):
    menus = Menu.objects.get(menu_id=_id)
    form = FormMenuView(instance=menus)

    context = {
        'form': form,
        'data': menus,
        'segment': 'menu',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='MENU') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/menu_view.html', context)


# ==================================================================
# Master: Satuan
# ==================================================================
@login_required(login_url='/login/')
@role_required(allowed_roles='SAT')
def unit_index(request):
    data = Unit.objects.all().order_by('code')
    return render(request, 'home/unit_index.html', _ctx(request, 'unit', 'index', 'SAT', data=data))


@login_required(login_url='/login/')
@role_required(allowed_roles='SAT')
def unit_add(request):
    if request.POST:
        form = FormUnit(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('unit-view', args=[form.instance.pk]))
        return render(request, 'home/unit_add.html', _ctx(request, 'unit', 'add', 'SAT', form=form, message=form.errors))
    return render(request, 'home/unit_add.html', _ctx(request, 'unit', 'add', 'SAT', form=FormUnit()))


@login_required(login_url='/login/')
@role_required(allowed_roles='SAT')
def unit_view(request, _id):
    data = Unit.objects.get(pk=_id)
    form = FormUnitView(instance=data)
    return render(request, 'home/unit_view.html', _ctx(request, 'unit', 'view', 'SAT', form=form, data=data))


@login_required(login_url='/login/')
@role_required(allowed_roles='SAT')
def unit_update(request, _id):
    data = Unit.objects.get(pk=_id)
    if request.POST:
        form = FormUnit(request.POST, instance=data)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('unit-view', args=[_id]))
        return render(request, 'home/unit_view.html', _ctx(request, 'unit', 'update', 'SAT', form=FormUnitView(instance=data), data=data, message=form.errors))
    return render(request, 'home/unit_view.html', _ctx(request, 'unit', 'update', 'SAT', form=FormUnit(instance=data), data=data))


@login_required(login_url='/login/')
@role_required(allowed_roles='SAT')
def unit_delete(request, _id):
    Unit.objects.get(pk=_id).delete()
    return HttpResponseRedirect(reverse('unit-index'))


# ==================================================================
# Master: Kategori Barang
# ==================================================================
@login_required(login_url='/login/')
@role_required(allowed_roles='KTG')
def category_index(request):
    data = ItemCategory.objects.all().order_by('code')
    return render(request, 'home/category_index.html', _ctx(request, 'category', 'index', 'KTG', data=data))


@login_required(login_url='/login/')
@role_required(allowed_roles='KTG')
def category_add(request):
    if request.POST:
        form = FormCategory(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('category-view', args=[form.instance.pk]))
        return render(request, 'home/category_add.html', _ctx(request, 'category', 'add', 'KTG', form=form, message=form.errors))
    return render(request, 'home/category_add.html', _ctx(request, 'category', 'add', 'KTG', form=FormCategory()))


@login_required(login_url='/login/')
@role_required(allowed_roles='KTG')
def category_view(request, _id):
    data = ItemCategory.objects.get(pk=_id)
    form = FormCategoryView(instance=data)
    return render(request, 'home/category_view.html', _ctx(request, 'category', 'view', 'KTG', form=form, data=data))


@login_required(login_url='/login/')
@role_required(allowed_roles='KTG')
def category_update(request, _id):
    data = ItemCategory.objects.get(pk=_id)
    if request.POST:
        form = FormCategory(request.POST, instance=data)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('category-view', args=[_id]))
        return render(request, 'home/category_view.html', _ctx(request, 'category', 'update', 'KTG', form=FormCategoryView(instance=data), data=data, message=form.errors))
    return render(request, 'home/category_view.html', _ctx(request, 'category', 'update', 'KTG', form=FormCategory(instance=data), data=data))


@login_required(login_url='/login/')
@role_required(allowed_roles='KTG')
def category_delete(request, _id):
    data = ItemCategory.objects.get(pk=_id)
    try:
        data.delete()
    except ProtectedError:
        pass
    return HttpResponseRedirect(reverse('category-index'))


# ==================================================================
# Master: Mitra (Supplier / Pelanggan)
# ==================================================================
@login_required(login_url='/login/')
@role_required(allowed_roles='MIT')
def partner_index(request):
    data = Partner.objects.all().order_by('code')
    return render(request, 'home/partner_index.html', _ctx(request, 'partner', 'index', 'MIT', data=data))


@login_required(login_url='/login/')
@role_required(allowed_roles='MIT')
def partner_add(request):
    if request.POST:
        form = FormPartner(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('partner-view', args=[form.instance.pk]))
        return render(request, 'home/partner_add.html', _ctx(request, 'partner', 'add', 'MIT', form=form, message=form.errors))
    return render(request, 'home/partner_add.html', _ctx(request, 'partner', 'add', 'MIT', form=FormPartner()))


@login_required(login_url='/login/')
@role_required(allowed_roles='MIT')
def partner_view(request, _id):
    data = Partner.objects.get(pk=_id)
    form = FormPartnerView(instance=data)
    return render(request, 'home/partner_view.html', _ctx(request, 'partner', 'view', 'MIT', form=form, data=data))


@login_required(login_url='/login/')
@role_required(allowed_roles='MIT')
def partner_update(request, _id):
    data = Partner.objects.get(pk=_id)
    if request.POST:
        form = FormPartner(request.POST, instance=data)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('partner-view', args=[_id]))
        return render(request, 'home/partner_view.html', _ctx(request, 'partner', 'update', 'MIT', form=FormPartnerView(instance=data), data=data, message=form.errors))
    return render(request, 'home/partner_view.html', _ctx(request, 'partner', 'update', 'MIT', form=FormPartner(instance=data), data=data))


@login_required(login_url='/login/')
@role_required(allowed_roles='MIT')
def partner_delete(request, _id):
    Partner.objects.get(pk=_id).delete()
    return HttpResponseRedirect(reverse('partner-index'))


# ==================================================================
# Master: Gudang
# ==================================================================
@login_required(login_url='/login/')
@role_required(allowed_roles='GUD')
def warehouse_index(request):
    data = Warehouse.objects.all().order_by('code')
    return render(request, 'home/warehouse_index.html', _ctx(request, 'warehouse', 'index', 'GUD', data=data))


@login_required(login_url='/login/')
@role_required(allowed_roles='GUD')
def warehouse_add(request):
    if request.POST:
        form = FormWarehouse(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('warehouse-view', args=[form.instance.pk]))
        return render(request, 'home/warehouse_add.html', _ctx(request, 'warehouse', 'add', 'GUD', form=form, message=form.errors))
    return render(request, 'home/warehouse_add.html', _ctx(request, 'warehouse', 'add', 'GUD', form=FormWarehouse()))


@login_required(login_url='/login/')
@role_required(allowed_roles='GUD')
def warehouse_view(request, _id):
    data = Warehouse.objects.get(pk=_id)
    form = FormWarehouseView(instance=data)
    return render(request, 'home/warehouse_view.html', _ctx(request, 'warehouse', 'view', 'GUD', form=form, data=data))


@login_required(login_url='/login/')
@role_required(allowed_roles='GUD')
def warehouse_update(request, _id):
    data = Warehouse.objects.get(pk=_id)
    if request.POST:
        form = FormWarehouse(request.POST, instance=data)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('warehouse-view', args=[_id]))
        return render(request, 'home/warehouse_view.html', _ctx(request, 'warehouse', 'update', 'GUD', form=FormWarehouseView(instance=data), data=data, message=form.errors))
    return render(request, 'home/warehouse_view.html', _ctx(request, 'warehouse', 'update', 'GUD', form=FormWarehouse(instance=data), data=data))


@login_required(login_url='/login/')
@role_required(allowed_roles='GUD')
def warehouse_delete(request, _id):
    data = Warehouse.objects.get(pk=_id)
    try:
        data.delete()
    except ProtectedError:
        pass
    return HttpResponseRedirect(reverse('warehouse-index'))


# ==================================================================
# Master: Lokasi Penyimpanan
# ==================================================================
@login_required(login_url='/login/')
@role_required(allowed_roles='LOK')
def location_index(request):
    data = StorageLocation.objects.select_related(
        'warehouse').order_by('warehouse__code', 'code')
    return render(request, 'home/location_index.html', _ctx(request, 'location', 'index', 'LOK', data=data))


@login_required(login_url='/login/')
@role_required(allowed_roles='LOK')
def location_add(request):
    if request.POST:
        form = FormLocation(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('location-view', args=[form.instance.pk]))
        return render(request, 'home/location_add.html', _ctx(request, 'location', 'add', 'LOK', form=form, message=form.errors))
    return render(request, 'home/location_add.html', _ctx(request, 'location', 'add', 'LOK', form=FormLocation()))


@login_required(login_url='/login/')
@role_required(allowed_roles='LOK')
def location_view(request, _id):
    data = StorageLocation.objects.select_related('warehouse').get(pk=_id)
    form = FormLocationView(instance=data)
    return render(request, 'home/location_view.html', _ctx(request, 'location', 'view', 'LOK', form=form, data=data))


@login_required(login_url='/login/')
@role_required(allowed_roles='LOK')
def location_update(request, _id):
    data = StorageLocation.objects.select_related('warehouse').get(pk=_id)
    if request.POST:
        form = FormLocation(request.POST, instance=data)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('location-view', args=[_id]))
        return render(request, 'home/location_view.html', _ctx(request, 'location', 'update', 'LOK', form=FormLocationView(instance=data), data=data, message=form.errors))
    return render(request, 'home/location_view.html', _ctx(request, 'location', 'update', 'LOK', form=FormLocation(instance=data), data=data))


@login_required(login_url='/login/')
@role_required(allowed_roles='LOK')
def location_delete(request, _id):
    data = StorageLocation.objects.get(pk=_id)
    try:
        data.delete()
    except ProtectedError:
        pass
    return HttpResponseRedirect(reverse('location-index'))


# ==================================================================
# Master: Barang
# ==================================================================
@login_required(login_url='/login/')
@role_required(allowed_roles='BRG')
def item_index(request):
    data = Item.objects.select_related('category', 'uom').order_by('sku')
    return render(request, 'home/item_index.html', _ctx(request, 'item', 'index', 'BRG', data=data))


@login_required(login_url='/login/')
@role_required(allowed_roles='BRG')
def item_add(request):
    if request.POST:
        form = FormItem(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('item-view', args=[form.instance.pk]))
        return render(request, 'home/item_add.html', _ctx(request, 'item', 'add', 'BRG', form=form, message=form.errors))
    return render(request, 'home/item_add.html', _ctx(request, 'item', 'add', 'BRG', form=FormItem()))


@login_required(login_url='/login/')
@role_required(allowed_roles='BRG')
def item_view(request, _id):
    data = Item.objects.select_related('category', 'uom').get(pk=_id)
    form = FormItemView(instance=data)
    return render(request, 'home/item_view.html', _ctx(request, 'item', 'view', 'BRG', form=form, data=data))


@login_required(login_url='/login/')
@role_required(allowed_roles='BRG')
def item_update(request, _id):
    data = Item.objects.select_related('category', 'uom').get(pk=_id)
    if request.POST:
        form = FormItem(request.POST, instance=data)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('item-view', args=[_id]))
        return render(request, 'home/item_view.html', _ctx(request, 'item', 'update', 'BRG', form=FormItemView(instance=data), data=data, message=form.errors))
    return render(request, 'home/item_view.html', _ctx(request, 'item', 'update', 'BRG', form=FormItem(instance=data), data=data))


@login_required(login_url='/login/')
@role_required(allowed_roles='BRG')
def item_delete(request, _id):
    data = Item.objects.get(pk=_id)
    try:
        data.delete()
    except ProtectedError:
        pass
    return HttpResponseRedirect(reverse('item-index'))
