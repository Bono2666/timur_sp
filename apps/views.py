from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import connection, IntegrityError, transaction
from django.db.models import ProtectedError, Q, Sum, F, Value
from django.db.models.functions import Coalesce
from decimal import Decimal
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
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


def health(request):
    """Endpoint liveness untuk health-check (tanpa auth)."""
    return JsonResponse({'status': 'ok', 'app': 'tsp-warehouse'})


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

    # KPI Penerimaan Barang (Fase 2)
    bulan_ini = timezone.now().replace(day=1, hour=0, minute=0,
                                       second=0, microsecond=0)
    rcv_pending_approval = StockDocument.objects.filter(
        document_type='RCV', status__in=['draft', 'submitted']).count()
    rcv_await_validation = StockDocument.objects.filter(
        document_type='RCV', status='approved',
        receive_status='pending').count()
    rcv_posted_month = StockDocument.objects.filter(
        document_type='RCV', status='posted',
        posted_at__gte=bulan_ini).count()
    rcv_putaway_pending = StockDocument.objects.filter(
        document_type='RCV', status='posted',
        putaway_status='pending').count()

    context = {
        'segment': 'index',
        'group_segment': 'dashboard',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'kpi': {
            'sku': total_sku,
            'gudang': total_gudang,
            'lokasi': total_lokasi,
            'mitra': total_mitra,
            'stok': total_stok,
            'below_min': di_bawah_minimum,
            'rcv_pending_approval': rcv_pending_approval,
            'rcv_await_validation': rcv_await_validation,
            'rcv_posted_month': rcv_posted_month,
            'rcv_putaway_pending': rcv_putaway_pending,
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


def _render_location_labels_pdf(items):
    """Render label lokasi: 1 lokasi = 1 halaman PDF 90x42mm.

    Format: Nama Lokasi di atas (rata tengah), barcode + angkanya di bawah.
    Nilai barcode: field barcode, fallback kode lokasi.
    """
    from io import BytesIO
    from reportlab.lib.units import mm
    from reportlab.lib.utils import simpleSplit
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.graphics.barcode.code128 import Code128

    page_w, page_h = 90 * mm, 42 * mm
    pad = 4 * mm
    buf = BytesIO()
    canvas = pdf_canvas.Canvas(buf, pagesize=(page_w, page_h))
    canvas.setTitle('Label Lokasi - TSP Warehouse')

    for loc in items:
        # Nama lokasi di atas, rata tengah, maksimal 2 baris
        canvas.setFillColorRGB(0.05, 0.05, 0.05)
        canvas.setFont('Helvetica-Bold', 14)
        lines = simpleSplit(loc.name or loc.code, 'Helvetica-Bold', 14,
                            page_w - 2 * pad)
        if len(lines) > 2:
            lines = lines[:2]
            while lines[1] and stringWidth(
                    lines[1] + '...', 'Helvetica-Bold', 14) > page_w - 2 * pad:
                lines[1] = lines[1][:-1]
            lines[1] += '...'
        for i, ln in enumerate(lines):
            canvas.drawCentredString(page_w / 2, page_h - 9 * mm - i * 5.4 * mm, ln)

        # Barcode di bawah, rata tengah + nilai barcode di bawahnya
        code = (loc.barcode or loc.code or '').strip()
        bc = None
        if code and code.isascii():
            try:
                bc = Code128(code, barHeight=11 * mm, barWidth=0.27 * mm,
                             humanReadable=False)
            except Exception:
                bc = None
        if bc is not None:
            bc.drawOn(canvas, (page_w - bc.width) / 2, 10 * mm)
            canvas.setFont('Helvetica', 9)
            canvas.setFillColorRGB(0.05, 0.05, 0.05)
            canvas.drawCentredString(page_w / 2, 6.4 * mm, code)
        else:
            canvas.setFont('Helvetica-Oblique', 7.5)
            canvas.setFillColorRGB(0.68, 0.68, 0.68)
            canvas.drawCentredString(page_w / 2, 13 * mm, 'TANPA BARCODE')

        canvas.showPage()

    canvas.save()
    return buf.getvalue()


@login_required(login_url='/login/')
@role_required(allowed_roles='LOK')
def location_label_print(request):
    """Cetak label penyimpanan terpilih: PDF, 1 lokasi = 1 halaman 90x42mm."""
    id_list = [int(x) for x in request.GET.get('ids', '').split(',')
               if x.strip().isdigit()]
    items = (StorageLocation.objects.filter(pk__in=id_list).select_related(
        'warehouse').order_by('warehouse__code', 'code') if id_list else [])
    if not items:
        return HttpResponseRedirect(reverse('location-index'))
    pdf = _render_location_labels_pdf(items)
    return HttpResponse(pdf, content_type='application/pdf', headers={
        'Content-Disposition': 'inline; filename="label-lokasi.pdf"'})


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


def _render_labels_pdf(items):
    """Render label sticker: 1 barang = 1 halaman PDF seukuran label 90x42mm."""
    from io import BytesIO
    from reportlab.lib.units import mm
    from reportlab.lib.utils import simpleSplit
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.graphics.barcode.code128 import Code128

    page_w, page_h = 90 * mm, 42 * mm
    pad = 4 * mm
    buf = BytesIO()
    canvas = pdf_canvas.Canvas(buf, pagesize=(page_w, page_h))
    canvas.setTitle('Label Barang - TSP Warehouse')

    for item in items:
        code = (item.barcode or '').strip()
        bc = None
        if code and code.isascii():
            try:
                bc = Code128(code, barHeight=11 * mm, barWidth=0.27 * mm,
                             humanReadable=False)
            except Exception:
                bc = None
        canvas.setFillColorRGB(0.05, 0.05, 0.05)
        if bc is not None:
            # barcode rata tengah + angka barcode di bawahnya
            bc.drawOn(canvas, (page_w - bc.width) / 2, page_h - pad - 11 * mm)
            canvas.setFont('Helvetica', 8.5)
            canvas.drawCentredString(page_w / 2, page_h - pad - 14.8 * mm, code)
        else:
            canvas.setFont('Helvetica-Oblique', 7.5)
            canvas.setFillColorRGB(0.68, 0.68, 0.68)
            canvas.drawCentredString(page_w / 2, page_h - 11 * mm, 'TANPA BARCODE')

        # Nama barang: tebal, maksimal 3 baris, elipsis bila terpotong
        canvas.setFillColorRGB(0.05, 0.05, 0.05)
        canvas.setFont('Helvetica-Bold', 12.5)
        lines = simpleSplit(item.name or '', 'Helvetica-Bold', 12.5,
                            page_w - 2 * pad)
        if len(lines) > 3:
            lines = lines[:3]
            while lines[2] and stringWidth(
                    lines[2] + '...', 'Helvetica-Bold', 12.5) > page_w - 2 * pad:
                lines[2] = lines[2][:-1]
            lines[2] += '...'
        first_y = page_h - 24 * mm
        for i, ln in enumerate(lines):
            canvas.drawString(pad, first_y - i * 4.9 * mm, ln)

        # SKU di kiri bawah
        canvas.setFont('Helvetica', 8.5)
        canvas.setFillColorRGB(0.27, 0.27, 0.27)
        canvas.drawString(pad, 4 * mm, item.sku)

        canvas.showPage()

    canvas.save()
    return buf.getvalue()


@login_required(login_url='/login/')
@role_required(allowed_roles='BRG')
def item_label_print(request):
    """Cetak label sticker barang terpilih: PDF, 1 label = 1 halaman seukuran label."""
    id_list = [int(x) for x in request.GET.get('ids', '').split(',')
               if x.strip().isdigit()]
    items = (Item.objects.filter(pk__in=id_list).select_related(
        'category', 'uom').order_by('sku') if id_list else [])
    if not items:
        return HttpResponseRedirect(reverse('item-index'))
    pdf = _render_labels_pdf(items)
    return HttpResponse(pdf, content_type='application/pdf', headers={
        'Content-Disposition': 'inline; filename="label-barang.pdf"'})


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


# ==================================================================
# Transaksi Gudang: Penerimaan Barang (Fase 2)
# ==================================================================
def _rctx(request, crud, **extra):
    ctx = {
        'segment': 'receipt',
        'group_segment': 'transaction',
        'crud': crud,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.filter(
            user_id=request.user.user_id, menu_id='RCV').first()
        if not request.user.is_superuser else Auth.objects.all(),
    }
    ctx.update(extra)
    return ctx


def _receipt_refs():
    """Data referensi untuk select pada form baris."""
    return {
        'items': Item.objects.filter(is_active=True).order_by('sku'),
        'locations': StorageLocation.objects.filter(
            is_active=True).select_related('warehouse').order_by('warehouse__code', 'code'),
        'receiving_locations': StorageLocation.objects.filter(
            is_active=True, location_type='receiving'
        ).select_related('warehouse').order_by('warehouse__code', 'code'),
    }


def _parse_lines(request, warehouse):
    """Parse baris detail dari POST. Return (lines, errors)."""
    items = request.POST.getlist('line_item')
    locs = request.POST.getlist('line_loc')
    qtys = request.POST.getlist('line_qty')
    notes = request.POST.getlist('line_note')
    lines, errors = [], []

    for i, item_raw in enumerate(items):
        if not str(item_raw).strip():
            continue
        loc_raw = locs[i] if i < len(locs) else ''
        qty_raw = qtys[i] if i < len(qtys) else ''
        note_raw = notes[i] if i < len(notes) else ''
        try:
            item = Item.objects.get(pk=int(item_raw))
        except (Item.DoesNotExist, ValueError, TypeError):
            errors.append('Baris %d: barang tidak valid.' % (i + 1))
            continue
        try:
            loc = StorageLocation.objects.get(pk=int(loc_raw))
        except (StorageLocation.DoesNotExist, ValueError, TypeError):
            errors.append('Baris %d: lokasi tujuan wajib dipilih.' % (i + 1))
            continue
        if loc.warehouse_id != warehouse.pk:
            errors.append('Baris %d: lokasi tujuan bukan milik gudang terpilih.' % (i + 1))
            continue
        try:
            qty = Decimal(str(qty_raw))
        except Exception:
            errors.append('Baris %d: kuantitas tidak valid.' % (i + 1))
            continue
        if qty <= 0:
            errors.append('Baris %d: kuantitas harus lebih besar dari 0.' % (i + 1))
            continue
        if qty != qty.to_integral_value():
            errors.append('Baris %d: kuantitas harus bilangan bulat.' % (i + 1))
            continue
        lines.append({'item': item, 'loc': loc, 'qty': qty, 'note': note_raw})

    if not lines and not errors:
        errors.append('Dokumen harus memiliki minimal 1 baris barang.')
    return lines, errors


def _save_lines(doc, lines):
    StockDocumentLine.objects.filter(document=doc).delete()
    for l in lines:
        StockDocumentLine.objects.create(
            document=doc, item=l['item'], destination_location=l['loc'],
            quantity=l['qty'], notes=l['note'])


def _render_receipt_view(request, doc, error=None, extra_status=None):
    doc = StockDocument.objects.select_related(
        'warehouse', 'partner').prefetch_related('lines__item').get(pk=doc.pk)
    lines = list(doc.lines.select_related('item', 'destination_location'))
    sod_block = (doc.created_by == request.user.user_id
                 and not request.user.is_superuser)
    ctx = _rctx(request, 'view', data=doc, lines=lines, sod_block=sod_block)
    if error:
        ctx['message'] = error
    if extra_status:
        ctx['info'] = extra_status
    return render(request, 'home/receipt_view.html', ctx)


def _balance_locked(location, item):
    """Ambil/buat saldo (harus dipanggil di dalam transaction.atomic)."""
    bal, _ = StockBalance.objects.select_for_update().get_or_create(
        item=item, location=location,
        defaults={'warehouse': location.warehouse,
                  'on_hand': Decimal('0'), 'reserved': Decimal('0')})
    return bal


def _apply_ledger(warehouse, location, item, qty, move_type, reference, notes, actor):
    """Tulis ledger + mutasi saldo (harus dalam transaction.atomic)."""
    StockLedger.objects.create(
        item=item, warehouse=warehouse, location=location, quantity=qty,
        move_type=move_type, reference=reference, notes=notes,
        actor=actor, posted_at=timezone.now())
    bal = _balance_locked(location, item)
    delta = qty if move_type == 'IN' else -qty
    bal.on_hand = (bal.on_hand or Decimal('0')) + delta
    bal.save(update_fields=['on_hand'])
    return bal


def _post_receipt(doc_id, actor):
    """Posting atomik: tulis ledger + update saldo. Idempoten (status lock)."""
    with transaction.atomic():
        doc = StockDocument.objects.select_for_update().get(pk=doc_id)
        if doc.status != 'approved':
            raise ValueError('Dokumen belum berstatus Approved.')
        if doc.receive_status != 'done':
            raise ValueError(
                'Lakukan Validasi Penerimaan terlebih dahulu sebelum posting.')
        for line in doc.lines.all():
            accepted = line.accepted_qty or Decimal('0')
            rejected = line.rejected_qty or Decimal('0')
            # Barang layak: 1 tahap -> lokasi tujuan, 2 tahap -> lokasi receiving
            if accepted > 0:
                target = (doc.receiving_location
                          if doc.operation_type == 'staged'
                          else line.destination_location)
                _apply_ledger(doc.warehouse, target, line.item, accepted, 'IN',
                              doc.number,
                              'Diterima layak (%s)' % line.item.sku, actor)
            # Barang rusak/tolak -> lokasi karantina (US-RCV-04)
            if rejected > 0 and line.quarantine_location:
                _apply_ledger(doc.warehouse, line.quarantine_location,
                              line.item, rejected, 'IN', doc.number,
                              'Karantina/tolak (%s)' % line.item.sku, actor)
        doc.status = 'posted'
        doc.posted_at = timezone.now()
        doc.putaway_status = ('pending' if doc.operation_type == 'staged'
                              else 'none')
        doc.save()
    return doc


@login_required(login_url='/login/')
@role_required(allowed_roles='RCV')
def receipt_index(request):
    status = request.GET.get('status', '')
    data = StockDocument.objects.select_related(
        'warehouse', 'partner').prefetch_related('lines')
    # Penyaringan mengikuti status scan (StockDocument.scan_state)
    scan_filters = {
        'pending_approval': Q(status__in=['draft', 'submitted']),
        'await_validation': Q(status='approved', receive_status='pending'),
        'validated': Q(status='approved', receive_status='done'),
        'putaway': Q(putaway_status='pending'),
        'done': Q(status='posted', putaway_status__in=['none', 'done']),
        'cancelled': Q(status__in=['cancelled', 'rejected']),
    }
    if status in scan_filters:
        data = data.filter(scan_filters[status])
    return render(request, 'home/receipt_index.html', _rctx(
        request, 'index', data=data, filter_status=status))


@login_required(login_url='/login/')
@role_required(allowed_roles='RCV')
def receipt_add(request):
    refs = _receipt_refs()
    if request.POST:
        form = FormReceipt(request.POST)
        if form.is_valid():
            warehouse = form.cleaned_data['warehouse']
            lines, line_errors = _parse_lines(request, warehouse)
            if line_errors:
                return render(request, 'home/receipt_add.html', _rctx(
                    request, 'add', form=form, message=line_errors, **refs))
            with transaction.atomic():
                doc = form.save(commit=False)
                doc.document_type = 'RCV'
                doc.number = DocumentSequence.next_number_for('RCV')
                doc.created_by = request.user.user_id
                doc.status = 'draft'
                doc.save()
                _save_lines(doc, lines)
            return HttpResponseRedirect(reverse('receipt-view', args=[doc.pk]))
        return render(request, 'home/receipt_add.html', _rctx(
            request, 'add', form=form, message=form.errors, **refs))
    return render(request, 'home/receipt_add.html', _rctx(
        request, 'add', form=FormReceipt(initial={'document_date': timezone.now().date()}), **refs))


@login_required(login_url='/login/')
@role_required(allowed_roles='RCV')
def receipt_edit(request, _id):
    doc = StockDocument.objects.get(pk=_id)
    if doc.status != 'draft':
        return HttpResponseRedirect(reverse('receipt-view', args=[_id]))
    refs = _receipt_refs()
    refs['existing_lines'] = doc.lines.select_related(
        'item', 'destination_location')
    refs['edit_doc'] = doc
    if request.POST:
        form = FormReceipt(request.POST, instance=doc)
        if form.is_valid():
            warehouse = form.cleaned_data['warehouse']
            lines, line_errors = _parse_lines(request, warehouse)
            if line_errors:
                return render(request, 'home/receipt_add.html', _rctx(
                    request, 'update', form=form, message=line_errors, **refs))
            with transaction.atomic():
                doc = form.save(commit=False)
                doc.save()
                _save_lines(doc, lines)
            return HttpResponseRedirect(reverse('receipt-view', args=[_id]))
        return render(request, 'home/receipt_add.html', _rctx(
            request, 'update', form=form, message=form.errors, **refs))
    return render(request, 'home/receipt_add.html', _rctx(
        request, 'update', form=FormReceipt(instance=doc), **refs))


@login_required(login_url='/login/')
@role_required(allowed_roles='RCV')
def receipt_view(request, _id):
    doc = StockDocument.objects.get(pk=_id)
    return _render_receipt_view(request, doc)


@login_required(login_url='/login/')
@role_required(allowed_roles='RCV')
def receipt_submit(request, _id):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('receipt-view', args=[_id]))
    with transaction.atomic():
        doc = StockDocument.objects.select_for_update().get(pk=_id)
        if doc.status != 'draft':
            return _render_receipt_view(request, doc, error='Hanya dokumen Draft yang dapat di-submit.')
        doc.status = 'submitted'
        doc.submitted_by = request.user.user_id
        doc.reject_reason = None
        doc.save()
    return HttpResponseRedirect(reverse('receipt-view', args=[_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='RCV')
def receipt_approve(request, _id):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('receipt-view', args=[_id]))
    with transaction.atomic():
        doc = StockDocument.objects.select_for_update().get(pk=_id)
        if doc.status != 'submitted':
            return _render_receipt_view(request, doc, error='Hanya dokumen Submitted yang dapat disetujui.')
        # Segregation of duties: pembuat tidak boleh approve dokumennya sendiri
        if doc.created_by == request.user.user_id and not request.user.is_superuser:
            return _render_receipt_view(
                request, doc,
                error='Anda tidak dapat menyetujui dokumen yang Anda buat sendiri (segregation of duties).')
        doc.status = 'approved'
        doc.approved_by = request.user.user_id
        doc.save()
    return HttpResponseRedirect(reverse('receipt-view', args=[_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='RCV')
def receipt_reject(request, _id):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('receipt-view', args=[_id]))
    reason = (request.POST.get('reason') or '').strip()
    with transaction.atomic():
        doc = StockDocument.objects.select_for_update().get(pk=_id)
        if doc.status != 'submitted':
            return _render_receipt_view(request, doc, error='Hanya dokumen Submitted yang dapat ditolak.')
        if not reason:
            return _render_receipt_view(request, doc, error='Alasan penolakan wajib diisi.')
        doc.status = 'draft'
        doc.reject_reason = reason
        doc.submitted_by = None
        doc.save()
    return HttpResponseRedirect(reverse('receipt-view', args=[_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='RCV')
def receipt_cancel(request, _id):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('receipt-view', args=[_id]))
    reason = (request.POST.get('reason') or '').strip()
    with transaction.atomic():
        doc = StockDocument.objects.select_for_update().get(pk=_id)
        if doc.status != 'draft':
            return _render_receipt_view(request, doc, error='Hanya dokumen Draft yang dapat dibatalkan.')
        if not reason:
            return _render_receipt_view(request, doc, error='Alasan pembatalan wajib diisi.')
        doc.status = 'cancelled'
        doc.cancel_reason = reason
        doc.save()
    return HttpResponseRedirect(reverse('receipt-view', args=[_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='RCV')
def receipt_post(request, _id):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('receipt-view', args=[_id]))
    try:
        _post_receipt(_id, request.user.user_id)
    except ValueError as e:
        doc = StockDocument.objects.get(pk=_id)
        return _render_receipt_view(request, doc, error=str(e))
    return HttpResponseRedirect(reverse('receipt-view', args=[_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='RCV')
def receipt_validate(request, _id):
    """Validasi penerimaan fisik (US-RCV-02): diterima / layak / ditolak."""
    doc = get_object_or_404(StockDocument.objects.select_related(
        'warehouse', 'receiving_location'), pk=_id)
    if doc.status != 'approved':
        return HttpResponseRedirect(reverse('receipt-view', args=[_id]))
    lines = list(doc.lines.select_related(
        'item', 'destination_location', 'quarantine_location'))
    quarantine_locations = StorageLocation.objects.filter(
        is_active=True, warehouse=doc.warehouse, location_type='quarantine')
    errors = []

    if request.POST:
        received_l = request.POST.getlist('v_received')
        accepted_l = request.POST.getlist('v_accepted')
        rejected_l = request.POST.getlist('v_rejected')
        quar_l = request.POST.getlist('v_quarantine')

        def dec(raw):
            raw = (raw or '').strip().replace(',', '')
            return Decimal(raw) if raw else Decimal('0')

        parsed = []
        for i, line in enumerate(lines):
            try:
                received = dec(received_l[i] if i < len(received_l) else '')
                accepted = dec(accepted_l[i] if i < len(accepted_l) else '')
                rejected = dec(rejected_l[i] if i < len(rejected_l) else '')
            except Exception:
                errors.append('Baris %d: kuantitas tidak valid.' % (i + 1))
                continue
            if min(received, accepted, rejected) < 0:
                errors.append('Baris %d: kuantitas tidak boleh negatif.' % (i + 1))
                continue
            if any(v != v.to_integral_value() for v in (received, accepted, rejected)):
                errors.append('Baris %d: kuantitas harus bilangan bulat.' % (i + 1))
                continue
            if accepted + rejected != received:
                errors.append(
                    'Baris %d: (diterima layak + ditolak) harus sama dengan '
                    'total diterima fisik.' % (i + 1))
                continue
            quar = None
            if rejected > 0:
                try:
                    quar = StorageLocation.objects.get(
                        pk=int(quar_l[i] if i < len(quar_l) else ''),
                        warehouse=doc.warehouse, is_active=True)
                except (StorageLocation.DoesNotExist, ValueError, TypeError):
                    errors.append(
                        'Baris %d: lokasi karantina wajib dipilih untuk '
                        'barang ditolak.' % (i + 1))
                    continue
            parsed.append((line, received, accepted, rejected, quar))

        if not errors:
            now = timezone.now()
            with transaction.atomic():
                doc_locked = StockDocument.objects.select_for_update().get(pk=doc.pk)
                if doc_locked.status != 'approved':
                    errors.append('Status dokumen berubah, silakan muat ulang.')
                else:
                    for line, received, accepted, rejected, quar in parsed:
                        line.received_qty = received
                        line.accepted_qty = accepted
                        line.rejected_qty = rejected
                        line.quarantine_location = quar
                        line.validated_by = request.user.user_id
                        line.validated_at = now
                        line.save()
                    doc_locked.receive_status = 'done'
                    doc_locked.validated_by = request.user.user_id
                    doc_locked.validated_at = now
                    doc_locked.save()
            if not errors:
                return HttpResponseRedirect(reverse('receipt-view', args=[doc.pk]))

    ctx = _rctx(request, 'validate', data=doc, lines=lines,
                quarantine_locations=quarantine_locations)
    if errors:
        ctx['message'] = errors
    return render(request, 'home/receipt_validate.html', ctx)


@login_required(login_url='/login/')
@role_required(allowed_roles='RCV')
def receipt_putaway(request, _id):
    """Putaway 2 tahap (US-RCV-03): pindah receiving -> lokasi penyimpanan."""
    doc = get_object_or_404(StockDocument.objects.select_related(
        'warehouse', 'receiving_location'), pk=_id)
    if doc.operation_type != 'staged' or doc.status != 'posted':
        return HttpResponseRedirect(reverse('receipt-view', args=[_id]))
    lines = [l for l in doc.lines.select_related(
        'item', 'destination_location') if l.putaway_remaining > 0]
    if not lines:
        return HttpResponseRedirect(reverse('receipt-view', args=[_id]))
    errors = []

    if request.POST:
        qty_l = request.POST.getlist('p_qty')

        def dec(raw):
            raw = (raw or '').strip().replace(',', '')
            return Decimal(raw) if raw else Decimal('0')

        parsed = []
        for i, line in enumerate(lines):
            try:
                qty = dec(qty_l[i] if i < len(qty_l) else '')
            except Exception:
                errors.append('Baris %d: kuantitas tidak valid.' % (i + 1))
                continue
            if qty < 0:
                errors.append('Baris %d: kuantitas tidak boleh negatif.' % (i + 1))
                continue
            if qty != qty.to_integral_value():
                errors.append('Baris %d: kuantitas harus bilangan bulat.' % (i + 1))
                continue
            if qty > line.putaway_remaining:
                errors.append(
                    'Baris %d: melebihi sisa putaway (%s).' % (i + 1, line.putaway_remaining))
                continue
            parsed.append((line, qty))

        if not errors and not any(q > 0 for _, q in parsed):
            errors.append('Minimal 1 baris harus memiliki kuantitas putaway.')

        if not errors:
            try:
                with transaction.atomic():
                    doc_locked = StockDocument.objects.select_for_update().get(pk=doc.pk)
                    if doc_locked.status != 'posted' or \
                            doc_locked.operation_type != 'staged':
                        raise ValueError('Status dokumen berubah, silakan muat ulang.')
                    if not doc_locked.receiving_location:
                        raise ValueError('Dokumen tidak memiliki lokasi receiving.')
                    # Kunci & verifikasi ulang semua baris sebelum mutasi apa pun
                    fresh = []
                    for line, qty in parsed:
                        if qty == 0:
                            continue
                        lf = StockDocumentLine.objects.select_for_update().get(pk=line.pk)
                        if qty > lf.putaway_remaining:
                            raise ValueError(
                                'Baris %s: sisa putaway berubah menjadi %s.'
                                % (lf.item.sku, lf.putaway_remaining))
                        fresh.append((lf, qty))
                    now = timezone.now()
                    for lf, qty in fresh:
                        bal_recv = _balance_locked(
                            doc_locked.receiving_location, lf.item)
                        if (bal_recv.on_hand or Decimal('0')) < qty:
                            raise ValueError(
                                'Stok di lokasi receiving tidak mencukupi '
                                'untuk %s.' % lf.item.sku)
                        _apply_ledger(
                            doc_locked.warehouse, doc_locked.receiving_location,
                            lf.item, qty, 'OUT', doc_locked.number,
                            'Putaway dari receiving (%s)' % lf.item.sku,
                            request.user.user_id)
                        _apply_ledger(
                            doc_locked.warehouse, lf.destination_location,
                            lf.item, qty, 'IN', doc_locked.number,
                            'Putaway ke %s (%s)' % (
                                lf.destination_location.code, lf.item.sku),
                            request.user.user_id)
                        lf.putaway_qty = (lf.putaway_qty or Decimal('0')) + qty
                        lf.putaway_by = request.user.user_id
                        lf.putaway_at = now
                        if lf.putaway_remaining <= 0:
                            lf.putaway_status = 'done'
                        lf.save()
                    if not doc_locked.putaway_pending_lines:
                        doc_locked.putaway_status = 'done'
                        doc_locked.save()
            except ValueError as e:
                errors.append(str(e))
            if not errors:
                return HttpResponseRedirect(reverse('receipt-view', args=[doc.pk]))

    ctx = _rctx(request, 'putaway', data=doc, lines=lines)
    if errors:
        ctx['message'] = errors
    return render(request, 'home/receipt_putaway.html', ctx)
