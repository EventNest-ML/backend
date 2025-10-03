from django import template
from django.utils import timezone
from datetime import datetime

register = template.Library()

@register.filter
def split(value, arg):
    """Split a string by the given delimiter"""
    if value:
        return value.split(arg)
    return []

@register.filter
def replace(value, arg):
    """Replace characters in a string"""
    if value and arg:
        old, new = arg.split(',') if ',' in arg else (arg, ' ')
        return value.replace(old, new)
    return value