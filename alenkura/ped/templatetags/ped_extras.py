from django import template

register = template.Library()


@register.filter(name="get_value")
def get_value(data, key):
    """Extrae un valor dinámico desde un dict o QueryDict en los templates."""
    if not key:
        return ""
    getter = getattr(data, "get", None)
    if callable(getter):
        return getter(key, "")
    if isinstance(data, dict):
        return data.get(key, "")
    return ""


@register.filter(name="get_decreto_nombre")
def get_decreto_nombre(decretos, decreto_id):
    """Devuelve el nombre del decreto seleccionado para mostrarlo en la tabla."""
    try:
        decreto_id = int(decreto_id)
    except (TypeError, ValueError):
        return "Aún no seleccionado."

    if hasattr(decretos, "filter"):
        decreto = decretos.filter(pk=decreto_id).first()
    elif isinstance(decretos, dict):
        decreto = decretos.get(decreto_id)
    else:
        decreto = None

    return decreto.nombre if decreto else "Aún no seleccionado."


@register.simple_tag(name="field_name")
def field_name(prefix, identifier):
    """Concatena prefijo + identificador para reutilizar en los formularios."""
    return f"{prefix}{identifier}"


@register.simple_tag(name="checked_option")
def checked_option(form_data, field_name, value):
    """
    Determina si un checkbox debe mostrarse como seleccionado según el POST previo.

    Devuelve True si `value` está dentro de los valores enviados para `field_name`.
    """
    str_value = str(value)
    values = []
    getlist = getattr(form_data, "getlist", None)
    if callable(getlist):
        values = [str(v) for v in getlist(field_name)]
    elif isinstance(form_data, dict):
        current = form_data.get(field_name)
        if isinstance(current, (list, tuple)):
            values = [str(v) for v in current]
        elif current is not None:
            values = [str(current)]
    return str_value in values
