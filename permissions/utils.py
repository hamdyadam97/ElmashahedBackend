"""أدوات مشتركة لمنطق إصدار الأذونات - مشترك بين النظام الداخلي والبورتال العام"""


def find_blocking_active_permission(client, target_institute_id):
    """
    يرجع إذن نشط للعميل في معهد مختلف عن المعهد المستهدف (لو موجود)، وإلا None.
    وجود إذن زي ده يمنع إصدار إذن جديد لحد ما يتم إلغاؤه من المعهد صاحب الإذن الأصلي.
    """
    from .models import PermissionSlip

    return PermissionSlip.objects.filter(
        client=client, status='active'
    ).exclude(institute_id=target_institute_id).select_related(
        'institute', 'issued_by', 'referral_employee'
    ).order_by('-created_at').first()


def find_existing_permission(client, target_institute_id):
    """
    يرجع إذن نشط للعميل في نفس المعهد المستهدف (لو موجود)، وإلا None.
    يُستخدم عشان لو الطالب أصدر مشهد قبل كده من نفس الفرع، نوجّهه لمشهده
    الحالي بدل ما يصدر واحد جديد مكرر.
    """
    from .models import PermissionSlip

    return PermissionSlip.objects.filter(
        client=client, status='active', institute_id=target_institute_id
    ).select_related('institute').order_by('-created_at').first()


def existing_info(permission):
    """يبني بيانات صالحة للعرض عن مشهد سابق للطالب في نفس الفرع"""
    return {
        'permission_number': permission.permission_number,
        'institute_name': permission.institute.name,
        'issue_date': permission.issue_date.strftime('%Y-%m-%d') if permission.issue_date else '',
    }


def resolve_contact(permission):
    """يرجع (الاسم، رقم التليفون) للتواصل بخصوص إلغاء إذن قديم"""
    if permission.issued_by and permission.issued_by.phone:
        name = permission.issued_by.get_full_name() or permission.issued_by.username
        return name, permission.issued_by.phone

    if permission.referral_employee and permission.referral_employee.phone:
        name = permission.referral_employee.get_full_name() or permission.referral_employee.username
        return name, permission.referral_employee.phone

    return permission.institute.name, permission.institute.phone


def blocking_info(permission):
    """يبني رسالة/بيانات صالحة للعرض للمستخدم توضح سبب المنع وبيانات التواصل"""
    contact_name, contact_phone = resolve_contact(permission)
    return {
        'permission_number': permission.permission_number,
        'institute_name': permission.institute.name,
        'contact_name': contact_name,
        'contact_phone': contact_phone,
    }
