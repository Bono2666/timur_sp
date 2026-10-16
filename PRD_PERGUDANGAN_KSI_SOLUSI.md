# Product Requirements Document (PRD)
## Sistem Manajemen Pergudangan — KSI Warehouse

| Field | Value |
|---|---|
| Nama Produk | KSI Warehouse — Warehouse Management System (WMS) |
| Versi Dokumen | 2.0 (Revisi berdasarkan video) |
| Tanggal | 14 Oktober 2026 |
| Pengembang | KSI Solusi |
| Status | Proposed / Belum dikembangkan |
| Referensi Teknis & UI | `PRD_SEKOLAH_ISLAM.md`, `PRODUCT_SPEC_SEKOLAH_ISLAM.md` |
| Referensi Video | https://www.youtube.com/watch?v=4veWoiL87kI&t=1090s |

> **Dasar revisi:** Video unggahan berdurasi ±73 menit telah ditinjau melalui cuplikan visual berkala. Video memperlihatkan presentasi dan demonstrasi **Odoo Inventory** mengenai lokasi gudang, label barcode lokasi, penerimaan barang, scanner barcode, pengiriman, dan pelacakan perpindahan. Dokumen ini mengadaptasi kebutuhan bisnis tersebut ke **Django + Soft UI Dashboard** mengikuti dokumen referensi; bukan spesifikasi implementasi Odoo. **Batas verifikasi:** audio/narasi tidak ditranskripsi; rincian aturan yang tidak terbaca pada video ditandai sebagai *usulan* dan perlu dikonfirmasi.

---

## 1. Executive Summary
KSI Warehouse adalah aplikasi web internal untuk mengelola persediaan barang, penerimaan, penyimpanan, pemindahan, pengeluaran, penyesuaian stok, stok opname, dan pelaporan lintas gudang. Semua perubahan kuantitas harus berasal dari transaksi yang dapat diaudit, bukan perubahan langsung pada angka saldo.

**Target:** perusahaan kecil-menengah dengan satu atau lebih gudang, staf gudang, admin inventaris, supervisor, dan manajemen. Antarmuka Bahasa Indonesia, responsif untuk desktop/tablet/mobile, mendukung barcode produk dan lokasi menggunakan scanner keyboard-wedge sejak MVP.

## 2. Goals, KPIs & Batasan
| Sasaran | KPI awal yang diusulkan | Cara ukur |
|---|---|---|
| Akurasi stok | >= 98% | Kesesuaian hasil opname dengan sistem |
| Ketertelusuran | 100% transaksi posted memiliki aktor, waktu, dokumen | Audit log |
| Efisiensi transaksi | Penerimaan/pengeluaran standar < 3 menit per dokumen sederhana | Waktu penyelesaian |
| Pencegahan stok negatif | 0 transaksi menyebabkan stok available negatif secara tidak sah | Validasi sistem |
| Monitoring | Saldo per gudang/lokasi tersedia setiap saat | Rekonsiliasi ledger |

**Dalam lingkup MVP:** multi-gudang, lokasi/rak, barang, kategori, satuan, supplier/customer, saldo, penerimaan, pengeluaran, transfer, adjustment, opname, laporan, RBAC, audit, import/export.

**Di luar MVP:** akuntansi/valuasi persediaan, integrasi ERP/marketplace, mobile native, wave picking, serial/lot/expiry, purchase order/sales order penuh, optimasi slotting, multi-company, offline sync. Dicatat sebagai fase berikutnya. **Revisi prioritas video:** label barcode lokasi, pemindaian barang/lokasi, alur penerimaan dua tahap, dan alur pengiriman pick–pack–delivery dimasukkan sebagai kebutuhan prioritas tinggi, dengan aktivasi per gudang.

## 3. Personas & Hak Akses
| Role | Tanggung jawab | Akses utama |
|---|---|---|
| Superuser | Konfigurasi teknis | Seluruh akses |
| Admin Gudang | Master, transaksi, pengguna | CRUD sesuai menu |
| Petugas Penerimaan | Terima dan simpan barang | Create draft, submit penerimaan |
| Petugas Pengeluaran | Picking dan pengeluaran | Create draft, submit pengeluaran |
| Supervisor | Validasi, approval, adjustment, opname | Approve/post sesuai matriks |
| Manajer | Monitoring dan analitik | Read/report/export |
| Auditor | Pemeriksaan mutasi dan perubahan | Read audit/ledger |

**RBAC:** ikuti pola referensi `User + Menu + add/edit/delete`, diperluas dengan `view`, `approve`, `post`, `export` dan **warehouse scope**. Semua otorisasi diperiksa di backend, tidak hanya tombol UI. Superuser bypass. Tidak boleh melakukan approve sendiri jika konfigurasi segregation-of-duties aktif.

