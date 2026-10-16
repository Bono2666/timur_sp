# Product Specification (Product Spec)
## KSI Warehouse — Sistem Manajemen Pergudangan v1.0

| Field | Value |
|---|---|
| Produk | KSI Warehouse |
| Dokumen | Product Specification |
| Versi | 1.0 (Draft implementasi) |
| Tanggal | 14 Oktober 2026 |
| Referensi | `PRD_PERGUDANGAN_KSI_SOLUSI.md` v2.0; `PRD_SEKOLAH_ISLAM.md`; `PRODUCT_SPEC_SEKOLAH_ISLAM.md` |
| Video acuan | Video unggahan *Bangun Sistem Manajemen Gudang Anti Fraud dengan Odoo Inventory*, ±73 menit |
| Framework | Django 5.x, MySQL 8, Bootstrap 5, Soft UI Dashboard, jQuery AJAX, DataTables, Select2 |
| Status | Draft untuk persetujuan pemilik produk |

> **Interpretasi sumber:** Video menampilkan demonstrasi Odoo Inventory terkait lokasi, label barcode, penerimaan, pemindaian, pergerakan dan pengiriman. Product Spec ini mengadaptasi kebutuhan bisnisnya ke stack aplikasi referensi. Rincian kontrol anti-fraud, API, data model, dan validasi adalah **rancangan implementasi KSI**, bukan pernyataan bahwa semua detail tersebut terlihat atau dijelaskan di video. Audio video tidak ditranskripsi.

