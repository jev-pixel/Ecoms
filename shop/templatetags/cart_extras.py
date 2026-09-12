from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply value by arg"""
    return value * arg
