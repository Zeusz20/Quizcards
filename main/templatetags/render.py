from django.template import Library

register = Library()


@register.simple_tag
def render(tag, **kwargs):
    """Template tag to add additional attributes to html tags."""

    attrs = tag.field.widget.attrs
    for key, value in kwargs.items():
        attrs[key] = value
    return tag