## Daftar Isi
1. [Konvensi Umum](#1-konvensi-umum)
2. [Authentication & Authorization](#2-authentication--authorization)
3. [Dashboard](#3-dashboard)
4. [Master Data](#4-master-data)
5. [Manajemen Gudang dan Lokasi](#5-manajemen-gudang-dan-lokasi)
6. [Barcode dan Scan Workflow](#6-barcode-dan-scan-workflow)
7. [Stock Balance, Ledger dan Reservasi](#7-stock-balance-ledger-dan-reservasi)
8. [Goods Receipt dan Putaway](#8-goods-receipt-dan-putaway)
9. [Internal Transfer](#9-internal-transfer)
10. [Delivery: Pick, Pack, Dispatch](#10-delivery-pick-pack-dispatch)
11. [Stock Adjustment dan Opname](#11-stock-adjustment-dan-opname)
12. [Laporan dan Audit](#12-laporan-dan-audit)
13. [Database Schema](#13-database-schema)
14. [URL Structure](#14-url-structure)
15. [Navigation Map](#15-navigation-map)
16. [Non-Functional Requirements](#16-non-functional-requirements)
17. [UAT dan Definition of Done](#17-uat-dan-definition-of-done)
18. [Risiko, Keputusan dan Traceability](#18-risiko-keputusan-dan-traceability)

---

## 1. Konvensi Umum

### 1.1 UI/UX baseline
Mengikuti dokumen sekolah Islam: **Soft UI Dashboard**, sidebar kiri, topbar/breadcrumb, Bootstrap cards, DataTables untuk list, Select2 untuk relasi, modal konfirmasi, toast, Font Awesome 5, Open Sans. Semua label antarmuka dalam Bahasa Indonesia. Tombol utama: `Tambah`, `Simpan Draft`, `Submit`, `Setujui`, `Validasi`, `Cetak`, `Ekspor` dan `Batalkan` sesuai status/izin.

### 1.2 Template halaman
- **Index:** judul, breadcrumb, tombol aksi, filter (gudang, status, tanggal), search, tabel paginasi, badge status, menu tindakan.
- **Create/Edit:** form card dengan label, `*` wajib isi, pesan kesalahan per field, tombol simpan eksplisit, tanpa autosave.
- **Detail:** header nomor/status, ringkasan, tab `Detail Barang`, `Tugas`, `Riwayat`, `Lampiran`, timeline operator dan tindakan kontekstual.
- **Scan panel:** input tersembunyi/terlihat yang selalu bisa difokuskan, kode terakhir, item/lokasi yang terdeteksi, qty terkonfirmasi, feedback sukses/gagal dan opsi scan ulang.
- **Mobile:** sidebar collapsible, form satu kolom, tombol sentuh besar, tabel dapat digeser horizontal.

### 1.3 Status dan aturan global
`draft → submitted → approved → in_progress → completed`, dengan cabang `rejected`/`cancelled`. Tahap approval dapat dilewati jika operation type tidak mensyaratkannya. Status tugas independen: `pending → assigned → in_progress → done` atau `exception`.

Semua `POST` menggunakan CSRF Django; semua operasi mutasi dicek permission server-side, gudang scope, validasi state, dan transaksi database atomic. Dokumen `completed/posted` tidak boleh dihapus atau diedit kuantitasnya; koreksi memakai reversal/adjustment yang dapat diaudit. Nilai kuantitas memakai `Decimal(18,4)` dan satuan dasar yang konsisten; tanggal tersimpan timezone-aware.

### 1.4 Definition of Ready
Sebelum pengembangan tiap modul: wireframe disetujui, hak akses dan state transition diputuskan, lokasi default ditetapkan, data master siap, dan skenario UAT tersedia.

## 2. Authentication & Authorization

**US-AUTH-01 — Login**: Sebagai pengguna, saya dapat login dengan `user_id` dan password.

**Field:** `user_id` (required), `password` (required). Django password hash; session idle timeout configurable.

**Acceptance criteria:**
1. Kredensial benar masuk dashboard sesuai hak akses; salah menampilkan pesan generik tanpa membocorkan keberadaan akun.
2. Akun nonaktif tidak dapat login; percobaan gagal tercatat.
3. Logout menghapus session; semua endpoint terproteksi.

**US-AUTH-02 — RBAC menu dan aksi**: Admin mengelola User, Position, Menu, Permission (`view/add/edit/delete/submit/approve/post/export`) dan `warehouse_scope`.

**Acceptance criteria:** sidebar hanya menampilkan menu yang boleh diakses; akses URL langsung tetap ditolak `403`; supervisor tidak dapat menyetujui dokumen miliknya sendiri bila segregation-of-duties aktif; akses gudang di luar scope ditolak.

**US-AUTH-03 — Audit izin**: Perubahan role, permission, dan gudang scope menyimpan aktor, waktu, nilai sebelum/sesudah.

## 3. Dashboard

**US-DASH-01 — Ringkasan operasional**: Manajer melihat kartu `SKU Aktif`, `Total Stok`, `Pending Receiving`, `Pending Putaway`, `Pending Picking`, `Pending Packing`, `Pending Dispatch`, `Exception` dan `Selisih Opname`.

**Filter:** gudang, periode, status; mengikuti warehouse scope.

**Acceptance criteria:** kartu menautkan daftar berfilter; angka konsisten dengan ledger dan tugas; tidak menghitung dokumen draft sebagai stok; loading/error/empty state tersedia.

**US-DASH-02 — Antrian tugas**: Operator melihat tugas yang ditugaskan kepadanya, urutan waktu dan status. Klik tugas membuka layar kerja terkait.

## 4. Master Data

### 4.1 Barang
**US-MST-ITEM-01**: Admin mengelola SKU, nama, barcode, kategori, satuan, stok minimum, aktif/nonaktif.

| Field | Tipe | Aturan |
|---|---|---|
| `sku` | varchar(50) | required, unik global |
| `name` | varchar(200) | required |
| `barcode` | varchar(100) | opsional, unik bila diisi |
| `category_id` | FK | required |
| `uom_id` | FK | required; immutable bila sudah ada mutasi tanpa prosedur migrasi |
| `minimum_stock` | decimal(18,4) | default 0, >= 0 |
| `is_active` | bool | default true |

**Acceptance criteria:** SKU duplikat ditolak; barang dengan riwayat transaksi tidak boleh hard delete; barang nonaktif tidak dapat dipilih untuk transaksi baru; pencarian berdasarkan SKU/nama/barcode.

### 4.2 Kategori, Satuan, Mitra
**US-MST-02**: CRUD kategori barang, satuan, supplier dan pelanggan. Validasi kode unik, nama wajib, referensi transaksi mencegah hapus fisik. Master mitra menyimpan kode, nama, kontak, alamat, status aktif.

### 4.3 Pengguna dan konfigurasi
**US-MST-03**: Konfigurasi penomoran dokumen (`RCV`, `PUT`, `TRF`, `DEL`, `ADJ`, `CNT`), reset per tahun bila dipilih, tidak boleh menghasilkan nomor ganda meskipun submit bersamaan.

## 5. Manajemen Gudang dan Lokasi

**US-LOC-01 — Gudang**: Admin membuat gudang (`code`, `name`, `address`, `active`, `manager`). Kode unik.

**US-LOC-02 — Hirarki lokasi**: Admin mengelola `Gudang → Zona → Rak → Bin` dengan parent fleksibel, tipe lokasi `storage/receiving/staging/packing/dispatch/quarantine`, kode lokasi dan barcode.

| Field | Tipe | Validasi |
|---|---|---|
| `warehouse_id` | FK | wajib |
| `parent_id` | FK self | nullable; parent wajib satu gudang |
| `code` | varchar(60) | unik dalam gudang |
| `name` | varchar(150) | wajib |
| `barcode` | varchar(100) | unik global |
| `location_type` | enum | wajib |
| `is_active` | bool | default true |

**Acceptance criteria:** parent tidak boleh membentuk siklus; lokasi dengan saldo/reservasi/tugas terbuka tidak boleh dinonaktifkan; pohon lokasi dapat expand/collapse; pencarian menampilkan breadcrumb lokasi.

**US-LOC-03 — Cetak label**: Pengguna berizin mencetak PDF label barcode lokasi satuan atau massal. Label berisi nama gudang, kode lokasi, barcode yang dapat dipindai, dan nama lokasi. Format kertas/ukuran label dapat dikonfigurasi.

**US-LOC-04 — Temukan barang**: Pengguna mencari SKU/barcode dan melihat lokasi, on-hand, reserved, available, quarantine per gudang sesuai scope.

## 6. Barcode dan Scan Workflow

**US-SCAN-01 — Scan barang/lokasi**: Operator memakai scanner USB/Bluetooth keyboard-wedge di browser. Input scan memproses `Enter`, mencari identitas dan menampilkan feedback.

**Acceptance criteria:**
1. Kode tak dikenal ditolak tanpa menambah kuantitas.
2. Scan lokasi tidak diterima ketika sistem meminta barcode produk dan sebaliknya.
3. Scan ulang tidak menggandakan posting; scan event tercatat per tugas.
4. UI menampilkan qty target, qty terproses, qty sisa, lokasi sumber/tujuan.
5. Scan manual tanpa perangkat didukung hanya bila permission `manual_override` diberikan; alasan wajib.

**US-SCAN-02 — Scan per baris tugas**: Scan barang mengonfirmasi item, scan bin mengonfirmasi lokasi, lalu kuantitas (default increment 1 per scan atau input batch yang tervalidasi). **Keputusan terbuka:** urutan scan dan default qty perlu dikonfirmasi.

**US-SCAN-03 — Kegagalan koneksi**: Jika request gagal, tampilkan status belum tersimpan; operator dapat retry dengan `idempotency_key`, sehingga retry tidak menggandakan mutasi.

## 7. Stock Balance, Ledger dan Reservasi

**US-STOCK-01 — Saldo stok**: Tabel stok per barang+lokasi menampilkan `on_hand`, `reserved`, `available = on_hand - reserved`, dan `quarantine` berdasarkan tipe lokasi. Nilai disajikan per gudang dan agregat.

**US-STOCK-02 — Kartu stok**: Semua perubahan on-hand menghasilkan `StockLedger` append-only dengan referensi dokumen, item, sumber/tujuan, qty bertanda, operator, waktu dan reversal reference bila ada.

**US-STOCK-03 — Reservasi**: Submit/approve delivery dapat melakukan reservasi atomik terhadap available. Pembatalan melepas reservasi; pick/dispatch memperbarui reservasi sesuai tahap; tidak ada reservasi ganda.

**Acceptance criteria:**
1. Dua operator bersamaan tidak bisa mengeluarkan stok melebihi available.
2. Posting dokumen dua kali tidak menggandakan ledger.
3. Mutasi internal mengurangi lokasi asal dan menambah lokasi tujuan dalam satu transaksi, tanpa mengubah total stok gudang bila satu gudang.
4. Receiving dan putaway tidak menggandakan total stok ketika barang dipindah ke storage.
5. Stok quarantine tidak tersedia untuk picking reguler.

## 8. Goods Receipt dan Putaway

**US-RCV-01 — Buat penerimaan**: Petugas membuat dokumen receipt dari supplier (referensi PO opsional) dan daftar barang expected.

| Field | Tipe | Aturan |
|---|---|---|
| `document_no` | string | auto, unik |
| `warehouse` | FK | required dan dalam scope |
| `supplier` | FK | required untuk receipt pembelian; jenis receipt lain dapat configurable |
| `reference_no` | string | opsional |
| `operation_type` | FK | receipt 1 tahap/2 tahap |
| `lines[item, expected_qty, uom]` | collection | minimal 1, qty > 0 |
| `notes` | text | opsional |

**US-RCV-02 — Validasi receiving**: Operator menerima barang ke `receiving` (2 tahap) atau storage default (1 tahap), melakukan scan produk, memasukkan `received_qty`, `accepted_qty`, `rejected_qty`, alasan variance.

**Acceptance criteria:** expected/received/accepted/rejected terlihat; `accepted+rejected <= received`; selisih memerlukan alasan; dokumen hanya diposting sekali; tanggal, operator dan scan tersimpan.

**US-RCV-03 — Putaway**: Untuk receipt 2 tahap, sistem membuat tugas putaway dengan sumber receiving, tujuan bin storage. Operator scan barang+lokasi dan validasi pemindahan.

**Acceptance criteria:** qty putaway tidak boleh melebihi saldo receiving; partial putaway diperbolehkan dan sisa tampil pending; setiap perpindahan menulis dua sisi ledger secara atomik; status receipt selesai ketika seluruh qty yang harus disimpan selesai dipindahkan atau ditangani exception.

**US-RCV-04 — Selisih/rusak**: Barang rejected diarahkan ke quarantine dengan alasan; approval exception sesuai threshold konfigurasi. **Threshold belum ditetapkan pemilik produk.**

## 9. Internal Transfer

**US-TRF-01**: Petugas membuat transfer antar bin atau antar gudang dengan sumber, tujuan, barang dan qty. Submit → approve jika perlu → scan sumber+barang+tujuan → validasi.

**Acceptance criteria:** sumber dan tujuan tidak sama; sumber punya available cukup; transfer partial tercatat; total stok global tidak berubah akibat transfer; cross-warehouse mengikuti scope kedua gudang; transfer cancelled tidak memodifikasi ledger yang sudah posted (gunakan reversal).

**US-TRF-02**: List menampilkan nomor, gudang, sumber, tujuan, operator, status, tanggal; filter dan ekspor.

## 10. Delivery: Pick, Pack, Dispatch

**US-DEL-01 — Buat delivery**: Petugas membuat delivery ke pelanggan/tujuan, daftar barang dan qty, operation type 1 tahap atau 3 tahap, serta tanggal rencana.

**US-DEL-02 — Reserve & Picking**: Setelah submit/approval, stok dapat direservasi dan sistem membentuk picking task berdasarkan lokasi stok. Operator scan bin+produk dan konfirmasi qty.

**Acceptance criteria:** tidak dapat pick di luar lokasi yang diizinkan tanpa override; overpick ditolak; short-pick membutuhkan alasan; picked qty tidak melebihi reserved/authorized; partial picking dapat dilanjutkan.

**US-DEL-03 — Packing**: Operator melihat daftar hasil pick, memverifikasi jumlah, mencatat `package_no`, jumlah kemasan, dan mengonfirmasi packing.

**Acceptance criteria:** packed qty tidak boleh melebihi picked qty; jika mismatch, status exception dan tidak bisa dispatch sampai terselesaikan; waktu dan packer tercatat.

**US-DEL-04 — Dispatch**: Petugas memvalidasi jumlah final, mengisi kurir/penerima bila diperlukan, mencetak surat jalan dan mengonfirmasi serah terima.

**Acceptance criteria:** dispatch tidak boleh melebihi packed; stok keluar dari gudang hanya sekali pada titik dispatch yang ditentukan; dokumen completed immutable; bukti dispatch terhubung ke dokumen.

**US-DEL-05 — One-step issue**: Gudang yang menggunakan operation type 1 tahap dapat melakukan pengeluaran langsung dengan validasi stok dan permission. Ledger tetap atomik dan tercatat.

**US-DEL-06 — Pembatalan dan retur**: Delivery sebelum dispatch dapat dibatalkan dengan pelepasan reservasi dan reversal movement internal jika perlu. Retur setelah dispatch memerlukan dokumen receipt baru yang merujuk delivery asal (**retur lengkap P1**).

## 11. Stock Adjustment dan Opname

**US-ADJ-01 — Adjustment**: Supervisor mengusulkan koreksi stok item/lokasi dengan qty sistem, qty usulan, selisih dan alasan; approval oleh role lain bila wajib.

**Acceptance criteria:** tidak ada edit langsung saldo; adjustment posted menghasilkan ledger; approval tidak dapat dilakukan pembuat bila SoD aktif; adjustment melebihi threshold wajib approval khusus.

**US-CNT-01 — Stock Opname**: Admin membuat sesi opname per gudang/lokasi dengan snapshot qty, assign petugas, dan waktu mulai. Operator menghitung fisik (scan/manual sesuai izin) tanpa melihat qty sistem bila mode blind count diaktifkan.

**US-CNT-02 — Rekonsiliasi**: Supervisor membandingkan counted vs snapshot, menginvestigasi selisih, lalu approve adjustment.

**Acceptance criteria:** satu sesi tidak diposting dua kali; snapshot dan timestamp jelas; mutasi saat opname ditangani dengan freeze lokasi atau rekonsiliasi movement selama periode (kebijakan dipilih); hasil count, selisih dan persetujuan dapat diaudit.

## 12. Laporan dan Audit

**US-RPT-01**: Laporan saldo per gudang/lokasi, kartu stok, receipt, putaway pending, transfer, delivery, adjustment, opname dan exception; filter periode/gudang/SKU/operator/status; export XLSX/CSV dan PDF untuk laporan yang dipilih.

**US-RPT-02 — Anti-fraud dashboard**: Supervisor melihat transaksi manual override, selisih receiving, adjustment, reversal, transaksi terlambat, serta operator dan waktu.

**US-AUD-01**: Audit trail mencatat login gagal, perubahan master, permission, workflow transition, scan, manual override, approval, posting dan reversal. Tampilkan before/after untuk perubahan data; audit append-only; hanya auditor/superuser dapat melihat sesuai scope.

**Acceptance criteria:** export mematuhi izin dan warehouse scope; jumlah laporan konsisten dengan ledger; pagination server-side untuk data besar; tidak ada informasi gudang terlarang pada pencarian atau API.

## 13. Database Schema

### 13.1 Tabel inti
| Model | Field penting | Index/constraint |
|---|---|---|
| `User` | user_id, password, position, is_active | unique user_id |
| `MenuPermission` | user/position, menu, action | unique subject+menu+action |
| `UserWarehouseAccess` | user, warehouse | unique user+warehouse |
| `Item` | sku, name, barcode, category, uom, min_stock, active | unique sku, barcode |
| `Category` | code, name | unique code |
| `UOM` | code, name | unique code |
| `Partner` | code, name, type, contact | unique code |
| `Warehouse` | code, name, address, active | unique code |
| `StorageLocation` | warehouse, parent, code, barcode, type, active | unique warehouse+code, unique barcode |
| `OperationType` | warehouse, code, kind, flow_mode, default locations | unique warehouse+code |
| `StockDocument` | no, type, warehouse, partner, status, created_by, approved_by, posted_at | unique no, index status/date |
| `StockDocumentLine` | document, item, expected_qty, processed_qty, rejected_qty, uom | FK, qty constraints |
| `WarehouseTask` | document, task_type, assignee, status, timestamps | index assignee/status |
| `WarehouseTaskLine` | task, item, src, dst, expected_qty, processed_qty | qty >= 0 |
| `StockLedger` | movement_key, document_line, item, location, qty_delta, posted_at, actor, reversal_of | unique movement_key+location, append-only |
| `StockBalance` | item, location, on_hand, reserved | unique item+location; index location |
| `StockReservation` | document_line, item, location, qty, status | unique reservation identity |
| `ScanEvent` | task_line, raw_code, scan_type, result, actor, timestamp, idempotency_key | unique idempotency_key |
| `StockException` | document, task, kind, expected, actual, reason, approval | index status/type |
| `StockCount` | warehouse, scope, snapshot_at, status, created_by | index warehouse/status |
| `StockCountLine` | count, item, location, snapshot_qty, counted_qty, variance | unique count+item+location |
| `StockPackage` | task, package_no, packed_at, packed_by | unique package_no |
| `DispatchProof` | task, recipient, carrier, handed_over_at, attachment | FK task |
| `AuditLog` | actor, action, model, object_id, before_json, after_json, timestamp | index model/object/time |

### 13.2 Integritas dan concurrency
- Seluruh mutasi ledger dan balance dalam `transaction.atomic()` dengan `select_for_update()` pada saldo yang terdampak.
- Urutkan penguncian berdasarkan `(item_id, location_id)` untuk mengurangi deadlock.
- Gunakan unique idempotency key per perintah posting/scan yang menulis perubahan.
- `on_hand >= 0` dan `reserved >= 0` serta `reserved <= on_hand` untuk lokasi picking biasa; pengecualian hanya melalui aturan bisnis eksplisit.
- Jangan gunakan float untuk kuantitas; normalisasi UOM sebelum posting.
- Audit dan event scan append-only; simpan lampiran dengan akses terotorisasi.

### 13.3 Contoh state transition
| Dokumen/Tugas | Dari | Ke | Role/Aksi | Efek stok |
|---|---|---|---|---|
| Receipt | draft | submitted | creator/submit | tidak ada |
| Receipt | submitted | approved | supervisor/approve | tidak ada |
| Receiving | pending | done | receiver/validate | + receiving/storage |
| Putaway | pending | done | putaway/validate | - receiving, + storage |
| Delivery | submitted | approved | supervisor/approve | reservasi opsional |
| Picking | pending | done | picker/validate | internal movement storage → staging |
| Packing | pending | done | packer/confirm | internal movement bila lokasi berbeda |
| Dispatch | pending | done | dispatcher/validate | - stok fisik dari dispatch location |
| Adjustment | approved | completed | supervisor/post | +/- ledger |

## 14. URL Structure

| URL | Method | Fungsi |
|---|---|---|
| `/login/`, `/logout/` | GET/POST | Authentication |
| `/dashboard/` | GET | Dashboard |
| `/master/items/`, `/master/items/add/`, `/master/items/<id>/edit/` | GET/POST | Barang |
| `/master/categories/`, `/master/uoms/`, `/master/partners/` | GET/POST | Master lain |
| `/warehouses/`, `/warehouses/<id>/locations/` | GET/POST | Gudang dan lokasi |
| `/locations/<id>/label/`, `/locations/labels/` | GET/POST | Label PDF |
| `/inventory/balances/`, `/inventory/ledger/`, `/inventory/reservations/` | GET | Stok |
| `/receipts/`, `/receipts/add/`, `/receipts/<id>/` | GET/POST | Receipt |
| `/receipts/<id>/submit/`, `/receipts/<id>/approve/` | POST | Transisi |
| `/tasks/`, `/tasks/<id>/`, `/tasks/<id>/scan/`, `/tasks/<id>/validate/` | GET/POST | Tugas & scan |
| `/transfers/`, `/transfers/add/`, `/transfers/<id>/` | GET/POST | Transfer |
| `/deliveries/`, `/deliveries/add/`, `/deliveries/<id>/` | GET/POST | Delivery |
| `/deliveries/<id>/delivery-note/` | GET | Surat jalan PDF |
| `/adjustments/`, `/stock-counts/` | GET/POST | Koreksi/opname |
| `/reports/<report_key>/` | GET | Laporan |
| `/audit-logs/` | GET | Audit |
| `/settings/operation-types/`, `/settings/permissions/` | GET/POST | Pengaturan |

Endpoint AJAX mengembalikan JSON `{success, message, data, errors}`; status HTTP `400` validasi, `401` belum login, `403` tanpa izin, `404` tidak ditemukan/di luar scope, `409` konflik state/stock, `500` internal error. Semua URL mutasi `POST` dengan CSRF, tidak memakai GET untuk perubahan data.

## 15. Navigation Map

```text
Dashboard
Master Data
  Barang | Kategori | Satuan | Supplier/Pelanggan
  Gudang | Lokasi Penyimpanan | Cetak Label Lokasi
  User | Position | Menu & Hak Akses
Persediaan
  Saldo Stok | Kartu Stok | Reservasi | Temukan Barang
Operasional Gudang
  Penerimaan Barang | Tugas Putaway
  Transfer Internal
  Pengiriman Barang | Tugas Picking | Tugas Packing | Tugas Dispatch
  Antrian Tugas | Exception
Kontrol Stok
  Penyesuaian Stok | Stock Opname
Laporan
  Saldo | Mutasi | Penerimaan | Pengiriman | Selisih | Audit
Pengaturan
  Tipe Operasi | Penomoran | Preferensi
```

## 16. Non-Functional Requirements

| Kategori | Requirement |
|---|---|
| Security | Django CSRF, password hashing, permission backend, session timeout, HTTPS, rate-limit login |
| Performance | Daftar data server-side pagination; indeks stok/ledger; target p95 < 2 detik untuk list standar (perlu benchmark) |
| Concurrency | Atomic posting, row lock, idempotency, retry aman |
| Availability | Backup harian, restore test berkala, monitoring error; target SLA ditentukan saat deployment |
| Audit | Ledger dan audit append-only, retention policy perlu keputusan |
| Compatibility | Desktop browser modern; tablet/mobile responsif; scanner keyboard-wedge |
| Accessibility | Label form, keyboard navigation, feedback teks selain warna |
| Internationalization | UI Bahasa Indonesia, timezone Asia/Jakarta; timestamp UTC di storage |
| Deployment | Docker + Gunicorn + Nginx + MySQL; secret environment; volume media/backup |
| Quality | Unit test model/permission, integration test posting, E2E UAT scan dan workflow |

## 17. UAT dan Definition of Done

| ID | Skenario UAT | Expected Result |
|---|---|---|
| UAT-01 | Login pengguna gudang A, akses data gudang B | 403 / data tidak muncul |
| UAT-02 | Buat lokasi dengan parent siklik | Ditolak |
| UAT-03 | Cetak barcode lokasi dan scan kembali | Kode terpetakan ke lokasi benar |
| UAT-04 | Receipt 10 unit ke receiving, putaway 10 unit | Total stok +10, bukan +20 |
| UAT-05 | Putaway parsial 6 dari 10 | Storage +6, receiving tersisa 4 |
| UAT-06 | Scan SKU salah pada picking | Ditolak dan dicatat |
| UAT-07 | Dua operator dispatch stok 5 untuk masing-masing 4 | Maksimum satu transaksi berhasil sesuai stok |
| UAT-08 | Retry posting request dengan idempotency key sama | Ledger hanya satu kali |
| UAT-09 | Packing qty lebih besar dari picked | Ditolak |
| UAT-10 | Dispatch tanpa packing pada flow 3 tahap | Ditolak |
| UAT-11 | Operator approve adjustment buatannya sendiri | Ditolak jika SoD aktif |
| UAT-12 | Edit/hapus dokumen completed | Ditolak; reversal tersedia |
| UAT-13 | Opname selisih, approve, post | Ledger adjustment benar, jejak audit lengkap |
| UAT-14 | Export laporan sebagai pengguna terbatas | Hanya data sesuai warehouse scope |
| UAT-15 | Barcode scan dua kali secara cepat | Tidak ada double posting tak sah |

**Definition of Done per modul:** migration valid, permission dan warehouse scope dites, error handling, empty/loading states, audit log, test otomatis, UAT disetujui, dokumentasi pengguna, serta tidak ada perubahan stok di luar ledger.

## 18. Risiko, Keputusan dan Traceability

### 18.1 Prioritas implementasi
**P0 / MVP:** Authentication/RBAC, master barang, gudang+lokasi, barcode label, saldo+ledger, receipt 1/2 tahap, putaway, scan, transfer, delivery 1/3 tahap, reservasi, picking, packing/dispatch dasar, adjustment, opname, audit dan laporan dasar.

**P1:** Alert exception, paket multi-koli, bukti serah terima, approval threshold kompleks, produktivitas operator, PDF lanjutan.

**P2:** Kamera scanner, mobile offline, serial/lot, expiry, integrasi PO/SO, ERP dan optimasi lokasi.

### 18.2 Keputusan terbuka
1. Default receipt 1 atau 2 tahap per gudang?
2. Default delivery 1 atau 3 tahap per gudang?
3. Kewajiban scan lokasi di semua movement?
4. Metode input kuantitas scanner: per unit atau batch?
5. Kebijakan partial/backorder dan quarantine?
6. Threshold approval dan matrix segregasi tugas?
7. Freeze stock atau reconciliation saat opname?
8. Kebutuhan tanda tangan/foto bukti dispatch?
9. Apakah stock valuation/lot/serial diperlukan fase pertama?

### 18.3 Traceability video dan rancangan
| Materi | Referensi visual perkiraan | Product Spec |
|---|---|---|
| Masalah barang sulit ditemukan | 03:00 | 5, 7, 12 |
| Master produk | 09:00 | 4 |
| Hirarki lokasi dan label barcode | 12:00–18:00 | 5–6 |
| Goods receipt / receiving area | 21:00–27:00 | 8 |
| Scanner barcode | 30:00–33:00 | 6, 8, 10 |
| Transfer / inventory report | 39:00–45:00 | 7, 9, 12 |
| Pick–pack–delivery | 48:00–57:00 | 10 |
| Operation types | 60:00–66:00 | 5, 13 |
| Segregation of duties, idempotency, DB locks | Usulan kontrol anti-fraud, bukan klaim isi video | 2, 7, 13 |

**Catatan akhir:** Detail implementasi di sini perlu review Product Owner sebelum dijadikan baseline sprint; khususnya mode operasi, kebijakan stok, dan approval.
