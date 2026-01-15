"""
Unit tests for deployment system
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from deploy import DockerOrchestrator, DatabaseManager, HealthCheckManager


class TestDockerOrchestrator(unittest.TestCase):
    """Tests for Docker orchestration functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.project_name = "test-project"
    
    @patch('docker.from_env')
    def test_orchestrator_initialization(self, mock_docker):
        """Test DockerOrchestrator initialization"""
        orchestrator = DockerOrchestrator(self.project_name)
        self.assertEqual(orchestrator.project_name, self.project_name)
    
    @patch('docker.from_env')
    def test_verify_docker_installation(self, mock_docker):
        """Test Docker installation verification"""
        orchestrator = DockerOrchestrator(self.project_name)
        # Mock successful Docker ping
        orchestrator.client.ping = MagicMock(return_value=True)
        result = orchestrator.verify_docker_installation()
        # Would pass if Docker is installed


class TestDatabaseManager(unittest.TestCase):
    """Tests for database management"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.db_manager = DatabaseManager(
            db_host='localhost',
            db_port=5432,
            db_name='test_db',
            db_user='postgres',
            db_password='password'
        )
    
    def test_database_manager_initialization(self):
        """Test DatabaseManager initialization"""
        self.assertEqual(self.db_manager.db_host, 'localhost')
        self.assertEqual(self.db_manager.db_port, 5432)
        self.assertEqual(self.db_manager.db_name, 'test_db')


class TestHealthCheckManager(unittest.TestCase):
    """Tests for health check functionality"""
    
    def test_port_availability(self):
        """Test port availability check"""
        # Test with an uncommon port that should be available
        result = HealthCheckManager.check_port_availability(54321)
        self.assertTrue(result)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_configuration_loading(self):
        """Test that configuration files can be loaded"""
        config_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'config',
            'deployment.yaml'
        )
        self.assertTrue(os.path.exists(config_path))


if __name__ == '__main__':
    unittest.main()
