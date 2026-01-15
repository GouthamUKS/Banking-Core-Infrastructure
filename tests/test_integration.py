"""
Integration test suite for deployed system
"""

import requests
import json
import time
import unittest
from typing import Dict


class DeploymentIntegrationTest(unittest.TestCase):
    """Integration tests for deployed system"""
    
    BASE_URL = "http://localhost:8080"
    
    @classmethod
    def setUpClass(cls):
        """Wait for system to be ready"""
        max_retries = 30
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = requests.get(f"{cls.BASE_URL}/health", timeout=2)
                if response.status_code == 200:
                    print("✓ System is ready")
                    break
            except requests.RequestException:
                retry_count += 1
                time.sleep(2)
        
        if retry_count >= max_retries:
            raise Exception("System failed to become ready")
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = requests.get(f"{self.BASE_URL}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
    
    def test_deep_health_check(self):
        """Test comprehensive health check"""
        response = requests.get(f"{self.BASE_URL}/health/deep")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('database', data)
    
    def test_app_info_endpoint(self):
        """Test application info endpoint"""
        response = requests.get(f"{self.BASE_URL}/api/v1/info")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('application', data)
        self.assertIn('version', data)
    
    def test_list_applications(self):
        """Test listing applications"""
        response = requests.get(f"{self.BASE_URL}/api/v1/applications")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('data', data)
        self.assertIsInstance(data['data'], list)
    
    def test_create_application(self):
        """Test creating application"""
        app_data = {
            "name": f"test-app-{int(time.time())}",
            "description": "Test application"
        }
        response = requests.post(
            f"{self.BASE_URL}/api/v1/applications",
            json=app_data
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('data', data)
    
    def test_api_error_handling(self):
        """Test API error handling"""
        # Test invalid application ID
        response = requests.get(f"{self.BASE_URL}/api/v1/applications/99999")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data['status'], 'error')
    
    def test_database_connectivity(self):
        """Test database connectivity through API"""
        response = requests.get(f"{self.BASE_URL}/health/deep")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['database']['status'], 'connected')


if __name__ == '__main__':
    unittest.main()
