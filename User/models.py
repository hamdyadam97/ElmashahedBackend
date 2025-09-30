import uuid
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager as DjangoUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.functional import cached_property
from django.conf import settings
def validate_number_id_user(value):
    if not value.isdigit():
        raise ValidationError(_("ID must contain digits only."))
    if len(value) != 10:
        raise ValidationError(_("ID must be exactly 10 digits."))
    if not value.startswith('1') and not value.startswith('2'):
        raise ValidationError(_("ID must start with 1 (Citizen) or 2 (Resident)."))
    return value


def upload_to_profile_pic(instance, filename):
    return f'uploads/profile/{uuid.uuid4()}/{filename}'


from django.contrib.auth.models import BaseUserManager

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, full_name, identity_number, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        if not identity_number:
            raise ValueError("The Identity Number must be set")

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            full_name=full_name,
            identity_number=identity_number,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, identity_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, full_name, identity_number, password, **extra_fields)



class User(AbstractBaseUser, PermissionsMixin):
    BRANCH_CHOICES = [
        ('riyadh', 'فرع الرياض'),
        ('jeddah', 'فرع جدة'),
        ('dammam', 'فرع الدمام'),
    ]

    full_name = models.CharField(max_length=100)
    email = models.EmailField(_('email address'), unique=True)
    identity_number = models.CharField(
        max_length=10,
        unique=True,
        validators=[validate_number_id_user],
        help_text=_("Saudi ID or Iqama number (must start with 1 or 2).")
    )
    branch = models.CharField(max_length=50, choices=BRANCH_CHOICES, blank=True, null=True)
    profile_picture = models.ImageField(upload_to=upload_to_profile_pic, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()
    slug = models.SlugField(unique=True, blank=True, null=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'identity_number']

    @cached_property
    def token(self):
        return RefreshToken.for_user(self)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.full_name)
            if not base_slug:
                base_slug = slugify(self.email.split("@")[0])

            slug = base_slug
            counter = 1
            # نتأكد أنه unique
            while User.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()
    def __str__(self):
        return self.full_name


class Diploma(models.Model):
    name = models.CharField(max_length=255, verbose_name="اسم الدبلوم")
    date = models.DateField(auto_now_add=True, verbose_name="تاريخ إنشاء الدبلوم")

    def __str__(self):
        return self.name

class Client(models.Model):
    SECTOR_CHOICES = [
        ('government', 'حكومي'),
        ('private', 'خاص'),
        ('non_profit', 'غير ربحي'),
        ('education', 'تعليمي'),
        ('health', 'صحي'),
        ('tech', 'تقني'),
        ('finance', 'مالي'),
        ('trade', 'تجاري'),
        ('industry', 'صناعي'),
        ('services', 'خدمي'),
    ]
    AREA_CHOICES = [
        ('riyadh', 'الرياض'),
        ('makkah', 'مكة المكرمة'),
        ('madinah', 'المدينة المنورة'),
        ('qassim', 'القصيم'),
        ('eastern', 'المنطقة الشرقية'),
        ('asir', 'عسير'),
        ('tabuk', 'تبوك'),
        ('hail', 'حائل'),
        ('north_border', 'الحدود الشمالية'),
        ('jazan', 'جازان'),
        ('najran', 'نجران'),
        ('baha', 'الباحة'),
        ('jouf', 'الجوف'),
    ]
    name = models.CharField(max_length=255, verbose_name="الاسم")
    identity_number = models.CharField(max_length=10, verbose_name="رقم الهوية")
    phone_number = models.CharField(max_length=15, verbose_name="رقم الهاتف")
    email = models.EmailField(verbose_name="الإيميل")
    sector = models.CharField(
        max_length=50,
        choices=SECTOR_CHOICES,
        verbose_name="القطاع"
    )

    area = models.CharField(
        max_length=50,
        choices=AREA_CHOICES,
        verbose_name="المنطقة"
    )
    diplomas = models.ManyToManyField(
        Diploma,
        related_name="clients",
        blank=True,
        through='ClientDiploma'
    )

    created_at = models.DateTimeField(auto_now_add=True,null=True)
    updated_at = models.DateTimeField(auto_now=True,null=True)

    def __str__(self):
        return self.name


class ClientDiploma(models.Model):
    client = models.ForeignKey(Client, related_name="client_diplomas", on_delete=models.CASCADE)
    diploma = models.ForeignKey(Diploma, on_delete=models.CASCADE,)
    added_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="added_clients",
        verbose_name="تم الإضافة بواسطة"
    )
    class Meta:
        unique_together = ('client', 'diploma')  # تمنع التكرار لنفس الدبلوم