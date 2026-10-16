from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from crum import get_current_user


def _current_username():
    """Username aktif pada request berjalan (None bila bukan dari request)."""
    user = get_current_user()
    return user.user_id if user else 'system'


class User(AbstractUser):
    is_active = models.BooleanField(default=True)
    user_id = models.CharField(max_length=50, primary_key=True)
    username = models.CharField(max_length=50)
    position = models.ForeignKey(
        'Position', on_delete=models.CASCADE, null=True)
    signature = models.ImageField(upload_to='signature/', null=True)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True)
    update_by = models.CharField(max_length=50, null=True)

    def save(self, *args, **kwargs):
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = _current_username()
        self.update_date = timezone.now()
        self.update_by = _current_username()
        super(User, self).save(*args, **kwargs)

    USERNAME_FIELD = 'user_id'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username


class Position(models.Model):
    position_id = models.CharField(
        max_length=3, primary_key=True, help_text='Max 3 digits Position shortname.')
    position_name = models.CharField(max_length=50)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True)
    update_by = models.CharField(max_length=50, null=True)

    def save(self, *args, **kwargs):
        self.position_id = self.position_id.upper()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = _current_username()
        self.update_date = timezone.now()
        self.update_by = _current_username()
        super(Position, self).save(*args, **kwargs)

    def __str__(self):
        return self.position_name


class Menu(models.Model):
    menu_id = models.CharField(max_length=50, primary_key=True)
    menu_name = models.CharField(max_length=50)
    menu_remark = models.CharField(max_length=200, null=True, blank=True)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True)
    update_by = models.CharField(max_length=50, null=True)

    def save(self, *args, **kwargs):
        self.menu_id = self.menu_id.upper()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = _current_username()
        self.update_date = timezone.now()
        self.update_by = _current_username()
        super(Menu, self).save(*args, **kwargs)

    def __str__(self):
        return self.menu_name


class Auth(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    add = models.BooleanField(default=False)
    edit = models.BooleanField(default=False)
    delete = models.BooleanField(default=False)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True)
    update_by = models.CharField(max_length=50, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'menu'], name='unique_user_menu')
        ]

    def save(self, *args, **kwargs):
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = _current_username()
        self.update_date = timezone.now()
        self.update_by = _current_username()
        super(Auth, self).save(*args, **kwargs)

    def __str__(self):
        return self.menu.menu_name


# ==================================================================
# Master Data Pergudangan — TSP Warehouse (Fase 1)
# ==================================================================
class Unit(models.Model):
    """Satuan dasar barang (PCS, KG, BOX, ...)."""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True)
    update_by = models.CharField(max_length=50, null=True)

    class Meta:
        verbose_name = 'Satuan'
        verbose_name_plural = 'Satuan'

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = _current_username()
        self.update_date = timezone.now()
        self.update_by = _current_username()
        super(Unit, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class ItemCategory(models.Model):
    """Kategori barang."""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True)
    update_by = models.CharField(max_length=50, null=True)

    class Meta:
        verbose_name = 'Kategori Barang'
        verbose_name_plural = 'Kategori Barang'

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = _current_username()
        self.update_date = timezone.now()
        self.update_by = _current_username()
        super(ItemCategory, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Partner(models.Model):
    """Supplier / Pelanggan (mitra)."""
    TYPE_CHOICES = [
        ('SUPPLIER', 'Supplier'),
        ('CUSTOMER', 'Pelanggan'),
        ('BOTH', 'Keduanya'),
    ]
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=150)
    partner_type = models.CharField(
        max_length=10, choices=TYPE_CHOICES, default='SUPPLIER')
    address = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=30, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True)
    update_by = models.CharField(max_length=50, null=True)

    class Meta:
        verbose_name = 'Mitra'
        verbose_name_plural = 'Mitra'

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = _current_username()
        self.update_date = timezone.now()
        self.update_by = _current_username()
        super(Partner, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    """Gudang."""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255, null=True, blank=True)
    manager = models.CharField(
        max_length=100, null=True, blank=True, help_text='Penanggung jawab gudang.')
    is_active = models.BooleanField(default=True)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True)
    update_by = models.CharField(max_length=50, null=True)

    class Meta:
        verbose_name = 'Gudang'
        verbose_name_plural = 'Gudang'

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = _current_username()
        self.update_date = timezone.now()
        self.update_by = _current_username()
        super(Warehouse, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class StorageLocation(models.Model):
    """Lokasi penyimpanan dalam gudang (Gudang > Zona > Rak > Bin)."""
    TYPE_CHOICES = [
        ('storage', 'Storage'),
        ('receiving', 'Receiving'),
        ('staging', 'Staging'),
        ('packing', 'Packing'),
        ('dispatch', 'Dispatch'),
        ('quarantine', 'Quarantine'),
    ]
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name='locations')
    parent = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, blank=True, related_name='children')
    code = models.CharField(max_length=60)
    name = models.CharField(max_length=150)
    barcode = models.CharField(
        max_length=100, unique=True, null=True, blank=True)
    location_type = models.CharField(
        max_length=12, choices=TYPE_CHOICES, default='storage')
    is_active = models.BooleanField(default=True)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True)
    update_by = models.CharField(max_length=50, null=True)

    class Meta:
        verbose_name = 'Lokasi'
        verbose_name_plural = 'Lokasi'
        constraints = [
            models.UniqueConstraint(
                fields=['warehouse', 'code'], name='unique_location_per_warehouse')
        ]

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = _current_username()
        self.update_date = timezone.now()
        self.update_by = _current_username()
        super(StorageLocation, self).save(*args, **kwargs)

    def __str__(self):
        return '%s — %s' % (self.warehouse.code, self.code)


