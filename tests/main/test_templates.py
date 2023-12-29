import os

from django.conf import settings
from django.template import Template


def test_compile_templates():
    """
    Ensure that all templates can compile. This is not the same as anything
    actually working as intended; it avoids (for example) attempting to load
    invalid libraries.
    """
    for template_dir in settings.TEMPLATES[0]["DIRS"]:
        for basepath, dirs, filenames in os.walk(template_dir):
            for filename in filenames:
                path = os.path.join(basepath, filename)
                with open(path, "r") as f:
                    # This will fail if the template cannot compile
                    Template(f.read())
