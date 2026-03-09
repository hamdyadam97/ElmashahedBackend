"""
Tests for Core App
اختبارات التطبيق الأساسي
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model

from core.mixins import (
    AdminRequiredMixin, EmployeeRequiredMixin,
    InstituteScopedMixin, SearchMixin, FilterMixin
)
from institutes.models import Institute
from clients.models import Client

User = get_user_model()


class MockView:
    """View وهمي للاختبار"""
    def __init__(self, user):
        self.request = type('Request', (), {'user': user})()


class RoleRequiredMixinTests(TestCase):
    """اختبارات Mixins الأدوار"""
    
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
        
        self.admin = User.objects.create_user(
            username='admin',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.employee = User.objects.create_user(
            username='employee',
            password='testpass123',
            role=User.Role.EMPLOYEE,
            institute=self.institute
        )
    
    def test_admin_required_allows_admin(self):
        """اختبار أن AdminRequiredMixin يسمح للـ Admin"""
        mixin = AdminRequiredMixin()
        mixin.request = MockView(self.admin).request
        self.assertTrue(mixin.test_func())
    
    def test_admin_required_blocks_employee(self):
        """اختبار أن AdminRequiredMixin يمنع الموظف"""
        mixin = AdminRequiredMixin()
        mixin.request = MockView(self.employee).request
        self.assertFalse(mixin.test_func())
    
    def test_employee_required_allows_employee(self):
        """اختبار أن EmployeeRequiredMixin يسمح للموظف"""
        mixin = EmployeeRequiredMixin()
        mixin.request = MockView(self.employee).request
        self.assertTrue(mixin.test_func())
    
    def test_employee_required_allows_admin(self):
        """اختبار أن EmployeeRequiredMixin يسمح للـ Admin (لأنه أعلى رتبة)"""
        mixin = EmployeeRequiredMixin()
        mixin.request = MockView(self.admin).request
        self.assertTrue(mixin.test_func())


class InstituteScopedMixinTests(TestCase):
    """اختبارات Mixin نطاق المعهد"""
    
    def setUp(self):
        self.institute1 = Institute.objects.create(
            name='Institute 1',
            code='INST001',
            license_number='LIC001',
            address='Test',
            city='Test',
            region='Test',
            phone='1234567890'
        )
        self.institute2 = Institute.objects.create(
            name='Institute 2',
            code='INST002',
            license_number='LIC002',
            address='Test',
            city='Test',
            region='Test',
            phone='1234567890'
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.employee = User.objects.create_user(
            username='employee',
            password='testpass123',
            role=User.Role.EMPLOYEE,
            institute=self.institute1
        )
        
        # Create clients
        self.client1 = Client.objects.create(
            first_name='Client',
            last_name='One',
            full_name='Client One',
            national_id='ID001',
            gender='male',
            birth_date='1990-01-01',
            phone='1234567890',
            address='Test',
            institute=self.institute1,
            registered_by=self.employee
        )
        self.client2 = Client.objects.create(
            first_name='Client',
            last_name='Two',
            full_name='Client Two',
            national_id='ID002',
            gender='female',
            birth_date='1995-01-01',
            phone='0987654321',
            address='Test',
            institute=self.institute2,
            registered_by=self.employee
        )
    
    def test_admin_sees_all_institutes(self):
        """اختبار أن Admin يرى جميع المعاهد"""
        mixin = InstituteScopedMixin()
        mixin.request = MockView(self.admin).request
        
        institutes = mixin.get_user_institutes()
        self.assertIsNone(institutes)  # None means all
    
    def test_employee_sees_own_institute(self):
        """اختبار أن الموظف يرى معهده فقط"""
        mixin = InstituteScopedMixin()
        mixin.request = MockView(self.employee).request
        
        institutes = mixin.get_user_institutes()
        self.assertEqual(len(institutes), 1)
        self.assertEqual(institutes[0], self.institute1)


class SearchMixinTests(TestCase):
    """اختبارات Mixin البحث"""
    
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
        
        self.admin = User.objects.create_user(
            username='admin',
            password='testpass123',
            role=User.Role.ADMIN
        )
    
    def test_search_by_name(self):
        """اختبار البحث بالاسم"""
        # This would need a concrete view to test properly
        pass


class BaseModelTests(TestCase):
    """اختبارات BaseModel"""
    
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
    
    def test_soft_delete(self):
        """اختبار الحذف الناعم"""
        client = Client.objects.create(
            first_name='Test',
            last_name='Client',
            full_name='Test Client',
            national_id='TEST001',
            gender='male',
            birth_date='1990-01-01',
            phone='1234567890',
            address='Test',
            institute=self.institute,
            registered_by=self.employee
        )
        
        self.assertFalse(client.is_deleted)
        
        client.soft_delete()
        client.refresh_from_db()
        
        self.assertTrue(client.is_deleted)
    
    def test_restore(self):
        """اختبار استعادة المحذوف"""
        client = Client.objects.create(
            first_name='Test',
            last_name='Client',
            full_name='Test Client',
            national_id='TEST002',
            gender='male',
            birth_date='1990-01-01',
            phone='1234567890',
            address='Test',
            institute=self.institute,
            registered_by=self.employee
        )
        
        client.soft_delete()
        client.restore()
        client.refresh_from_db()
        
        self.assertFalse(client.is_deleted)
    
    def test_default_manager_excludes_deleted(self):
        """اختبار أن المدير الافتراضي يستبعد المحذوفات"""
        client = Client.objects.create(
            first_name='Test',
            last_name='Client',
            full_name='Test Client',
            national_id='TEST003',
            gender='male',
            birth_date='1990-01-01',
            phone='1234567890',
            address='Test',
            institute=self.institute,
            registered_by=self.employee
        )
        
        count_before = Client.objects.count()
        client.soft_delete()
        count_after = Client.objects.count()
        
        self.assertEqual(count_before - 1, count_after)
    
    def test_all_objects_includes_deleted(self):
        """اختبار أن all_objects يشمل المحذوفات"""
        client = Client.objects.create(
            first_name='Test',
            last_name='Client',
            full_name='Test Client',
            national_id='TEST004',
            gender='male',
            birth_date='1990-01-01',
            phone='1234567890',
            address='Test',
            institute=self.institute,
            registered_by=self.employee
        )
        
        client.soft_delete()
        
        # Default manager excludes deleted
        self.assertEqual(Client.objects.filter(national_id='TEST004').count(), 0)
        # all_objects includes deleted
        self.assertEqual(Client.all_objects.filter(national_id='TEST004').count(), 1)