## 4. Tech Stack (mengikuti dokumen referensi)
| Lapisan | Pilihan | Keterangan |
|---|---|---|
| Backend | Python 3.11+ / Django 5.x | Pertahankan pola Django server-rendered; gunakan versi patch yang masih didukung saat implementasi |
| Database | MySQL 8.x | Django ORM, transaksi ACID, index & constraint |
| Frontend | Bootstrap 5 + Soft UI Dashboard (Argon-style) | Konsisten dengan proyek referensi |
| Interaksi | jQuery AJAX + Fetch jika diperlukan | CSRF, validasi server, update tabel tanpa full reload |
| Tabel | DataTables Bootstrap 5 | Pagination, sorting, filter server-side |
| Form | Select2, jQuery UI (opsional) | Dropdown searchable |
| Icons | Font Awesome 5 | Konsistensi desain |
| Typography | Open Sans | Konsistensi desain |
| Import/export | django-import-export, openpyxl/xlsxwriter | XLSX/CSV |
| Cetak | ReportLab atau xhtml2pdf | Surat jalan, penerimaan, laporan PDF |
| Deployment | Docker + Gunicorn + Nginx | Konfigurasi environment terpisah |
| Timezone | Asia/Jakarta | Simpan UTC aware di database, tampilkan WIB |

**Keputusan desain:** tidak menyalin konfigurasi `USE_TZ=False` dari proyek lama; gunakan `USE_TZ=True` untuk keamanan timestamp dan integrasi. Hindari paket lama yang tidak kompatibel dengan versi Django yang dipilih.

## 5. Prinsip UX/UI
- Desktop: sidebar kiri berkelompok, topbar dengan breadcrumb, area konten kartu Soft UI, tabel DataTables, tombol aksi di kanan atas.
- Mobile: sidebar collapsible, form satu kolom, tabel horizontal-scroll atau kartu ringkas.
- Halaman daftar: judul, breadcrumb, tombol Tambah, filter (gudang/status/tanggal), search, DataTables, export.
- Halaman detail: nomor dokumen, status badge, ringkasan, tab Detail Barang / Riwayat / Lampiran, aksi kontekstual.
- Form: layout card, label Indonesia, indikator required, Select2 barang/lokasi, grid baris transaksi, subtotal qty.
- Status warna konsisten: Draft abu-abu, Submitted biru, Approved teal, Posted hijau, Cancelled merah.
- Loading indicator, toast sukses/error, konfirmasi tindakan irreversible, empty states, skeleton saat memuat.
- Dark mode opsional fase 2; gunakan token warna agar mudah diimplementasikan.
- **Tidak ada autosave transaksi**: pengguna menekan Simpan Draft; posting selalu eksplisit.

## 6. Navigasi Utama
```text
Dashboard
Master Data
  Barang / Kategori Barang / Satuan
  Gudang / Lokasi Penyimpanan
  Supplier / Pelanggan
  Pengguna / Posisi / Menu & Hak Akses
Persediaan
  Stok Saat Ini
  Kartu Stok / Mutasi Stok
  Stok Minimum
Transaksi Gudang
  Penerimaan Barang
  Pengeluaran Barang
  Transfer Antar Lokasi/Gudang
  Penyesuaian Stok
Stock Opname
  Sesi Opname
  Selisih & Persetujuan
Laporan
  Saldo Stok / Mutasi / Penerimaan / Pengeluaran
  Transfer / Adjustment / Opname
Pengaturan
  Penomoran Dokumen / Preferensi / Audit Log
```

## 7. Functional Requirements

### 7.1 Authentication & User Management — P0
**FR-AUTH-01** Login dengan `user_id` dan password hash Django; logout; change password; reset oleh admin. **FR-AUTH-02** Session idle timeout configurable (default 15 menit). **FR-AUTH-03** Sidebar dan endpoint berdasarkan RBAC. **FR-AUTH-04** Permission dibatasi per gudang. **FR-AUTH-05** Catat login gagal dan perubahan izin.

### 7.2 Dashboard — P0
**FR-DASH-01** KPI: total SKU aktif, total qty on-hand, stok di bawah minimum, transaksi menunggu approval, penerimaan/pengeluaran hari ini. **FR-DASH-02** Filter gudang dan rentang tanggal. **FR-DASH-03** Grafik inbound/outbound bulanan; 10 barang terendah stoknya; aktivitas terakhir. **FR-DASH-04** Drill-down kartu ke halaman terkait dengan filter.

