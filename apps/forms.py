from django import forms
from django.forms import ModelForm
from decimal import Decimal
from apps.models import *
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm, UserCreationForm


class TrimDecimalInput(forms.NumberInput):
    """Input angka yang menampilkan nilai tanpa nol desimal di belakang.

    5.0000 -> '5', 7.5000 -> '7.5' (hanya tampilan; input tetap menerima desimal).
    """

    def format_value(self, value):
        if value in (None, ''):
            return ''
        try:
            d = Decimal(str(value))
        except Exception:
            return super(TrimDecimalInput, self).format_value(value)
        if d == d.to_integral_value():
            d = d.quantize(Decimal('1'))
        else:
            d = d.normalize()
        return format(d, 'f')


class FormUser(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(FormUser, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['user_id'].label = 'User ID'
        self.fields['username'].label = 'Nama User'
        self.fields['email'].label = 'Email'
        self.fields['position'].label = 'Posisi'
        self.fields['signature'].label = 'Tanda Tangan'
        self.fields['signature'].required = False
        self.fields['password1'].label = 'Password'
        self.fields['password2'].label = 'Konfirmasi Password'
        self.fields['user_id'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['username'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['email'].widget = forms.EmailInput(
            {'class': 'form-control-sm'})
        self.fields['password1'].widget = forms.PasswordInput(
            {'class': 'form-control-sm'})
        self.fields['password2'].widget = forms.PasswordInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = User
        exclude = ['date_joined', 'password', 'is_active', 'is_staff',
                   'is_superuser', 'entry_date', 'entry_by', 'update_date', 'update_by']
        widgets = {
            'signature': forms.FileInput(attrs={'class': 'form-control form-control-sm'}),
        }


class FormUserView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormUserView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['username'].label = 'Nama User'
        self.fields['email'].label = 'Email'
        self.fields['position'].label = 'Posisi'
        self.fields['username'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['email'].widget = forms.EmailInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = User
        fields = ['user_id', 'username', 'email', 'position', 'signature']

        widgets = {
            'position': forms.Select(attrs={'class': 'form-control form-select-sm', 'disabled': 'disabled'}),
            'signature': forms.FileInput(attrs={'class': 'form-control form-control-sm', 'disabled': 'disabled'}),
        }


class FormUserUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormUserUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['username'].label = 'Nama User'
        self.fields['email'].label = 'Email'
        self.fields['position'].label = 'Posisi'
        self.fields['username'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['email'].widget = forms.EmailInput(
            {'class': 'form-control-sm'})
        self.fields['signature'].required = False

    class Meta:
        model = User
        exclude = ['user_id', 'password', 'date_joined',
                   'is_active', 'is_staff', 'is_superuser', 'entry_date', 'entry_by', 'update_date', 'update_by']

        widgets = {
            'position': forms.Select(attrs={'class': 'form-control form-select-sm'}),
            'signature': forms.FileInput(attrs={'class': 'form-control form-control-sm'}),
        }


class FormChangePassword(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(FormChangePassword, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['old_password'].label = 'Password Lama'
        self.fields['new_password1'].label = 'Password Baru'
        self.fields['new_password2'].label = 'Konfirmasi Password Baru'
        self.fields['old_password'].widget = forms.PasswordInput(
            {'class': 'form-control-sm z-index-2'})
        self.fields['new_password1'].widget = forms.PasswordInput(
            {'class': 'form-control-sm z-index-2'})
        self.fields['new_password2'].widget = forms.PasswordInput(
            {'class': 'form-control-sm z-index-2'})


class FormSetPassword(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super(FormSetPassword, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['new_password1'].label = 'Password Baru'
        self.fields['new_password2'].label = 'Konfirmasi Password Baru'
        self.fields['new_password1'].widget = forms.PasswordInput(
            {'class': 'form-control-sm'})
        self.fields['new_password2'].widget = forms.PasswordInput(
            {'class': 'form-control-sm'})


class FormPosition(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormPosition, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['position_id'].label = 'ID Posisi'
        self.fields['position_name'].label = 'Nama Posisi'
        self.fields['position_id'].widget = forms.TextInput(
            {'class': 'form-control-sm text-uppercase', 'placeholder': 'XXX'})
        self.fields['position_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Position
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormPositionUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormPositionUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['position_name'].label = 'Nama Posisi'
        self.fields['position_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Position
        exclude = ['position_id', 'entry_date',
                   'entry_by', 'update_date', 'update_by']


class FormPositionView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormPositionView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['position_name'].label = 'Nama Posisi'
        self.fields['position_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = Position
        fields = ['position_id', 'position_name']


class FormMenu(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormMenu, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['menu_id'].label = 'ID Menu'
        self.fields['menu_name'].label = 'Nama Menu'
        self.fields['menu_remark'].label = 'Deskripsi'
        self.fields['menu_id'].widget = forms.TextInput(
            {'class': 'form-control-sm text-uppercase'})
        self.fields['menu_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['menu_remark'].widget = forms.Textarea(
            {'class': 'form-control-sm', 'rows': 3})

    class Meta:
        model = Menu
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormMenuUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormMenuUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['menu_name'].label = 'Nama Menu'
        self.fields['menu_remark'].label = 'Deskripsi'
        self.fields['menu_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['menu_remark'].widget = forms.Textarea(
            {'class': 'form-control-sm', 'rows': 3})

    class Meta:
        model = Menu
        exclude = ['menu_id', 'entry_date',
                   'entry_by', 'update_date', 'update_by']


class FormMenuView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormMenuView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['menu_name'].label = 'Nama Menu'
        self.fields['menu_remark'].label = 'Deskripsi'
        self.fields['menu_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['menu_remark'].widget = forms.Textarea(
            {'class': 'form-control-sm', 'rows': 3, 'readonly': 'readonly'})

    class Meta:
        model = Menu
        fields = ['menu_id', 'menu_name', 'menu_remark']


class FormAuthUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormAuthUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['add'].widget = forms.CheckboxInput(
            {'class': 'border mt-1'})
        self.fields['edit'].widget = forms.CheckboxInput(
            {'class': 'border mt-1'})
        self.fields['delete'].widget = forms.CheckboxInput(
            {'class': 'border mt-1'})

    class Meta:
        model = Auth
        exclude = ['user', 'entry_date',
                   'entry_by', 'update_date', 'update_by']


# ==================================================================
# Master Data Pergudangan — Forms (Fase 1)
# ==================================================================
class FormUnit(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormUnit, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['code'].label = 'Kode Satuan'
        self.fields['name'].label = 'Nama Satuan'
        self.fields['code'].widget = forms.TextInput(
            {'class': 'form-control-sm text-uppercase', 'placeholder': 'PCS'})
        self.fields['name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Unit
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormUnitView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormUnitView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['code'].label = 'Kode Satuan'
        self.fields['name'].label = 'Nama Satuan'
        self.fields['code'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = Unit
        fields = ['code', 'name']


class FormCategory(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormCategory, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['code'].label = 'Kode Kategori'
        self.fields['name'].label = 'Nama Kategori'
        self.fields['code'].widget = forms.TextInput(
            {'class': 'form-control-sm text-uppercase'})
        self.fields['name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = ItemCategory
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormCategoryView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormCategoryView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['code'].label = 'Kode Kategori'
        self.fields['name'].label = 'Nama Kategori'
        self.fields['code'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = ItemCategory
        fields = ['code', 'name']


class FormPartner(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormPartner, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['code'].label = 'Kode Mitra'
        self.fields['name'].label = 'Nama Mitra'
        self.fields['partner_type'].label = 'Jenis'
        self.fields['address'].label = 'Alamat'
        self.fields['phone'].label = 'Telepon'
        self.fields['email'].label = 'Email'
        self.fields['is_active'].label = 'Aktif'
        self.fields['code'].widget = forms.TextInput(
            {'class': 'form-control-sm text-uppercase'})
        self.fields['name'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['partner_type'].widget = forms.Select(
            {'class': 'form-control form-select-sm'})
        self.fields['address'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['phone'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['email'].widget = forms.EmailInput({'class': 'form-control-sm'})
        self.fields['is_active'].widget = forms.CheckboxInput({'class': 'border mt-1'})

    class Meta:
        model = Partner
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormPartnerView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormPartnerView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['code'].label = 'Kode Mitra'
        self.fields['name'].label = 'Nama Mitra'
        self.fields['partner_type'].label = 'Jenis'
        self.fields['address'].label = 'Alamat'
        self.fields['phone'].label = 'Telepon'
        self.fields['email'].label = 'Email'
        self.fields['is_active'].label = 'Aktif'
        for f in ['code', 'name', 'address', 'phone', 'email']:
            self.fields[f].widget = forms.TextInput(
                {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['partner_type'].widget = forms.Select(
            {'class': 'form-control form-select-sm', 'disabled': 'disabled'})
        self.fields['is_active'].widget = forms.CheckboxInput(
            {'class': 'border mt-1', 'disabled': 'disabled'})

    class Meta:
        model = Partner
        fields = ['code', 'name', 'partner_type', 'address',
                  'phone', 'email', 'is_active']


class FormWarehouse(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormWarehouse, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['code'].label = 'Kode Gudang'
        self.fields['name'].label = 'Nama Gudang'
        self.fields['address'].label = 'Alamat'
        self.fields['manager'].label = 'Penanggung Jawab'
        self.fields['is_active'].label = 'Aktif'
        self.fields['code'].widget = forms.TextInput(
            {'class': 'form-control-sm text-uppercase'})
        self.fields['name'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['address'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['manager'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['is_active'].widget = forms.CheckboxInput({'class': 'border mt-1'})

    class Meta:
        model = Warehouse
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormWarehouseView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormWarehouseView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['code'].label = 'Kode Gudang'
        self.fields['name'].label = 'Nama Gudang'
        self.fields['address'].label = 'Alamat'
        self.fields['manager'].label = 'Penanggung Jawab'
        self.fields['is_active'].label = 'Aktif'
        for f in ['code', 'name', 'address', 'manager']:
            self.fields[f].widget = forms.TextInput(
                {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['is_active'].widget = forms.CheckboxInput(
            {'class': 'border mt-1', 'disabled': 'disabled'})

    class Meta:
        model = Warehouse
        fields = ['code', 'name', 'address', 'manager', 'is_active']


class FormLocation(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormLocation, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['warehouse'].label = 'Gudang'
        self.fields['parent'].label = 'Induk (Parent)'
        self.fields['code'].label = 'Kode Lokasi'
        self.fields['name'].label = 'Nama Lokasi'
        self.fields['barcode'].label = 'Barcode'
        self.fields['location_type'].label = 'Tipe Lokasi'
        self.fields['is_active'].label = 'Aktif'
        self.fields['warehouse'].widget = forms.Select(
            {'class': 'form-control form-select-sm'})
        self.fields['parent'].widget = forms.Select(
            {'class': 'form-control form-select-sm'})
        self.fields['code'].widget = forms.TextInput(
            {'class': 'form-control-sm text-uppercase'})
        self.fields['name'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['barcode'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['location_type'].widget = forms.Select(
            {'class': 'form-control form-select-sm'})
        self.fields['is_active'].widget = forms.CheckboxInput({'class': 'border mt-1'})

    class Meta:
        model = StorageLocation
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormLocationView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormLocationView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['warehouse'].label = 'Gudang'
        self.fields['parent'].label = 'Induk (Parent)'
        self.fields['code'].label = 'Kode Lokasi'
        self.fields['name'].label = 'Nama Lokasi'
        self.fields['barcode'].label = 'Barcode'
        self.fields['location_type'].label = 'Tipe Lokasi'
        self.fields['is_active'].label = 'Aktif'
        self.fields['warehouse'].widget = forms.Select(
            {'class': 'form-control form-select-sm', 'disabled': 'disabled'})
        self.fields['parent'].widget = forms.Select(
            {'class': 'form-control form-select-sm', 'disabled': 'disabled'})
        for f in ['code', 'name', 'barcode']:
            self.fields[f].widget = forms.TextInput(
                {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['location_type'].widget = forms.Select(
            {'class': 'form-control form-select-sm', 'disabled': 'disabled'})
        self.fields['is_active'].widget = forms.CheckboxInput(
            {'class': 'border mt-1', 'disabled': 'disabled'})

    class Meta:
        model = StorageLocation
        fields = ['warehouse', 'parent', 'code', 'name',
                  'barcode', 'location_type', 'is_active']


class FormItem(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormItem, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['sku'].label = 'SKU'
        self.fields['name'].label = 'Nama Barang'
        self.fields['barcode'].label = 'Barcode'
        self.fields['category'].label = 'Kategori'
        self.fields['uom'].label = 'Satuan'
        self.fields['minimum_stock'].label = 'Stok Minimum'
        self.fields['is_active'].label = 'Aktif'
        self.fields['description'].label = 'Deskripsi'
        self.fields['sku'].widget = forms.TextInput(
            {'class': 'form-control-sm text-uppercase'})
        self.fields['name'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['barcode'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['category'].widget = forms.Select(
            {'class': 'form-control form-select-sm'})
        self.fields['uom'].widget = forms.Select(
            {'class': 'form-control form-select-sm'})
        self.fields['minimum_stock'].widget = TrimDecimalInput(
            {'class': 'form-control-sm', 'step': '0.0001', 'min': '0'})
        self.fields['is_active'].widget = forms.CheckboxInput({'class': 'border mt-1'})
        self.fields['description'].widget = forms.TextInput({'class': 'form-control-sm'})

    class Meta:
        model = Item
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormItemView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormItemView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['sku'].label = 'SKU'
        self.fields['name'].label = 'Nama Barang'
        self.fields['barcode'].label = 'Barcode'
        self.fields['category'].label = 'Kategori'
        self.fields['uom'].label = 'Satuan'
        self.fields['minimum_stock'].label = 'Stok Minimum'
        self.fields['is_active'].label = 'Aktif'
        self.fields['description'].label = 'Deskripsi'
        for f in ['sku', 'name', 'barcode', 'description']:
            self.fields[f].widget = forms.TextInput(
                {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['category'].widget = forms.Select(
            {'class': 'form-control form-select-sm', 'disabled': 'disabled'})
        self.fields['uom'].widget = forms.Select(
            {'class': 'form-control form-select-sm', 'disabled': 'disabled'})
        self.fields['minimum_stock'].widget = TrimDecimalInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['is_active'].widget = forms.CheckboxInput(
            {'class': 'border mt-1', 'disabled': 'disabled'})

    class Meta:
        model = Item
        fields = ['sku', 'name', 'barcode', 'category', 'uom',
                  'minimum_stock', 'is_active', 'description']


# ==================================================================
# Transaksi Gudang — Penerimaan Barang (Fase 2)
# ==================================================================
class FormReceipt(ModelForm):
    """Header dokumen penerimaan. Baris detail ditangani terpisah (array POST)."""

    def __init__(self, *args, **kwargs):
        super(FormReceipt, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['warehouse'].label = 'Gudang'
        self.fields['partner'].label = 'Supplier'
        self.fields['reference'].label = 'Referensi (No. PO)'
        self.fields['document_date'].label = 'Tanggal Dokumen'
        self.fields['notes'].label = 'Catatan'
        self.fields['operation_type'].label = 'Skema Penerimaan'
        self.fields['receiving_location'].label = 'Lokasi Receiving'
        self.fields['warehouse'].widget = forms.Select(
            {'class': 'form-control form-select-sm'})
        self.fields['partner'].widget = forms.Select(
            {'class': 'form-control form-select-sm'})
        self.fields['partner'].required = False
        self.fields['reference'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['document_date'].widget = forms.DateInput(
            {'class': 'form-control-sm', 'type': 'date'})
        self.fields['notes'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['operation_type'].widget = forms.Select(
            {'class': 'form-control form-select-sm', 'id': 'id_operation_type'})
        self.fields['receiving_location'].widget = forms.Select(
            {'class': 'form-control form-select-sm', 'id': 'id_receiving_location'})
        self.fields['receiving_location'].required = False

    def clean(self):
        cleaned = super(FormReceipt, self).clean()
        operation_type = cleaned.get('operation_type')
        receiving_location = cleaned.get('receiving_location')
        warehouse = cleaned.get('warehouse')
        if operation_type == 'staged':
            if not receiving_location:
                self.add_error(
                    'receiving_location',
                    'Lokasi receiving wajib diisi untuk skema 2 tahap.')
            elif warehouse and receiving_location.warehouse_id != warehouse.pk:
                self.add_error(
                    'receiving_location',
                    'Lokasi receiving harus berada di gudang yang sama '
                    'dengan dokumen.')
        elif receiving_location and warehouse and \
                receiving_location.warehouse_id != warehouse.pk:
            self.add_error(
                'receiving_location',
                'Lokasi receiving harus berada di gudang yang sama '
                'dengan dokumen.')
        return cleaned

    class Meta:
        model = StockDocument
        fields = ['warehouse', 'partner', 'reference', 'document_date',
                  'operation_type', 'receiving_location', 'notes']
