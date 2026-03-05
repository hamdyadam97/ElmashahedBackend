from django.db import models

# Create your models here.
from django.db import models


# 1. مدير بيانات مخصص لفلترة المحذوف تلقائياً
class NonDeletedManager(models.Manager):
    def get_queryset(self):
        # هذا السطر هو السر: أي Queryset سيفلتر is_deleted=False تلقائياً
        return super().get_queryset().filter(is_deleted=False)


# 2. الموديل الأب (Abstract Model)
class BaseModel(models.Model):
    is_deleted = models.BooleanField(default=False, verbose_name="محذوف")

    # المدير الافتراضي يفلتر المحذوف
    objects = NonDeletedManager()
    # مدير إضافي إذا أردت الوصول لكل البيانات بما فيها المحذوفة
    all_objects = models.Manager()

    class Meta:
        abstract = True  # هذه تعني أن Django لن ينشئ جدولاً لهذا الموديل في قاعدة البيانات

    def soft_delete(self):
        """دالة الحذف الناعم"""
        self.is_deleted = True
        self.save()

    def restore(self):
        """دالة استعادة المحذوف"""
        self.is_deleted = False
        self.save()