### 7.3 Master Barang — P0
**FR-ITEM-01** CRUD barang: `sku` unik, nama, kategori, satuan dasar, barcode opsional, deskripsi, status aktif, minimum stok, foto opsional. **FR-ITEM-02** Barang yang pernah dipakai transaksi tidak dapat dihapus fisik; nonaktifkan. **FR-ITEM-03** SKU/barcode unik; validasi server. **FR-ITEM-04** Satuan transaksi MVP harus sama dengan satuan dasar; konversi multi-UOM fase 2.

### 7.4 Gudang & Lokasi — P0
**FR-WH-01** CRUD gudang (kode unik, nama, alamat, penanggung jawab, status). **FR-WH-02** CRUD lokasi dengan parent warehouse, kode unik per gudang, tipe `storage/receiving/shipping/quarantine`, status aktif. **FR-WH-03** Tidak boleh nonaktifkan lokasi dengan stok tersisa tanpa migrasi stok. **FR-WH-04** Semua mutasi mencatat lokasi asal/tujuan yang valid.

### 7.5 Stok & Kartu Stok — P0
**FR-STOCK-01** Saldo on-hand per `(item, warehouse, location)` dihitung dari ledger transaksi posted. **FR-STOCK-02** Tampilkan qty on-hand, reserved (fase 2; default 0), available = on-hand - reserved. **FR-STOCK-03** Kartu stok: waktu, tipe, nomor dokumen, lokasi, qty masuk, qty keluar, saldo berjalan, aktor. **FR-STOCK-04** Filter SKU, gudang, lokasi, tanggal; export XLSX. **FR-STOCK-05** Posting atomic dengan row lock; dilarang saldo negatif kecuali konfigurasi khusus yang diaudit.

### 7.6 Penerimaan Barang — P0
**FR-IN-01** Buat dokumen penerimaan dengan nomor otomatis, tanggal, gudang, supplier opsional, referensi eksternal, catatan. **FR-IN-02** Detail berisi item, qty positif, lokasi tujuan, catatan. **FR-IN-03** Alur `draft -> submitted -> approved -> posted`, atau `draft -> cancelled`; supervisor dapat menolak `submitted -> draft` dengan alasan. **FR-IN-04** Hanya posted menambah stok. **FR-IN-05** Cetak bukti penerimaan dan lampiran opsional.

### 7.7 Pengeluaran Barang — P0
**FR-OUT-01** Buat dokumen pengeluaran dengan tujuan/pelanggan opsional, referensi, tanggal, gudang, detail item/qty/lokasi. **FR-OUT-02** Cek stok available pada saat submit dan posting ulang pada saat post. **FR-OUT-03** Alur approval sama dengan penerimaan. **FR-OUT-04** Posting mengurangi stok atomically. **FR-OUT-05** Cetak bukti pengeluaran/surat jalan.

### 7.8 Transfer Stok — P0
**FR-TRF-01** Transfer dari lokasi asal ke lokasi tujuan (dalam gudang maupun lintas gudang). **FR-TRF-02** Validasi asal ≠ tujuan, qty positif, saldo cukup. **FR-TRF-03** MVP: satu langkah posting yang membuat pasangan ledger OUT/IN dalam satu database transaction; tidak ada in-transit. **FR-TRF-04** Persetujuan supervisor untuk lintas gudang configurable.

### 7.9 Adjustment — P0
**FR-ADJ-01** Adjustment plus/minus dengan reason code wajib. **FR-ADJ-02** Perubahan harus disetujui supervisor sebelum posting. **FR-ADJ-03** Catat kuantitas delta, alasan, lampiran, approver. **FR-ADJ-04** Tidak boleh menghasilkan stok negatif.

### 7.10 Stock Opname — P0
**FR-COUNT-01** Buat sesi opname per gudang/lokasi dan snapshot qty sistem saat mulai. **FR-COUNT-02** Masukkan hitungan fisik per item; tampilkan selisih setelah submit (blind count opsional fase 2). **FR-COUNT-03** Kunci hasil hitung setelah submit; supervisor review dan approve. **FR-COUNT-04** Saat post, hitung delta terhadap **saldo terbaru**, bukan hanya snapshot; tampilkan warning perubahan selama opname dan wajib reconfirm. **FR-COUNT-05** Posting menghasilkan adjustment ledger; tidak langsung overwrite saldo. **FR-COUNT-06** Cegah double-post dan overlap sesi aktif pada scope sama kecuali diizinkan kebijakan.

### 7.11 Reports — P0
**FR-RPT-01** Saldo stok per SKU/gudang/lokasi. **FR-RPT-02** Kartu stok dan mutasi berdasarkan periode. **FR-RPT-03** Rekap penerimaan, pengeluaran, transfer, adjustment. **FR-RPT-04** Hasil opname & variance. **FR-RPT-05** Ekspor XLSX/CSV dan PDF terfilter; catat user ekspor.

