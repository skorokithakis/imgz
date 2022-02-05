from django import template

register = template.Library()


traditional = [
    (1024**5, "P"),
    (1024**4, "T"),
    (1024**3, "G"),
    (1024**2, "M"),
    (1024**1, "K"),
    (1024**0, "B"),
]

alternative = [
    (1024**5, " PB"),
    (1024**4, " TB"),
    (1024**3, " GB"),
    (1024**2, " MB"),
    (1024**1, " KBbyte"),
    (1024**0, (" byte", " bytes")),
]

verbose = [
    (1024**5, (" petabyte", " petabytes")),
    (1024**4, (" terabyte", " terabytes")),
    (1024**3, (" gigabyte", " gigabytes")),
    (1024**2, (" megabyte", " megabytes")),
    (1024**1, (" kilobyte", " kilobytes")),
    (1024**0, (" byte", " bytes")),
]

iec = [
    (1024**5, "Pi"),
    (1024**4, "Ti"),
    (1024**3, "Gi"),
    (1024**2, "Mi"),
    (1024**1, "Ki"),
    (1024**0, ""),
]

si = [
    (1000**5, "P"),
    (1000**4, "T"),
    (1000**3, "G"),
    (1000**2, "M"),
    (1000**1, "K"),
    (1000**0, "B"),
]


def size(bytes: int, system=alternative) -> str:
    """
    Human-readable file size.
    """
    # Sometimes `bytes` is an empty string here, try to work around that.
    if not bytes:
        bytes = 0

    for factor, suffix in system:
        if bytes >= factor:
            break

    amount = "{0:.2f}".format(bytes / factor)

    if "." in amount:
        # Strip non-significant decimal digits (and the dot).
        integer, decimal = amount.split(".")
        amount = integer + ("." + decimal).rstrip("0.")

    if isinstance(suffix, tuple):
        # Select singular or plural.
        suffix = suffix[0] if amount == "1" else suffix[1]
    return amount + suffix


@register.filter
def human_size(byte_size):
    return size(byte_size)