class Item(models.Model):
    """Barang / SKU."""
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    barcode = models.CharField(
        max_length=100, unique=True, null=True, blank=True)
    category = models.ForeignKey(
        ItemCategory, on_delete=models.PROTECT, related_name='items')
    uom = models.ForeignKey(
        Unit, on_delete=models.PROTECT, related_name='items')
    minimum_stock = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    is_active = models.BooleanField(default=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True)
    update_by = models.CharField(max_length=50, null=True)

    class Meta:
        verbose_name = 'Barang'
        verbose_name_plural = 'Barang'

    def save(self, *args, **kwargs):
        self.sku = self.sku.upper()
        if self.barcode:
            self.barcode = self.barcode.strip()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = _current_username()
        self.update_date = timezone.now()
        self.update_by = _current_username()
        super(Item, self).save(*args, **kwargs)

    def __str__(self):
        return '%s — %s' % (self.sku, self.name)


# ==================================================================
# Fondasi Persediaan — Ledger & Saldo (Fase 1)
# ==================================================================
class StockLedger(models.Model):
    """Buku besar mutasi stok (append-only). Sumber kebenaran saldo."""
    MOVE_CHOICES = [('IN', 'Masuk'), ('OUT', 'Keluar')]
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='ledger')
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name='ledger')
    location = models.ForeignKey(
        StorageLocation, on_delete=models.PROTECT, related_name='ledger')
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    move_type = models.CharField(max_length=3, choices=MOVE_CHOICES)
    reference = models.CharField(
        max_length=50, null=True, blank=True, help_text='Nomor dokumen sumber.')
    notes = models.CharField(max_length=255, null=True, blank=True)
    actor = models.CharField(max_length=50)
    posted_at = models.DateTimeField()

    class Meta:
        verbose_name = 'Ledger Stok'
        verbose_name_plural = 'Ledger Stok'
        ordering = ['-posted_at', '-id']
        indexes = [
            models.Index(fields=['item', 'location']),
            models.Index(fields=['posted_at']),
        ]

    def __str__(self):
        return '%s %s @%s' % (self.move_type, self.quantity, self.location.code)


class StockBalance(models.Model):
    """Cache materialisasi saldo stok per item+lokasi."""
    item = models.ForeignKey(
        Item, on_delete=models.PROTECT, related_name='balances')
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name='balances')
    location = models.ForeignKey(
        StorageLocation, on_delete=models.PROTECT, related_name='balances')
    on_hand = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    reserved = models.DecimalField(max_digits=18, decimal_places=4, default=0)

    class Meta:
        verbose_name = 'Saldo Stok'
        verbose_name_plural = 'Saldo Stok'
        constraints = [
            models.UniqueConstraint(
                fields=['item', 'location'], name='unique_balance_item_location')
        ]

    @property
    def available(self):
        return self.on_hand - self.reserved

    def __str__(self):
        return '%s @%s = %s' % (self.item.sku, self.location.code, self.on_hand)