### 7.12 Import & Export — P1
Wizard upload -> preview 5 baris -> mapping -> validasi -> konfirmasi -> ringkasan. Import master barang, gudang/lokasi, supplier/customer. Deteksi duplikat dengan SKU/kode unik, opsi skip/update, unduh error report; jangan mengimpor saldo awal langsung: gunakan dokumen **Opening Balance** yang diposting dan tercatat di ledger.

### 7.13 Notification & Audit — P1
Notifikasi dalam aplikasi untuk approval pending, stok minimum, transaksi ditolak. Audit event append-only untuk create/update/status/approve/post/cancel, before/after perubahan metadata, IP dan user agent secara proporsional. Dokumen posted tidak dapat diedit/hapus; koreksi melalui reversal document dengan alasan.

## 8. Workflow & State Machine
```text
DRAFT --submit--> SUBMITTED --approve--> APPROVED --post--> POSTED
  |                   |                  |
  +--cancel--> CANCELLED    +--reject--> DRAFT
```
- Cancel hanya sebelum posted; dokumen posted dikoreksi melalui reversal terotorisasi.
- Dokumen yang sudah submitted tidak boleh diedit sampai dikembalikan ke draft.
- Approval dan posting adalah aksi POST dengan CSRF dan idempotency key.
- Nomor dokumen otomatis unik per tipe/tahun: `IN/2026/000001`, `OUT/...`, `TRF/...`, `ADJ/...`, `CNT/...`.

## 9. Data Model & Constraints
| Model | Field utama | Constraints |
|---|---|---|
| `User` | `user_id` PK, username, email, position, is_active | `USERNAME_FIELD=user_id` |
| `Menu`, `Auth`, `UserWarehouseAccess` | menu_id, user, permission flags, warehouse | unique user-menu dan user-warehouse |
| `ItemCategory` | id, code, name | code unique |
| `Unit` | id, code, name | code unique |
| `Item` | id, sku, barcode, name, category FK, unit FK, min_stock, is_active | sku unique; barcode unique nullable |
| `Warehouse` | id, code, name, address, is_active | code unique |
| `StorageLocation` | id, warehouse FK, code, name, type, is_active | unique warehouse-code |
| `Partner` | id, type, code, name, address, phone | unique code |
| `StockDocument` | id, number, type, status, warehouse, partner, reference, date, notes, submitted_by, approved_by, posted_at | number unique; typed workflow |
| `StockDocumentLine` | id, document FK, item FK, source_location, destination_location, quantity | quantity > 0; location validity |
| `StockLedger` | id, document_line FK, item FK, warehouse FK, location FK, signed_qty, posted_at, sequence | immutable; unique posting event |
| `StockBalance` | item FK, warehouse FK, location FK, quantity | unique tuple; transactional cache of ledger |
| `StockCount` | id, number, warehouse, location, snapshot_at, status, approver | unique number |
| `StockCountLine` | count FK, item FK, snapshot_qty, counted_qty, variance | unique count-item-location |
| `AuditLog` | id, actor, action, entity, entity_id, before, after, created_at | append-only |
| `DocumentSequence` | document_type, year, next_number | unique type-year; locked allocation |

**Field audit standar semua master/dokumen:** `entry_date`, `entry_by`, `update_date`, `update_by` (Django timezone-aware; `django-crum` atau middleware current user). Gunakan `PROTECT` pada relasi referensi historis. `StockLedger` sumber kebenaran, `StockBalance` materialized transactional cache yang dapat direkonsiliasi. Seluruh pergerakan dibuat dalam `transaction.atomic()` dengan `select_for_update()` untuk baris saldo; tentukan lock order deterministik untuk transfer. Gunakan decimal untuk qty (mis. `Decimal(18,4)`), bukan float.

## 10. URL Structure
| URL | Method | Fungsi |
|---|---|---|
| `/login/`, `/logout/` | GET/POST | Autentikasi |
| `/` | GET | Dashboard |
| `/master/item/`, `/master/item/add/`, `/master/item/<id>/`, `/master/item/<id>/update/` | GET/POST | Master barang |
| `/master/warehouse/`, `/master/location/`, `/master/unit/`, `/master/category/`, `/master/partner/` | GET/POST | Master data |
| `/inventory/stock/`, `/inventory/ledger/` | GET | Saldo dan kartu stok |
| `/warehouse/receipt/`, `/warehouse/issue/`, `/warehouse/transfer/`, `/warehouse/adjustment/` | GET/POST | Index transaksi |
| `/warehouse/<type>/add/`, `/warehouse/<type>/<id>/` | GET/POST | Form dan detail |
| `/warehouse/<type>/<id>/submit/`, `/approve/`, `/reject/`, `/post/`, `/cancel/` | POST | State transitions |
| `/warehouse/stock-count/`, `/warehouse/stock-count/<id>/` | GET/POST | Stock opname |
| `/reports/<report>/`, `/reports/<report>/export/` | GET | Laporan |
| `/api/v1/items/search/`, `/api/v1/stock/availability/` | GET | Select2 dan pengecekan stok |
| `/master/<entity>/data/` | GET | JSON server-side DataTables |
| `/settings/audit-log/` | GET | Audit trail |

