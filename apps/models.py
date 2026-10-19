from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from decimal import Decimal
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


# ==================================================================
# Transaksi Gudang — Penerimaan Barang (Fase 2)
# ==================================================================
class DocumentSequence(models.Model):
    """Penomoran dokumen otomatis & unik per tipe/tahun (locked allocation)."""
    document_type = models.CharField(max_length=10)
    year = models.IntegerField()
    next_number = models.IntegerField(default=1)

    class Meta:
        verbose_name = 'Sequence Dokumen'
        verbose_name_plural = 'Sequence Dokumen'
        constraints = [
            models.UniqueConstraint(
                fields=['document_type', 'year'], name='unique_seq_type_year')
        ]

    @classmethod
    def next_number_for(cls, document_type):
        from django.db import transaction
        year = timezone.now().year
        with transaction.atomic():
            seq, _ = cls.objects.select_for_update().get_or_create(
                document_type=document_type, year=year,
                defaults={'next_number': 1})
            current = seq.next_number
            seq.next_number = current + 1
            seq.save(update_fields=['next_number'])
        return '%s/%d/%06d' % (document_type, year, current)


class StockDocument(models.Model):
    """Dokumen transaksi stok (untuk sekarang: penerimaan RCV)."""
    TYPE_CHOICES = [
        ('RCV', 'Penerimaan Barang'),
        # ('OUT', 'Pengeluaran Barang'),   # fase berikutnya
        # ('TRF', 'Transfer Stok'),
        # ('ADJ', 'Penyesuaian Stok'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ]
    document_type = models.CharField(
        max_length=3, choices=TYPE_CHOICES, default='RCV')
    number = models.CharField(max_length=30, unique=True)
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name='documents')
    partner = models.ForeignKey(
        Partner, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='documents')
    reference = models.CharField(max_length=50, null=True, blank=True)
    document_date = models.DateField()
    notes = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=12, choices=STATUS_CHOICES, default='draft')
    # --- 2 tahap (Fase 2b) ---
    operation_type = models.CharField(
        max_length=8, choices=[
            ('direct', '1 Tahap — langsung ke lokasi penyimpanan'),
            ('staged', '2 Tahap — receiving lalu putaway'),
        ], default='direct')
    receiving_location = models.ForeignKey(
        StorageLocation, on_delete=models.PROTECT, null=True, blank=True,
        related_name='+',
        help_text='Lokasi receiving (wajib untuk skema 2 tahap).')
    receive_status = models.CharField(
        max_length=12, choices=[
            ('pending', 'Menunggu validasi'),
            ('done', 'Tervalidasi'),
        ], default='pending')
    validated_by = models.CharField(max_length=50, null=True, blank=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    putaway_status = models.CharField(
        max_length=12, choices=[
            ('none', 'Tidak perlu putaway'),
            ('pending', 'Menunggu putaway'),
            ('done', 'Putaway selesai'),
        ], default='none')
    created_by = models.CharField(max_length=50)
    submitted_by = models.CharField(max_length=50, null=True, blank=True)
    approved_by = models.CharField(max_length=50, null=True, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    reject_reason = models.CharField(max_length=255, null=True, blank=True)
    cancel_reason = models.CharField(max_length=255, null=True, blank=True)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True)
    update_by = models.CharField(max_length=50, null=True)

    class Meta:
        verbose_name = 'Dokumen Stok'
        verbose_name_plural = 'Dokumen Stok'
        ordering = ['-document_date', '-id']
        indexes = [
            models.Index(fields=['document_type', 'status']),
            models.Index(fields=['document_date']),
        ]

    def save(self, *args, **kwargs):
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = _current_username()
        self.update_date = timezone.now()
        self.update_by = _current_username()
        super(StockDocument, self).save(*args, **kwargs)

    @property
    def total_quantity(self):
        return sum((l.quantity for l in self.lines.all()), Decimal('0'))

    @property
    def total_received(self):
        return sum((l.received_qty or Decimal('0')
                    for l in self.lines.all()), Decimal('0'))

    @property
    def total_accepted(self):
        return sum((l.accepted_qty or Decimal('0')
                    for l in self.lines.all()), Decimal('0'))

    @property
    def total_rejected(self):
        return sum((l.rejected_qty or Decimal('0')
                    for l in self.lines.all()), Decimal('0'))

    @property
    def scan_state(self):
        """Status operasional petugas scan (Daftar Penerimaan & Dashboard).

        pending_approval = draft/submitted — menunggu persetujuan
        await_validation = approved — menunggu validasi (scan validasi)
        validated        = sudah divalidasi, menunggu posting
        putaway          = menunggu putaway (scan putaway)
        done             = selesai
        cancelled        = dibatalkan
        """
        if self.status in ('cancelled', 'rejected'):
            return 'cancelled'
        if self.putaway_status == 'pending':
            return 'putaway'
        if self.status == 'approved':
            return ('validated' if self.receive_status == 'done'
                    else 'await_validation')
        if self.status == 'posted':
            return 'done'
        return 'pending_approval'

    # Nama & warna badge status — SATU sumber untuk semua halaman
    SCAN_STATE_LABELS = {
        'pending_approval': ('Menunggu Persetujuan', 'bg-gradient-secondary'),
        'await_validation': ('Menunggu Validasi', 'bg-gradient-primary'),
        'validated': ('Sudah Divalidasi', 'bg-gradient-info'),
        'putaway': ('Putaway Pending', 'bg-gradient-warning'),
        'done': ('Selesai', 'bg-gradient-success'),
        'cancelled': ('Dibatalkan', 'bg-gradient-danger'),
    }

    @property
    def scan_state_label(self):
        return self.SCAN_STATE_LABELS[self.scan_state][0]

    @property
    def scan_state_css(self):
        return self.SCAN_STATE_LABELS[self.scan_state][1]

    @property
    def putaway_pending_lines(self):
        """Baris staged yang masih punya sisa putaway."""
        return [l for l in self.lines.all() if l.putaway_remaining > 0]

    def __str__(self):
        return self.number


class StockDocumentLine(models.Model):
    """Baris detail dokumen: item, qty, lokasi tujuan + hasil validasi."""
    document = models.ForeignKey(
        StockDocument, on_delete=models.CASCADE, related_name='lines')
    item = models.ForeignKey(Item, on_delete=models.PROTECT,
                             related_name='document_lines')
    destination_location = models.ForeignKey(
        StorageLocation, on_delete=models.PROTECT, related_name='+')
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    notes = models.CharField(max_length=255, null=True, blank=True)
    # --- hasil validasi penerimaan (US-RCV-02) ---
    received_qty = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True)
    accepted_qty = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True)
    rejected_qty = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True)
    quarantine_location = models.ForeignKey(
        StorageLocation, on_delete=models.PROTECT, null=True, blank=True,
        related_name='+',
        help_text='Lokasi karantina untuk barang rusak/tolak.')
    validated_by = models.CharField(max_length=50, null=True, blank=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    # --- putaway (US-RCV-03) ---
    putaway_qty = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True)
    putaway_status = models.CharField(
        max_length=12, choices=[
            ('pending', 'Menunggu putaway'),
            ('done', 'Putaway selesai'),
        ], default='pending')
    putaway_by = models.CharField(max_length=50, null=True, blank=True)
    putaway_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Baris Dokumen'
        verbose_name_plural = 'Baris Dokumen'

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError({'quantity': 'Kuantitas harus lebih besar dari 0.'})

    @property
    def putaway_remaining(self):
        """Sisa qty yang masih harus diputaway dari lokasi receiving."""
        if self.accepted_qty is None:
            return Decimal('0')
        return (self.accepted_qty or Decimal('0')) - (self.putaway_qty or Decimal('0'))

    def __str__(self):
        return '%s x%s' % (self.item.sku, self.quantity)


