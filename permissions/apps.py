from django.apps import AppConfig


class PermissionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'permissions'
    verbose_name = 'Permissions'

    def ready(self):
        import permissions.signals  # تأكدي أن المسار صحيح لملف السيجنالز

