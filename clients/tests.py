"""
Tests for Clients App
اختبارات تطبيق العملاء
"""
from django.test import TestCase, Client as TestClient
from django.urls import reverse
from django.contrib.auth import get_user_model

from institutes.models import Institute
from .models import Client

User = get_user_model()


class ClientModelTests(TestCase):
    """اختبارات نموذج العميل"""
    
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
        self.employee = User.objects.create_user(
            username='employee',
            password='testpass123',
            role=User.Role.EMPLOYEE,
            institute=self.institute
        )
    
    def test_create_client(self):
        """اختبار إنشاء عميل"""
        client = Client.objects.create(
            first_name='John',
            last_name='Doe',
            full_name='John Doe',
            national_id='1234567890',
            gender='male',
            birth_date='1990-01-01',
            phone='0123456789',
            email='john@example.com',
            address='123 Test St',
            institute=self.institute,
            registered_by=self.employee
        )
        
        self.assertEqual(client.full_name, 'John Doe')
        self.assertEqual(client.national_id, '1234567890')
        self.assertEqual(client.status, Client.Status.ACTIVE)
    
    def test_full_name_auto_generation(self):
        """اختبار توليد الاسم الكامل تلقائياً"""
        client = Client.objects.create(
            first_name='Jane',
            last_name='Smith',
            full_name='',  # Will be auto-generated
            national_id='0987654321',
            gender='female',
            birth_date='1995-01-01',
            phone='0123456789',
            address='456 Test St',
            institute=self.institute,
            registered_by=self.employee
        )
        
        self.assertEqual(client.full_name, 'Jane Smith')
    
    def test_national_id_unique(self):
        """اختبار أن رقم الهوية فريد"""
        Client.objects.create(
            first_name='First',
            last_name='Client',
            full_name='First Client',
            national_id='UNIQUE001',
            gender='male',
            birth_date='1990-01-01',
            phone='0123456789',
            address='Test',
            institute=self.institute,
            registered_by=self.employee
        )
        
        with self.assertRaises(Exception):
            Client.objects.create(
                first_name='Second',
                last_name='Client',
                full_name='Second Client',
                national_id='UNIQUE001',  # Same ID
                gender='female',
                birth_date='1995-01-01',
                phone='0987654321',
                address='Test',
                institute=self.institute,
                registered_by=self.employee
            )
    
    def test_get_active_registrations(self):
        """اختبار الحصول على التسجيلات النشطة"""
        client = Client.objects.create(
            first_name='Test',
            last_name='Client',
            full_name='Test Client',
            national_id='REGTEST001',
            gender='male',
            birth_date='1990-01-01',
            phone='0123456789',
            address='Test',
            institute=self.institute,
            registered_by=self.employee
        )
        
        active_regs = client.get_active_registrations()
        self.assertEqual(active_regs.count(), 0)


class ClientViewsTests(TestCase):
    """اختبارات Views العملاء"""
    
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
    
    def test_client_list_requires_login(self):
        """اختبار أن قائمة العملاء تتطلب تسجيل دخول"""
        response = self.client.get(reverse('clients:client_list'))
        self.assertEqual(response.status_code, 302)
    
    def test_client_list_accessible_to_employee(self):
        """اختبار أن الموظف يمكنه رؤية قائمة العملاء"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('clients:client_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_create_client(self):
        """اختبار إنشاء عميل"""
        self.client.login(username='employee', password='testpass123')
        
        response = self.client.post(reverse('clients:client_create'), {
            'first_name': 'New',
            'last_name': 'Client',
            'national_id': 'NEW001',
            'gender': 'male',
            'birth_date': '1990-01-01',
            'phone': '0123456789',
            'email': 'new@example.com',
            'address': 'Test Address',
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(Client.objects.filter(national_id='NEW001').exists())
    
    def test_search_clients_ajax(self):
        """اختبار البحث عن العملاء عبر AJAX"""
        Client.objects.create(
            first_name='Searchable',
            last_name='Client',
            full_name='Searchable Client',
            national_id='SEARCH001',
            gender='male',
            birth_date='1990-01-01',
            phone='0123456789',
            address='Test',
            institute=self.institute,
            registered_by=self.employee
        )
        
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(
            reverse('clients:client_search'),
            {'q': 'Searchable'}
        )
        
        self.assertEqual(response.status_code, 200)
        import json
        data = json.loads(response.content)
        self.assertTrue(len(data['results']) > 0)
    
    def test_get_client_by_national_id(self):
        """اختبار الحصول على عميل برقم الهوية"""
        Client.objects.create(
            first_name='NationalID',
            last_name='Test',
            full_name='NationalID Test',
            national_id='NID001',
            gender='male',
            birth_date='1990-01-01',
            phone='0123456789',
            address='Test',
            institute=self.institute,
            registered_by=self.employee
        )
        
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(
            reverse('clients:get_client_by_national_id'),
            {'national_id': 'NID001'}
        )
        
        self.assertEqual(response.status_code, 200)
        import json
        data = json.loads(response.content)
        self.assertTrue(data['found'])
        self.assertEqual(data['client']['full_name'], 'NationalID Test')


class ClientPermissionsTests(TestCase):
    """اختبارات صلاحيات العملاء"""
    
    def setUp(self):
        self.client = TestClient()
        
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
        
        self.employee1 = User.objects.create_user(
            username='employee1',
            password='testpass123',
            role=User.Role.EMPLOYEE,
            institute=self.institute1
        )
        self.employee2 = User.objects.create_user(
            username='employee2',
            password='testpass123',
            role=User.Role.EMPLOYEE,
            institute=self.institute2
        )
        
        self.client1 = Client.objects.create(
            first_name='Client',
            last_name='One',
            full_name='Client One',
            national_id='CLIENT001',
            gender='male',
            birth_date='1990-01-01',
            phone='0123456789',
            address='Test',
            institute=self.institute1,
            registered_by=self.employee1
        )
        self.client2 = Client.objects.create(
            first_name='Client',
            last_name='Two',
            full_name='Client Two',
            national_id='CLIENT002',
            gender='female',
            birth_date='1995-01-01',
            phone='0987654321',
            address='Test',
            institute=self.institute2,
            registered_by=self.employee2
        )
    
    def test_employee_sees_only_own_institute_clients(self):
        """اختبار أن الموظف يرى عملاء معهده فقط"""
        self.client.login(username='employee1', password='testpass123')
        response = self.client.get(reverse('clients:client_list'))
        
        self.assertEqual(response.status_code, 200)
        # Should only see client1 (from institute1)
        self.assertIn(self.client1, response.context['clients'])
        self.assertNotIn(self.client2, response.context['clients'])
