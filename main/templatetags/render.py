from django.template import Library

register = Library()


@register.simple_tag
def render(tag, **kwargs):
    attrs = tag.field.widget.attrs

    for key, value in kwargs.items():
        attrs[key] = value

    return tag
