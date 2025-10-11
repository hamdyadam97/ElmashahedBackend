
import User.models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='الاسم')),
                ('identity_number', models.CharField(max_length=10, unique=True, verbose_name='رقم الهوية')),
                ('phone_number', models.CharField(max_length=15, verbose_name='رقم الهاتف')),
                ('email', models.EmailField(max_length=254, verbose_name='الإيميل')),
                ('sector', models.CharField(choices=[('government', 'حكومي'), ('private', 'خاص'), ('non_profit', 'غير ربحي'), ('education', 'تعليمي'), ('health', 'صحي'), ('tech', 'تقني'), ('finance', 'مالي'), ('trade', 'تجاري'), ('industry', 'صناعي'), ('services', 'خدمي')], max_length=50, verbose_name='القطاع')),
                ('area', models.CharField(choices=[('riyadh', 'الرياض'), ('makkah', 'مكة المكرمة'), ('madinah', 'المدينة المنورة'), ('qassim', 'القصيم'), ('eastern', 'المنطقة الشرقية'), ('asir', 'عسير'), ('tabuk', 'تبوك'), ('hail', 'حائل'), ('north_border', 'الحدود الشمالية'), ('jazan', 'جازان'), ('najran', 'نجران'), ('baha', 'الباحة'), ('jouf', 'الجوف')], max_length=50, verbose_name='المنطقة')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Diploma',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='اسم الدبلوم')),
                ('date', models.DateField(auto_now_add=True, verbose_name='تاريخ إنشاء الدبلوم')),
            ],
        ),
        migrations.CreateModel(
            name='ClientDiploma',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='User.client')),
                ('diploma', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='User.diploma')),
            ],
            options={
                'unique_together': {('client', 'diploma')},
            },
        ),
        migrations.AddField(
            model_name='client',
            name='diplomas',
            field=models.ManyToManyField(blank=True, related_name='clients', through='User.ClientDiploma', to='User.diploma'),
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('full_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
                ('identity_number', models.CharField(help_text='Saudi ID or Iqama number (must start with 1 or 2).', max_length=10, unique=True, validators=[User.models.validate_number_id_user])),
                ('branch', models.CharField(blank=True, choices=[('riyadh', 'فرع الرياض'), ('jeddah', 'فرع جدة'), ('dammam', 'فرع الدمام')], max_length=50, null=True)),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to=User.models.upload_to_profile_pic)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('slug', models.SlugField(blank=True, null=True, unique=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
            managers=[
                ('objects', User.models.UserManager()),
            ],
        ),
        migrations.AddField(
            model_name='client',
            name='added_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='added_clients', to=settings.AUTH_USER_MODEL, verbose_name='تم الإضافة بواسطة'),
        ),
    ]
