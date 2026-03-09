"""
Tests for Programs App
اختبارات تطبيق البرامج
"""
from django.test import TestCase, Client as TestClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, timedelta

from institutes.models import Institute
from clients.models import Client
from .models import ProgramCategory, Diploma, Course, ProgramRegistration

User = get_user_model()


class ProgramCategoryTests(TestCase):
    """اختبارات فئات البرامج"""
    
    def setUp(self):
        self.category = ProgramCategory.objects.create(
            name='Computer Science',
            type=ProgramCategory.Type.DIPLOMA,
            description='IT and programming courses'
        )
    
    def test_create_category(self):
        """اختبار إنشاء فئة"""
        self.assertEqual(self.category.name, 'Computer Science')
        self.assertEqual(self.category.type, ProgramCategory.Type.DIPLOMA)
    
    def test_category_str(self):
        """اختبار تمثيل الفئة نصياً"""
        self.assertIn('Computer Science', str(self.category))


class DiplomaTests(TestCase):
    """اختبارات الدبلومات"""
    
    def setUp(self):
        self.institute = Institute.objects.create(
            name='Test Institute',
            code='TEST001',
            license_number='LIC001',
            address='Test',
            city='Test',
            region='Test',
            phone='1234567890'
        )
        self.category = ProgramCategory.objects.create(
            name='IT',
            type=ProgramCategory.Type.DIPLOMA
        )
        self.diploma = Diploma.objects.create(
            name='Software Engineering',
            code='SE2024',
            description='Full stack development',
            institute=self.institute,
            category=self.category,
            duration_months=24,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=730),
            registration_start_date=date.today(),
            registration_end_date=date.today() + timedelta(days=30),
            fees=10000.00
        )
    
    def test_create_diploma(self):
        """اختبار إنشاء دبلومة"""
        self.assertEqual(self.diploma.name, 'Software Engineering')
        self.assertEqual(self.diploma.code, 'SE2024')
        self.assertEqual(self.diploma.duration_months, 24)
    
    def test_diploma_code_unique(self):
        """اختبار أن كود الدبلومة فريد"""
        with self.assertRaises(Exception):
            Diploma.objects.create(
                name='Another Diploma',
                code='SE2024',  # Same code
                institute=self.institute,
                duration_months=12,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=365)
            )
    
    def test_get_registered_clients_count(self):
        """اختبار عدد العملاء المسجلين"""
        count = self.diploma.get_registered_clients_count()
        self.assertEqual(count, 0)


class CourseTests(TestCase):
    """اختبارات الدورات"""
    
    def setUp(self):
        self.institute = Institute.objects.create(
            name='Test Institute',
            code='TEST001',
            license_number='LIC001',
            address='Test',
            city='Test',
            region='Test',
            phone='1234567890'
        )
        self.category = ProgramCategory.objects.create(
            name='Short Courses',
            type=ProgramCategory.Type.COURSE
        )
        self.course = Course.objects.create(
            name='Python Basics',
            code='PY101',
            description='Introduction to Python',
            institute=self.institute,
            category=self.category,
            duration_months=6,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=180),
            registration_start_date=date.today(),
            registration_end_date=date.today() + timedelta(days=30),
            fees=2000.00
        )
    
    def test_create_course(self):
        """اختبار إنشاء دورة"""
        self.assertEqual(self.course.name, 'Python Basics')
        self.assertEqual(self.course.code, 'PY101')
        self.assertEqual(self.course.duration_months, 6)


class ProgramRegistrationTests(TestCase):
    """اختبارات تسجيل البرامج"""
    
    def setUp(self):
        self.institute = Institute.objects.create(
            name='Test Institute',
            code='TEST001',
            license_number='LIC001',
            address='Test',
            city='Test',
            region='Test',
            phone='1234567890'
        )
        self.employee = User.objects.create_user(
            username='employee',
            password='testpass123',
            role=User.Role.EMPLOYEE,
            institute=self.institute
        )
        self.client_obj = Client.objects.create(
            first_name='Test',
            last_name='Client',
            full_name='Test Client',
            national_id='REG001',
            gender='male',
            birth_date='1990-01-01',
            phone='0123456789',
            address='Test',
            institute=self.institute,
            registered_by=self.employee
        )
        self.diploma = Diploma.objects.create(
            name='Test Diploma',
            code='DIP001',
            institute=self.institute,
            duration_months=24,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=730)
        )
    
    def test_create_registration(self):
        """اختبار إنشاء تسجيل"""
        registration = ProgramRegistration.objects.create(
            client=self.client_obj,
            diploma=self.diploma,
            registered_by=self.employee,
            status=ProgramRegistration.Status.CONFIRMED
        )
        
        self.assertEqual(registration.client, self.client_obj)
        self.assertEqual(registration.diploma, self.diploma)
        self.assertEqual(registration.get_program_type(), 'diploma')
    
    def test_get_program(self):
        """اختبار الحصول على البرنامج"""
        registration = ProgramRegistration.objects.create(
            client=self.client_obj,
            diploma=self.diploma,
            registered_by=self.employee
        )
        
        program = registration.get_program()
        self.assertEqual(program, self.diploma)


class ProgramViewsTests(TestCase):
    """اختبارات Views البرامج"""
    
    def setUp(self):
        self.client = TestClient()
        self.institute = Institute.objects.create(
            name='Test Institute',
            code='TEST001',
            license_number='LIC001',
            address='Test',
            city='Test',
            region='Test',
            phone='1234567890'
        )
        self.employee = User.objects.create_user(
            username='employee',
            password='testpass123',
            role=User.Role.EMPLOYEE,
            institute=self.institute
        )
        self.diploma = Diploma.objects.create(
            name='Test Diploma',
            code='DIP001',
            institute=self.institute,
            duration_months=24,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=730)
        )
    
    def test_diploma_list_requires_login(self):
        """اختبار أن قائمة الدبلومات تتطلب تسجيل دخول"""
        response = self.client.get(reverse('programs:diploma_list'))
        self.assertEqual(response.status_code, 302)
    
    def test_diploma_list_accessible_to_employee(self):
        """اختبار أن الموظف يمكنه رؤية الدبلومات"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('programs:diploma_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.diploma, response.context['diplomas'])