Semua `<id>` merupakan parameter URL Django, bukan literal string; namespace route konsisten dengan pola proyek referensi. Mutasi menggunakan POST, bukan GET.

## 11. User Stories & Acceptance Criteria
| ID | Story | Acceptance Criteria |
|---|---|---|
| US-001 | Sebagai admin saya login | Kredensial benar masuk dashboard; salah ditolak; CSRF dan session aktif |
| US-002 | Sebagai admin saya mengelola SKU | SKU unik, validasi wajib, item historis hanya dinonaktifkan |
| US-003 | Sebagai petugas saya menerima barang | Draft -> approval -> post; stok naik tepat satu kali; bukti tersedia |
| US-004 | Sebagai petugas saya mengeluarkan barang | Stok cukup diverifikasi saat posting; stok berkurang tepat sekali |
| US-005 | Sebagai supervisor saya memindahkan barang | Dua ledger berlawanan, net total perusahaan nol, atomic |
| US-006 | Sebagai supervisor saya adjustment stok | Reason wajib; approval; delta tercatat; tanpa saldo negatif |
| US-007 | Sebagai petugas saya opname | Snapshot, hitung, review variance, approval, post adjustment |
| US-008 | Sebagai manajer saya memantau stok | Filter gudang dan export menampilkan saldo sesuai ledger |
| US-009 | Sebagai auditor saya memeriksa mutasi | Setiap ledger dapat ditelusuri ke dokumen, user, waktu |
| US-010 | Sebagai admin saya mengatur akses | User tanpa izin tidak dapat mengakses endpoint walau menebak URL |
| US-011 | Sebagai admin saya import barang | Preview mapping, validasi duplikat, error per baris |
| US-012 | Sebagai petugas saya membatalkan draft | Cancel tercatat, tidak memengaruhi stok |

### Contoh Acceptance Test kritikal
1. Dua user bersamaan mengeluarkan 8 unit dari saldo 10: hanya satu posting sukses; saldo tidak negatif.
2. Klik tombol Post dua kali / retry HTTP: ledger tidak terduplikasi.
3. Transfer 5 unit A -> B gagal pada sisi B: rollback keduanya; total stok tidak berubah.
4. User hanya berhak Gudang A membuka URL Gudang B: HTTP 403.
5. Perubahan saldo selama opname: sistem menampilkan konflik dan memerlukan rekonsiliasi sebelum post.
6. Reversal dokumen posted membuat mutasi penyeimbang, dokumen asli tetap utuh.

## 12. Non-Functional Requirements
| Area | Target awal |
|---|---|
| Performance | p95 halaman daftar < 2 detik untuk 10.000 SKU / 100.000 ledger (target uji, bukan jaminan) |
| Scalability | Server-side pagination, query indexing, asynchronous export besar |
| Security | HTTPS, CSRF, secure cookies, permission server-side, throttling login, input validation |
| Data integrity | Atomic posting, row locks, immutable ledger, idempotent posting, DB constraints |
| Backup | Backup database harian + media; retensi 7 harian/4 mingguan/3 bulanan; uji restore bulanan |
| RPO/RTO | RPO 24 jam, RTO 8 jam (target awal untuk disepakati) |
| Accessibility | Keyboard navigation, label form, kontras cukup, feedback error terbaca |
| Localization | Bahasa Indonesia, WIB, tanggal DD/MM/YYYY, angka lokal |
| Observability | Structured log, exception monitoring, request IDs, alert backup gagal |
| Testing | Unit tests untuk saldo/approval; integration tests transaksi; UAT skenario kritikal |

## 13. Deployment & Architecture
```text
Browser -> Nginx HTTPS -> Gunicorn -> Django Apps -> MySQL
                                   |-> Media storage
                                   |-> Background jobs (fase 2)
```
Aplikasi Django dipisah ke `accounts`, `masters`, `inventory`, `warehouse`, `stock_count`, `reports`, `core`. Secrets dari environment, migration versioned, Docker Compose untuk staging/production, health checks, database tidak dibuka ke publik. Pisahkan staging dan production.