# ==================================================================
# Pengelolaan Stok — Stock Opname (Fase 3)
# ==================================================================
class StockOpname(models.Model):
    """Sesi Stock Opname per gudang (FR-COUNT-01..06).

    Alur: draft -> submitted -> approved -> posted.
    Hasil hitung dikunci saat submit; supervisor approve; posting menyesuaikan
    saldo lewat ledger (bukan overwrite langsung).
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Menunggu Persetujuan'),
        ('approved', 'Disetujui'),
        ('posted', 'Posted'),
        ('cancelled', 'Dibatalkan'),
    ]
    number = models.CharField(max_length=30, unique=True)
    opname_date = models.DateField(help_text='Tanggal pelaksanaan opname.')
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name='opnames')
    notes = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=12, choices=STATUS_CHOICES, default='draft')
    # Kunci hasil hitung setelah submit (FR-COUNT-03)
    counted_at = models.DateTimeField(null=True, blank=True)
    counted_by = models.CharField(max_length=50, null=True, blank=True)
    approved_by = models.CharField(max_length=50, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    reject_reason = models.CharField(max_length=255, null=True, blank=True)
    cancel_reason = models.CharField(max_length=255, null=True, blank=True)
    created_by = models.CharField(max_length=50)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True)
    update_by = models.CharField(max_length=50, null=True)

    class Meta:
        verbose_name = 'Stock Opname'
        verbose_name_plural = 'Stock Opname'
        ordering = ['-opname_date', '-id']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['opname_date']),
        ]

    def save(self, *args, **kwargs):
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = _current_username()
        self.update_date = timezone.now()
        self.update_by = _current_username()
        super(StockOpname, self).save(*args, **kwargs)

    @property
    def is_locked(self):
        """Sesi terkunci: hasil hitung tidak boleh diubah lagi (FR-COUNT-03)."""
        return self.status in ('submitted', 'approved', 'posted')

    @property
    def total_system(self):
        return sum((l.system_qty for l in self.lines.all()), Decimal('0'))

    @property
    def total_counted(self):
        return sum((l.counted_qty for l in self.lines.all()), Decimal('0'))

    @property
    def total_difference(self):
        return sum((l.difference for l in self.lines.all()), Decimal('0'))

    @property
    def difference_lines(self):
        """Baris yang selisihnya tidak nol (perlu investigasi)."""
        return [l for l in self.lines.all() if l.difference != 0]

    # Badge status — SATU sumber untuk semua halaman (konsisten dengan RCV)
    STATUS_LABELS = {
        'draft': ('Draft', 'bg-gradient-secondary'),
        'submitted': ('Menunggu Persetujuan', 'bg-gradient-primary'),
        'approved': ('Disetujui', 'bg-gradient-info'),
        'posted': ('Selesai', 'bg-gradient-success'),
        'cancelled': ('Dibatalkan', 'bg-gradient-danger'),
    }

    @property
    def status_label(self):
        return self.STATUS_LABELS[self.status][0]

    @property
    def status_css(self):
        return self.STATUS_LABELS[self.status][1]

    def __str__(self):
        return self.number


class StockOpnameLine(models.Model):
    """Baris hasil hitung fisik per item+lokasi, dengan snapshot qty sistem."""
    opname = models.ForeignKey(
        StockOpname, on_delete=models.CASCADE, related_name='lines')
    item = models.ForeignKey(Item, on_delete=models.PROTECT,
                             related_name='opname_lines')
    location = models.ForeignKey(
        StorageLocation, on_delete=models.PROTECT, related_name='+')
    system_qty = models.DecimalField(
        max_digits=18, decimal_places=4,
        help_text='Snapshot saldo sistem saat sesi dibuat.')
    counted_qty = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True,
        help_text='Hasil hitung fisik. Kosong = tidak dihitung.')
    notes = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Baris Opname'
        verbose_name_plural = 'Baris Opname'
        constraints = [
            models.UniqueConstraint(
                fields=['opname', 'item', 'location'],
                name='unique_opname_item_location')
        ]

    @property
    def effective_counted(self):
        """Qty fisik yang dipakai: hasil hitung, atau snapshot bila tidak dihitung."""
        if self.counted_qty is None:
            return self.system_qty
        return self.counted_qty

    @property
    def difference(self):
        """Selisih terhadap snapshot sistem."""
        return (self.effective_counted or Decimal('0')) - (
            self.system_qty or Decimal('0'))

    @property
    def current_balance(self):
        """Saldo sistem TERKINI (bukan snapshot) — untuk deteksi mutasi selama opname.

        View dapat mengisi `_current_balance` secara massal agar tidak N+1.
        """
        if hasattr(self, '_current_balance'):
            return self._current_balance
        balance = StockBalance.objects.filter(
            item=self.item, location=self.location).first()
        return balance.on_hand if balance else Decimal('0')

    @property
    def posting_difference(self):
        """Delta yang benar-benar diposting: terhadap saldo terbaru (FR-COUNT-04)."""
        return (self.effective_counted or Decimal('0')) - self.current_balance

    @property
    def balance_changed(self):
        """True bila saldo berubah selama sesi opname berjalan (FR-COUNT-04)."""
        return self.current_balance != (self.system_qty or Decimal('0'))

    def __str__(self):
        return '%s hitung %s (sistem %s)' % (
            self.item.sku, self.counted_qty, self.system_qty)
