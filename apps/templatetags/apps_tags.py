import re

from django import template
from django.utils.safestring import mark_safe
from decimal import Decimal, InvalidOperation

register = template.Library()


@register.filter
def qty(value):
    """Format kuantitas stok: buang nol desimal di belakang.

    72.0000 -> '72', 7.5000 -> '7.5', 0.2500 -> '0.25'.
    Nilai kosong (None/'') -> '' (gabungkan dengan |default:'-' untuk tampilan).
    """
    if value in (None, ''):
        return ''
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return value
    if d == d.to_integral_value():
        d = d.quantize(Decimal('1'))
    else:
        d = d.normalize()
    return format(d, 'f')


@register.filter
def barcode_svg(value):
    """Render barcode Code128 sebagai SVG inline (untuk cetak label sticker).

    Koordinat mm diubah menjadi user-unit + viewBox agar bisa diskalakan CSS.
    Nilai kosong / tak ter-render -> '' (aman ditempel inline).
    """
    code = (value or '').strip()
    if not code:
        return ''
    try:
        import barcode as _barcode
        from barcode.writer import SVGWriter
        cls = _barcode.get_barcode_class('code128')
        svg = cls(code, writer=SVGWriter()).render(
            writer_options={'write_text': False, 'module_width': 0.25,
                            'module_height': 6, 'quiet_zone': 2})
        if isinstance(svg, bytes):
            svg = svg.decode('utf-8')
        # buang prolog XML/DOCTYPE agar aman inline di HTML
        svg = svg[svg.find('<svg'):]
        # mm -> user-unit biasa, lalu tambahkan viewBox agar bisa diskalakan CSS
        svg = re.sub(r'([0-9.]+)mm', r'\1', svg)
        m = re.search(r'width="([\d.]+)" height="([\d.]+)"', svg)
        if m:
            svg = re.sub(r'width="[\d.]+" height="[\d.]+"',
                         'viewBox="0 0 %s %s" preserveAspectRatio="xMidYMid meet"'
                         % (m.group(1), m.group(2)), svg, count=1)
        return mark_safe(svg)
    except Exception:
        return ''