## 14. Roadmap & Prioritas
| Fase | Prioritas | Deliverables | Exit criteria |
|---|---|---|---|
| 0 — Foundation | P0 | Django project, theme Soft UI, auth, RBAC, master user | Login & permission test lulus |
| 1 — Inventory Core | P0 | Barang, gudang/lokasi, saldo & ledger | Rekonsiliasi saldo lulus |
| 2 — Operations | P0 | Receipt, issue, transfer, adjustment, approval | Concurrent posting tests lulus |
| 3 — Control | P0 | Opname, laporan, PDF, audit | UAT operasional lulus |
| 4 — Productivity | P1 | Import wizard, notifikasi, dashboard lanjut | Pilot 1 gudang selesai |
| 5 — Advanced | P2 | Barcode scan, lot/expiry, reservation, picking, ERP integration | Scope baru disetujui |

## 15. Risiko, Asumsi & Pertanyaan Terbuka
| Item | Risiko/keputusan yang dibutuhkan |
|---|---|
| Video referensi | Harus divalidasi manual; isi video belum dapat diakses sehingga pemetaan fitur belum terkonfirmasi |
| Jenis barang | Apakah perlu serial number, batch, expired date, ukuran/varian? |
| Banyak gudang | Apakah transfer memerlukan in-transit dan penerimaan terpisah? |
| Approval | Apakah semua dokumen wajib supervisor atau hanya nominal/jenis tertentu? |
| Integrasi | Apakah terhubung dengan Odoo, pembelian, penjualan, atau akuntansi? |
| Valuasi | Apakah dibutuhkan FIFO/average costing? Tidak termasuk MVP |
| Barcode | Apakah hardware scanner sudah tersedia dan format label ditentukan? |
| Initial stock | Harus ada cutover opening balance yang diaudit sebelum go-live |
| Satuan | Jika beli karton dan keluar pcs, multi-UOM perlu diprioritaskan |
| Volume | Target user bersamaan, SKU, lokasi, transaksi/hari perlu dikonfirmasi |

## 16. Definition of Done
- Semua P0 selesai dan telah melalui code review.
- Test suite transaksi kritikal, concurrent posting, RBAC, audit, dan rollback lulus.
- UAT dengan data sampel realistis: penerimaan -> transfer -> pengeluaran -> opname -> laporan.
- Dokumentasi setup, migrasi, backup/restore, dan manual user tersedia.
- Tidak ada bug kritikal terbuka; sign-off dari pemilik proses gudang.

## 17. Traceability & Referensi
- `PRD_SEKOLAH_ISLAM.md`: struktur PRD, stack Django/MySQL, RBAC per menu, master CRUD, audit, import/export.
- `PRODUCT_SPEC_SEKOLAH_ISLAM.md`: gaya user stories, acceptance criteria, validasi, endpoint, navigasi, error handling.
- Video yang diberikan pengguna: https://www.youtube.com/watch?v=4veWoiL87kI&t=1090s — **belum terverifikasi**.
- Setelah transkrip atau ringkasan video tersedia, lakukan gap analysis dan revisi PRD v1.1 sebelum pengembangan.

---
**End of PRD — KSI Warehouse v1.0**


---

## 18. Addendum Revisi Berdasarkan Video (v2.0)

### 18.1 Peta bukti visual video
| Waktu perkiraan | Materi yang tampak | Dampak requirement |
|---|---|---|
| 03:00 | Tantangan: barang sulit ditemukan, ketergantungan pada personel tertentu, lokasi tidak terstruktur | Kewajiban lokasi fisik dan histori mutasi |
| 06:00–09:00 | Solusi Odoo Inventory dan layar master produk | Master barang dengan identitas dan barcode |
| 12:00–18:00 | Manajemen lokasi, hierarki lokasi, daftar warehouse, cetak label barcode lokasi | Hirarki gudang–zona–rak–bin; label lokasi |
| 21:00–27:00 | Goods Receipt Management, receiving/staging, validasi penerimaan dan dokumen transfer | Penerimaan bertahap dengan validasi fisik |
| 30:00–33:00 | Tampilan scanner barcode dan proses validasi jumlah | Scan-to-confirm, selisih dan jejak pemindaian |
| 39:00–45:00 | Operasi transfer, inventory report, pergerakan internal | Transfer lokasi dan audit ledger |
| 48:00–57:00 | Delivery Management, skema pick–pack–delivery, barcode produk dan lokasi, dokumen pergerakan | Pengiriman multi-tahap dan bukti serah terima |
| 60:00–66:00 | Pengaturan tipe operasi dan daftar transaksi pergerakan | Konfigurasi workflow per gudang, monitoring status |

