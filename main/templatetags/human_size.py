import re

from django import template
from hurry.filesize import size

register = template.Library()


@register.filter
def human_size(byte_size):
    s = size(byte_size)
    return re.sub(r"(\d+)(\w+)", r"\1 \2", s)
