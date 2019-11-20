from django import template
from hurry.filesize import size

register = template.Library()


@register.filter
def human_size(byte_size):
    s = size(byte_size)
    return f"{s[:-1]} {s[-1]}B"