**Klasifikasi:** tabel di atas merupakan pengamatan visual; tidak mengklaim rincian dialog atau aturan sistem yang tidak terlihat jelas. Contoh kode barang, identitas perusahaan dalam demo, dan detail konfigurasi Odoo bukan kewajiban produk KSI Warehouse.

### 18.2 Requirement baru/diubah
| ID | Requirement | Prioritas | Asal |
|---|---|---|---|
| FR-LOC-10 | Struktur lokasi bertingkat: Gudang > Zona > Rak > Bin (fleksibel), lokasi bertipe storage/receiving/staging/packing/dispatch | P0 | Visual video + adaptasi |
| FR-LOC-11 | Kode lokasi unik per gudang; barcode lokasi unik secara sistem; cetak label PDF massal dan individual | P0 | Visual video |
| FR-LOC-12 | Tampilan pohon lokasi, filter stok per lokasi, pencarian barang dari kode/barcode | P0 | Visual video |
| FR-SCAN-10 | Input scanner keyboard-wedge di web, dengan fokus scan, umpan balik berhasil/gagal, pencegahan duplikasi | P0 | Visual video + rancangan |
| FR-SCAN-11 | Scan produk dan scan lokasi untuk mengonfirmasi pemindahan; kuantitas scan tidak boleh melampaui sisa tanpa izin supervisor | P0 | Visual video + rancangan |
| FR-RCV-10 | Alur configurable **1 tahap** (receive langsung ke stok) atau **2 tahap** (receive ke Receiving Area, lalu putaway ke Storage) | P0 | Video menampilkan receiving/staging; opsi adalah rancangan |
| FR-RCV-11 | Catat expected, received, accepted, rejected/damaged; validasi selisih dan alasan | P0 | Usulan kontrol anti-fraud |
| FR-RCV-12 | Petugas receiving dan petugas putaway dapat berbeda; audit pelaksana setiap tahap | P0 | Usulan kontrol anti-fraud |
| FR-DEL-10 | Alur configurable **1 tahap** (issue langsung) atau **3 tahap** (Pick → Pack → Dispatch/Delivery) | P0 | Visual video + adaptasi |
| FR-DEL-11 | Picking list dengan sumber bin, scan barang + bin, hasil pick, selisih dan alasan | P0 | Visual video + rancangan |
| FR-DEL-12 | Packing checklist, jumlah kemasan, identitas packer dan waktu konfirmasi | P1 | Visual video + rancangan |
| FR-DEL-13 | Dispatch validation, surat jalan, identitas penerima/kurir, bukti serah terima opsional | P1 | Visual video + rancangan |
| FR-FRAUD-10 | Segregation of duties: pembuat tidak dapat approve dokumen sendiri pada workflow yang mewajibkan approval | P0 | Usulan anti-fraud |
| FR-FRAUD-11 | Posted immutable, reversal dengan referensi dan approval; tanpa hapus fisik dokumen posted | P0 | Usulan anti-fraud |
| FR-FRAUD-12 | Audit log mencatat before/after, pelaku, waktu, sumber lokasi, tujuan, qty, alasan, perangkat/IP bila tersedia | P0 | Usulan anti-fraud |
| FR-FRAUD-13 | Alert untuk selisih receiving, overpick, penyesuaian stok, pembatalan, dan transfer tidak selesai | P1 | Usulan anti-fraud |
| FR-OPS-10 | Konfigurasi operation type per gudang: receipt, internal transfer, delivery, dan lokasi default setiap tahap | P1 | Visual video + adaptasi |

### 18.3 Flow penerimaan 2 tahap
```text
Draft Receipt → Submit → Approve (jika disyaratkan)
  → Receiving: scan produk + qty; posting ke RECEIVING
  → Putaway Task: scan lokasi asal + produk + bin tujuan
  → Validasi putaway → posting RECEIVING → STORAGE
  → Completed
```
- Receipt dan putaway menghasilkan **pergerakan ledger terpisah**; tidak boleh menambah stok dua kali.
- Barang di receiving dapat ditandai `quarantine` jika rusak/selisih dan tidak masuk available stock untuk picking.
- Putaway parsial diperbolehkan; sisa tetap terlihat sebagai pending receiving.
- Perbedaan expected vs actual harus disertai alasan dan dapat membutuhkan approval berdasarkan threshold.

