from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def unread_notifications(context):
    user = context.get('user')
    if not user or not user.is_authenticated:
        return 0
    return user.lms_notifications.filter(is_read=False).count()


@register.filter
def get_item(mapping, key):
    try:
        return mapping.get(key)
    except AttributeError:
        return None


@register.filter
def grade_class(value):
    if value >= 8:
        return 'grade-high'
    if value >= 5:
        return 'grade-mid'
    return 'grade-low'


@register.filter
def get_field_value(form, student_id):
    return form[f'grade_{student_id}']


@register.filter
def get_field_att(form, student_id):
    return form[f'att_{student_id}']


@register.filter
def get_field_comment(form, student_id):
    return form[f'comment_{student_id}']
