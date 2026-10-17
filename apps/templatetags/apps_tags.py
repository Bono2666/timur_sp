from django import template
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