### 18.4 Flow pengiriman 3 tahap
```text
Draft Delivery → Submit → Reserve stock
  → Picking Task (scan bin + produk + qty)
  → Packing Task (cek barang/qty, kemasan)
  → Dispatch Validation (surat jalan, serah terima)
  → Completed
```
- Reservasi stok mengurangi **available** tetapi bukan **on-hand**; perpindahan ke staging/packing diposting sebagai internal movement.
- Stok keluar dari kepemilikan gudang ketika dispatch terkonfirmasi; kegagalan packing tidak boleh mengurangi stok dua kali.
- Partial pick/partial dispatch harus menampilkan sisa kuantitas dan status yang dapat dilanjutkan.
- Semua langkah mencatat operator, timestamp dan sumber scan.

### 18.5 Kontrol pencegahan fraud
1. **Tidak boleh mengubah angka stok langsung:** semua saldo berasal dari ledger posted.
2. **Pemisahan tugas:** create, receive, putaway, approve adjustment, dispatch dapat dipisahkan berdasarkan izin.
3. **Bukti fisik:** scan lokasi dan produk untuk tahapan yang dikonfigurasi wajib scan; input manual membutuhkan alasan dan permission khusus.
4. **Audit immutable:** perubahan draft tercatat, dokumen posted hanya dapat dibalik melalui reversal.
5. **Rekonsiliasi:** dashboard menampilkan pending putaway, pending pick, stok quarantine, dan selisih opname.
6. **Atomic posting:** transaksi dan saldo diproses dalam database transaction dengan locking agar tidak terjadi double posting atau oversell.
7. **Threshold approval:** nominal/kuantitas adjustment atau selisih dapat diatur; default threshold perlu keputusan bisnis.

### 18.6 Tambahan entitas data
| Entitas | Field utama | Constraint |
|---|---|---|
| `StorageLocation` (revisi) | warehouse, parent, type, code, barcode, active | unique warehouse+code, unique barcode; larang circular parent |
| `OperationType` | warehouse, code, name, flow_mode, default_source, default_destination | unique warehouse+code |
| `WarehouseTask` | document, type(receive/putaway/pick/pack/dispatch), assignee, status, started_at, completed_at | state machine terkontrol |
| `WarehouseTaskLine` | task, item, source_location, destination_location, expected_qty, processed_qty | processed_qty >= 0 |
| `ScanEvent` | task_line, scan_type, raw_code, item/location, operator, timestamp, result | append-only |
| `StockReservation` | document_line, item, location, reserved_qty, status | qty positif, tidak melebihi available |
| `StockException` | document/task, type, expected_qty, actual_qty, reason, approved_by | reason wajib untuk variance |
| `StockPackage` | packing_task, package_no, packed_by, packed_at | unique package_no |
| `DispatchProof` | dispatch_task, recipient, carrier, handed_over_at, attachment | akses sesuai izin |

### 18.7 UI tambahan (tetap Soft UI Dashboard)
- **Lokasi:** tree view di panel kiri, detail stok dan barcode di panel kanan; tombol *Cetak Label*.
- **Receiving:** card ringkasan expected/received/variance, tabel item, panel scan yang fokus otomatis, aksi *Konfirmasi Penerimaan*.
- **Putaway:** daftar tugas berdasarkan gudang, scan lokasi asal/tujuan dan barang, progress per baris.
- **Picking:** picking list berdasarkan bin, progres scan dan indikator short-pick.
- **Packing:** checklist barang, jumlah paket, ringkasan hasil pick.
- **Dispatch:** verifikasi final, cetak surat jalan dan konfirmasi serah terima.
- **Monitoring:** tab *Pending Receiving*, *Pending Putaway*, *Pending Picking*, *Pending Packing*, *Pending Dispatch*, *Exceptions*.

### 18.8 Revisi roadmap
- **MVP/P0:** master lokasi + label barcode; receiving 1/2 tahap; putaway; picking; delivery 1/3 tahap (packing/dispatch minimal); scan barang/lokasi; ledger, reservation, audit dan RBAC.
- **P1:** exception approval bertingkat, paket dan bukti dispatch lengkap, alert otomatis, laporan produktivitas operator.
- **P2:** handheld offline, serial/lot, integrasi PO/SO, advanced route/slotting.

### 18.9 Keputusan yang harus divalidasi pemilik produk
- Apakah setiap gudang memakai receipt 2 tahap dan delivery 3 tahap, atau configurable?
- Apakah scanner berupa keyboard-wedge USB/Bluetooth saja, atau kamera ponsel juga?
- Apakah semua lokasi harus diberi barcode dan scan diwajibkan untuk setiap movement?
- Apakah partial receipt/delivery diperbolehkan dan bagaimana kebijakan backorder?
- Berapa threshold approval untuk selisih dan adjustment?
- Apakah proof of delivery memerlukan tanda tangan/foto/geolocation? **Tidak terkonfirmasi dari video.**
