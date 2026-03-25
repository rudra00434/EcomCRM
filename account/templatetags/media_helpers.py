from django import template
from django.urls import reverse


register = template.Library()


@register.filter
def media_fallback_url(field_file):
    name = getattr(field_file, "name", "")
    if not name:
        return ""
    return reverse("media_fallback", kwargs={"file_path": name})
