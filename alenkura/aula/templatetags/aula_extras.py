from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
    """Safe dictionary/QueryDict lookup in templates."""
    if mapping is None:
        return ""
    try:
        return mapping.get(key, "")
    except Exception:  # pragma: no cover - fallback for uncommon mappings
        try:
            return mapping[key]
        except Exception:
            return ""


@register.filter
def split_lines_default(value):
    """Split text into non-empty lines; return [''] if empty."""
    if not value:
        return [""]
    lines = [line for line in str(value).splitlines() if line.strip() or line == ""]
    return lines or [""]


@register.filter
def index(sequence, idx):
    """Get element by index or return empty string."""
    try:
        return sequence[idx]
    except Exception:
        return ""
