
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
# استيراد الموديل الصحيح للأذونات
from .models import PermissionSlip


@receiver(post_save, sender=PermissionSlip)
def send_auto_email(sender, instance, created, **kwargs):
    if created:
        try:
            subject = f"تأكيد إصدار إذن تسجيل: {instance.client.full_name}"

            # التعديل هنا: نستخدم الإيميل الموثق في Brevo
            from_email = 'hamdy.adam@ararhni.com'
            to = instance.client.email

            if not to:
                print("فشل الإرسال: العميل ليس لديه بريد إلكتروني مسجل.")
                return

            site_url = "http://127.0.0.1:8000"

            html_content = render_to_string('emails/permission_email.html', {
                'obj': instance,
                'site_url': site_url
            })
            text_content = f"مرحباً {instance.client.full_name}، تم إصدار إذن تسجيلك رقم {instance.permission_number}."

            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            print(f"✅ تم إرسال الإيميل بنجاح إلى {to}")
        except Exception as e:
            print(f"❌ حدث خطأ أثناء إرسال الإيميل: {str(e)}")