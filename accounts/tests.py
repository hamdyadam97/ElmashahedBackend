"""
Tests for Accounts App
اختبارات تطبيق الحسابات
"""
from django.test import TestCase, Client as TestClient
from django.urls import reverse
from django.contrib.auth import get_user_model

from institutes.models import Institute

User = get_user_model()


class UserModelTests(TestCase):
    """اختبارات نموذج المستخدم"""
    
    def setUp(self):
        self.institute = Institute.objects.create(
            name='Test Institute',
            code='TEST001',
            license_number='LIC001',
            address='Test Address',
            city='Test City',
            region='Test Region',
            phone='1234567890'
        )
    
    def test_create_admin_user(self):
        """اختبار إنشاء مستخدم Admin"""
        user = User.objects.create_user(
            username='admin_test',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.assertTrue(user.is_admin())
        self.assertFalse(user.is_employee())
    
    def test_create_employee_user(self):
        """اختبار إنشاء موظف"""
        user = User.objects.create_user(
            username='employee_test',
            password='testpass123',
            role=User.Role.EMPLOYEE,
            institute=self.institute
        )
        self.assertTrue(user.is_employee())
        self.assertEqual(user.institute, self.institute)
    
    def test_create_branch_manager(self):
        """اختبار إنشاء مدير فرع"""
        user = User.objects.create_user(
            username='manager_test',
            password='testpass123',
            role=User.Role.BRANCH_MANAGER,
            managed_institute=self.institute
        )
        self.assertTrue(user.is_branch_manager())
        self.assertEqual(user.managed_institute, self.institute)
    
    def test_get_managed_institutes_admin(self):
        """اختبار الحصول على المعاهد لـ Admin"""
        admin = User.objects.create_user(
            username='admin',
            password='testpass123',
            role=User.Role.ADMIN
        )
        institutes = admin.get_managed_institutes()
        self.assertIsNotNone(institutes)
    
    def test_get_managed_institutes_employee(self):
        """اختبار الحصول على المعهد لـ Employee"""
        employee = User.objects.create_user(
            username='employee',
            password='testpass123',
            role=User.Role.EMPLOYEE,
            institute=self.institute
        )
        result = employee.get_managed_institutes()
        self.assertEqual(result, self.institute)


class AuthenticationTests(TestCase):
    """اختبارات المصادقة"""
    
    def setUp(self):
        self.client = TestClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role=User.Role.EMPLOYEE
        )
    
    def test_login_page_loads(self):
        """اختبار تحميل صفحة تسجيل الدخول"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
    
    def test_successful_login(self):
        """اختبار تسجيل الدخول بنجاح"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
    
    def test_failed_login(self):
        """اختبار تسجيل الدخول الفاشل"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Stay on page
    
    def test_dashboard_requires_login(self):
        """اختبار أن Dashboard تتطلب تسجيل دخول"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Login and try again
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)


class PermissionMixinsTests(TestCase):
    """اختبارات Mixins الصلاحيات"""
    
    def setUp(self):
        self.client = TestClient()
        
        self.admin = User.objects.create_user(
            username='admin',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.employee = User.objects.create_user(
            username='employee',
            password='testpass123',
            role=User.Role.EMPLOYEE
        )
    
    def test_admin_required_view_blocks_employee(self):
        """اختبار أن AdminRequiredMixin يمنع الموظف"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_admin_required_view_allows_admin(self):
        """اختبار أن AdminRequiredMixin يسمح للـ Admin"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('accounts:user_list'))
        # Should either show list or redirect if no users
        self.assertIn(response.status_code, [200, 302])


class DashboardTests(TestCase):
    """اختبارات Dashboard"""
    
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
    
    def test_admin_dashboard_context(self):
        """اختبار context الخاص بـ Admin"""
        admin = User.objects.create_user(
            username='admin',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_institutes', response.context)
    
    def test_employee_dashboard_context(self):
        """اختبار context الخاص بـ Employee"""
        employee = User.objects.create_user(
            username='employee',
            password='testpass123',
            role=User.Role.EMPLOYEE,
            institute=self.institute
        )
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
