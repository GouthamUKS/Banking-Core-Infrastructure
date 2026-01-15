#!/usr/bin/env python3
"""
Enterprise-Grade Infrastructure-as-Code Deployment Manager
Automates the provisioning and management of a secure, multi-container web environment
with PostgreSQL database and web server orchestration.

Author: Cloud Automation Team
License: MIT
"""

import os
import sys
import json
import argparse
import subprocess
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import yaml
import docker
from docker.errors import DockerException


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class DeploymentConfig:
    """Configuration for deployment environment"""
    project_name: str
    environment: str  # dev, staging, prod
    db_name: str
    db_user: str
    db_password: str
    db_port: int
    web_port: int
    web_port_internal: int
    enable_ssl: bool
    backup_enabled: bool
    log_level: str


class DockerOrchestrator:
    """Manages Docker container orchestration and lifecycle"""
    
    def __init__(self, project_name: str):
        """Initialize Docker client and set project context"""
        try:
            self.client = docker.from_env()
            self.project_name = project_name
            logger.info(f"Docker client initialized for project: {project_name}")
        except DockerException as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise SystemExit(1)
    
    def verify_docker_installation(self) -> bool:
        """Verify Docker and Docker Compose are installed and accessible"""
        try:
            self.client.ping()
            logger.info("✓ Docker daemon is running")
            
            # Check Docker Compose
            result = subprocess.run(
                ['docker', 'compose', '--version'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info(f"✓ Docker Compose available: {result.stdout.strip()}")
                return True
            else:
                logger.error("✗ Docker Compose not found")
                return False
        except Exception as e:
            logger.error(f"Docker verification failed: {e}")
            return False
    
    def build_images(self, docker_compose_file: str) -> bool:
        """Build Docker images defined in compose file"""
        try:
            logger.info("Building Docker images...")
            result = subprocess.run(
                ['docker', 'compose', '-f', docker_compose_file, 'build', '--no-cache'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("✓ Docker images built successfully")
                return True
            else:
                logger.error(f"Failed to build images: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Build process failed: {e}")
            return False
    
    def start_containers(self, docker_compose_file: str) -> bool:
        """Start containers using docker-compose"""
        try:
            logger.info("Starting containers...")
            result = subprocess.run(
                ['docker', 'compose', '-f', docker_compose_file, 'up', '-d'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("✓ Containers started successfully")
                return True
            else:
                logger.error(f"Failed to start containers: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Container startup failed: {e}")
            return False
    
    def stop_containers(self, docker_compose_file: str) -> bool:
        """Stop running containers"""
        try:
            logger.info("Stopping containers...")
            result = subprocess.run(
                ['docker', 'compose', '-f', docker_compose_file, 'down'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("✓ Containers stopped successfully")
                return True
            else:
                logger.error(f"Failed to stop containers: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Container stop failed: {e}")
            return False
    
    def get_container_status(self, docker_compose_file: str) -> Dict:
        """Get status of all containers"""
        try:
            result = subprocess.run(
                ['docker', 'compose', '-f', docker_compose_file, 'ps', '--format', 'json'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                containers = json.loads(result.stdout) if result.stdout.strip() else []
                return {
                    'containers': containers,
                    'total': len(containers),
                    'running': len([c for c in containers if c.get('State') == 'running'])
                }
            return {'error': 'Failed to get container status'}
        except Exception as e:
            logger.error(f"Failed to get container status: {e}")
            return {'error': str(e)}


class DatabaseManager:
    """Manages database initialization and migrations"""
    
    def __init__(self, db_host: str, db_port: int, db_name: str, 
                 db_user: str, db_password: str):
        """Initialize database connection parameters"""
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
    
    def wait_for_database(self, max_attempts: int = 30, delay: int = 2) -> bool:
        """Wait for database to become available"""
        logger.info(f"Waiting for database at {self.db_host}:{self.db_port}...")
        
        import psycopg2
        
        for attempt in range(max_attempts):
            try:
                conn = psycopg2.connect(
                    host=self.db_host,
                    port=self.db_port,
                    user=self.db_user,
                    password=self.db_password,
                    database='postgres'
                )
                conn.close()
                logger.info("✓ Database is ready")
                return True
            except psycopg2.OperationalError:
                logger.info(f"  Attempt {attempt + 1}/{max_attempts} - Database not ready, retrying in {delay}s...")
                time.sleep(delay)
        
        logger.error("✗ Database failed to become ready")
        return False
    
    def run_migrations(self, migration_dir: str) -> bool:
        """Run database migration scripts"""
        try:
            logger.info(f"Running migrations from {migration_dir}...")
            
            import psycopg2
            
            # Read and execute migration files
            migration_files = sorted(Path(migration_dir).glob('*.sql'))
            
            if not migration_files:
                logger.warning("No migration files found")
                return True
            
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name
            )
            cursor = conn.cursor()
            
            for migration_file in migration_files:
                logger.info(f"  Executing: {migration_file.name}")
                with open(migration_file, 'r') as f:
                    cursor.execute(f.read())
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("✓ Migrations completed successfully")
            return True
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    def backup_database(self, backup_dir: str) -> Optional[str]:
        """Create database backup"""
        try:
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_dir, f"backup_{timestamp}.sql")
            
            logger.info(f"Creating database backup...")
            
            result = subprocess.run([
                'pg_dump',
                '-h', self.db_host,
                '-p', str(self.db_port),
                '-U', self.db_user,
                '-d', self.db_name,
                '-f', backup_file
            ], env={**os.environ, 'PGPASSWORD': self.db_password})
            
            if result.returncode == 0:
                logger.info(f"✓ Backup created: {backup_file}")
                return backup_file
            else:
                logger.error("Backup creation failed")
                return None
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None


class HealthCheckManager:
    """Manages system health checks and monitoring"""
    
    @staticmethod
    def check_container_health(docker_compose_file: str) -> Dict:
        """Check health of all containers"""
        try:
            result = subprocess.run(
                ['docker', 'compose', '-f', docker_compose_file, 'ps'],
                capture_output=True,
                text=True
            )
            return {
                'status': 'healthy' if result.returncode == 0 else 'unhealthy',
                'output': result.stdout
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    @staticmethod
    def check_port_availability(port: int) -> bool:
        """Check if port is available"""
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result != 0


class DeploymentManager:
    """Orchestrates the entire deployment process"""
    
    def __init__(self, config_file: str):
        """Initialize deployment manager with configuration"""
        self.config = self._load_config(config_file)
        self.orchestrator = DockerOrchestrator(self.config['project_name'])
        self.db_manager = DatabaseManager(
            db_host='postgres',
            db_port=self.config['db_port'],
            db_name=self.config['db_name'],
            db_user=self.config['db_user'],
            db_password=self.config['db_password']
        )
        self.health_check = HealthCheckManager()
    
    @staticmethod
    def _load_config(config_file: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_file}")
            raise SystemExit(1)
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML configuration: {e}")
            raise SystemExit(1)
    
    def pre_deployment_checks(self) -> bool:
        """Perform pre-deployment validation"""
        logger.info("=" * 60)
        logger.info("PERFORMING PRE-DEPLOYMENT CHECKS")
        logger.info("=" * 60)
        
        checks_passed = True
        
        # Check Docker installation
        if not self.orchestrator.verify_docker_installation():
            checks_passed = False
        
        # Check port availability
        if not self.health_check.check_port_availability(self.config['web_port']):
            logger.error(f"✗ Port {self.config['web_port']} is already in use")
            checks_passed = False
        else:
            logger.info(f"✓ Port {self.config['web_port']} is available")
        
        # Verify docker-compose file exists
        compose_file = self.config.get('docker_compose_file', 'docker-compose.yml')
        if not os.path.exists(compose_file):
            logger.error(f"✗ Docker Compose file not found: {compose_file}")
            checks_passed = False
        else:
            logger.info(f"✓ Docker Compose file found: {compose_file}")
        
        return checks_passed
    
    def deploy(self, skip_build: bool = False) -> bool:
        """Execute complete deployment process"""
        try:
            logger.info("\n" + "=" * 60)
            logger.info("STARTING DEPLOYMENT")
            logger.info(f"Project: {self.config['project_name']}")
            logger.info(f"Environment: {self.config['environment']}")
            logger.info("=" * 60 + "\n")
            
            # Pre-deployment checks
            if not self.pre_deployment_checks():
                logger.error("Pre-deployment checks failed")
                return False
            
            compose_file = self.config.get('docker_compose_file', 'docker-compose.yml')
            
            # Build images
            if not skip_build:
                if not self.orchestrator.build_images(compose_file):
                    return False
            
            # Start containers
            if not self.orchestrator.start_containers(compose_file):
                return False
            
            # Wait for database
            logger.info("\nInitializing database...")
            if not self.db_manager.wait_for_database():
                return False
            
            # Run migrations
            migration_dir = self.config.get('migration_dir', 'database/migrations')
            if os.path.exists(migration_dir):
                if not self.db_manager.run_migrations(migration_dir):
                    logger.warning("Migrations completed with warnings")
            
            # Health checks
            logger.info("\nPerforming health checks...")
            health = self.health_check.check_container_health(compose_file)
            logger.info(f"Container health: {health['status']}")
            
            # Print deployment summary
            self._print_deployment_summary()
            
            logger.info("\n" + "=" * 60)
            logger.info("DEPLOYMENT COMPLETED SUCCESSFULLY")
            logger.info("=" * 60 + "\n")
            return True
        
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False
    
    def stop_deployment(self) -> bool:
        """Stop running containers and clean up"""
        try:
            logger.info("Stopping deployment...")
            compose_file = self.config.get('docker_compose_file', 'docker-compose.yml')
            return self.orchestrator.stop_containers(compose_file)
        except Exception as e:
            logger.error(f"Failed to stop deployment: {e}")
            return False
    
    def _print_deployment_summary(self):
        """Print deployment summary and access information"""
        compose_file = self.config.get('docker_compose_file', 'docker-compose.yml')
        status = self.orchestrator.get_container_status(compose_file)
        
        logger.info("\n" + "=" * 60)
        logger.info("DEPLOYMENT SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Containers: {status.get('total', 0)}")
        logger.info(f"Running: {status.get('running', 0)}")
        logger.info(f"\nWeb Application: http://localhost:{self.config['web_port']}")
        logger.info(f"Database Host: localhost:{self.config['db_port']}")
        logger.info(f"Database Name: {self.config['db_name']}")
        logger.info("=" * 60 + "\n")


def main():
    """Main entry point for deployment script"""
    parser = argparse.ArgumentParser(
        description='Enterprise IaC Deployment Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s deploy --config config/production.yaml
  %(prog)s stop --config config/production.yaml
  %(prog)s status --config config/production.yaml
        """
    )
    
    parser.add_argument(
        'action',
        choices=['deploy', 'stop', 'status'],
        help='Deployment action to perform'
    )
    parser.add_argument(
        '--config',
        default='config/deployment.yaml',
        help='Configuration file path (default: config/deployment.yaml)'
    )
    parser.add_argument(
        '--skip-build',
        action='store_true',
        help='Skip Docker image build step'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Create database backup before deployment'
    )
    
    args = parser.parse_args()
    
    # Initialize deployment manager
    manager = DeploymentManager(args.config)
    
    if args.action == 'deploy':
        if args.backup:
            logger.info("Creating pre-deployment backup...")
            backup_dir = manager.config.get('backup_dir', 'backups')
            manager.db_manager.backup_database(backup_dir)
        
        success = manager.deploy(skip_build=args.skip_build)
        sys.exit(0 if success else 1)
    
    elif args.action == 'stop':
        success = manager.stop_deployment()
        sys.exit(0 if success else 1)
    
    elif args.action == 'status':
        compose_file = manager.config.get('docker_compose_file', 'docker-compose.yml')
        status = manager.orchestrator.get_container_status(compose_file)
        logger.info(json.dumps(status, indent=2))
        sys.exit(0)


if __name__ == '__main__':
    main()
