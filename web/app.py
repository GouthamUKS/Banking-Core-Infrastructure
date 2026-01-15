"""
Enterprise Web Application
Demonstrates a production-ready Flask application connected to PostgreSQL
"""

import os
import logging
from datetime import datetime
from typing import Optional
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.exceptions import HTTPException

# Configure logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:password@localhost:5432/enterprise_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)


# Database Models
class Application(db.Model):
    """Application metadata model"""
    __tablename__ = 'applications'
    
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(255), nullable=False, unique=True)
    description: Optional[str] = db.Column(db.Text)
    status: str = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, name: str, description: Optional[str] = None, status: str = 'active'):
        """Explicit constructor to satisfy Pylance type checking"""
        self.name = name
        self.description = description
        self.status = status
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class ServiceHealth(db.Model):
    """Service health monitoring model"""
    __tablename__ = 'service_health'
    
    id: int = db.Column(db.Integer, primary_key=True)
    service_name: str = db.Column(db.String(255), nullable=False)
    status: str = db.Column(db.String(50), default='healthy')
    response_time_ms: Optional[int] = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, service_name: str, status: str = 'healthy', response_time_ms: Optional[int] = None):
        """Explicit constructor to satisfy Pylance type checking"""
        self.service_name = service_name
        self.status = status
        self.response_time_ms = response_time_ms
    
    def to_dict(self):
        return {
            'id': self.id,
            'service_name': self.service_name,
            'status': self.status,
            'response_time_ms': self.response_time_ms,
            'timestamp': self.timestamp.isoformat()
        }


# Error Handlers
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Handle HTTP exceptions"""
    response = {
        'error': e.name,
        'message': e.description,
        'status_code': e.code
    }
    return jsonify(response), e.code


@app.errorhandler(Exception)
def handle_exception(e):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(e)}")
    response = {
        'error': 'Internal Server Error',
        'message': str(e),
        'status_code': 500
    }
    return jsonify(response), 500


# Health Check Endpoints
@app.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    try:
        # Check database connectivity
        db.session.execute(text('SELECT 1'))
        db_status = 'healthy'
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = 'unhealthy'
    
    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'database': db_status,
        'timestamp': datetime.utcnow().isoformat()
    }), 200 if db_status == 'healthy' else 503


@app.route('/health/deep', methods=['GET'])
def deep_health_check():
    """Comprehensive health check with database details"""
    try:
        # Test database connection and query
        result = db.session.execute(text('SELECT NOW()'))
        row = result.fetchone()
        db_time = row[0] if row else None
        
        # Count records
        app_count = Application.query.count()
        health_count = ServiceHealth.query.count()
        
        return jsonify({
            'status': 'healthy',
            'database': {
                'status': 'connected',
                'server_time': db_time.isoformat() if db_time else None,
                'applications': app_count,
                'health_records': health_count
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Deep health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503


# Application Endpoints
@app.route('/api/v1/applications', methods=['GET'])
def list_applications():
    """List all applications"""
    try:
        applications = Application.query.all()
        return jsonify({
            'status': 'success',
            'data': [app.to_dict() for app in applications],
            'count': len(applications)
        }), 200
    except Exception as e:
        logger.error(f"Failed to list applications: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/v1/applications', methods=['POST'])
def create_application():
    """Create a new application"""
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: name'
            }), 400
        
        # Check if application already exists
        existing = Application.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({
                'status': 'error',
                'message': f"Application '{data['name']}' already exists"
            }), 409
        
        # Create new application - Errors resolved by __init__
        new_app = Application(
            name=data.get('name', ''),
            description=data.get('description', ''),
            status=data.get('status', 'active')
        )
        
        db.session.add(new_app)
        db.session.commit()
        
        logger.info(f"Created application: {data['name']}")
        
        return jsonify({
            'status': 'success',
            'message': f"Application '{data['name']}' created successfully",
            'data': new_app.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create application: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/v1/applications/<int:app_id>', methods=['GET'])
def get_application(app_id):
    """Get specific application"""
    try:
        app = Application.query.get(app_id)
        if not app:
            return jsonify({'status': 'error', 'message': 'Application not found'}), 404
        
        return jsonify({
            'status': 'success',
            'data': app.to_dict()
        }), 200
    except Exception as e:
        logger.error(f"Failed to get application: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/v1/applications/<int:app_id>', methods=['PUT'])
def update_application(app_id):
    """Update application"""
    try:
        app = Application.query.get(app_id)
        if not app:
            return jsonify({'status': 'error', 'message': 'Application not found'}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            app.name = data['name']
        if 'description' in data:
            app.description = data['description']
        if 'status' in data:
            app.status = data['status']
        
        db.session.commit()
        logger.info(f"Updated application: {app.name}")
        
        return jsonify({
            'status': 'success',
            'message': 'Application updated successfully',
            'data': app.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update application: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/v1/applications/<int:app_id>', methods=['DELETE'])
def delete_application(app_id):
    """Delete application"""
    try:
        app = Application.query.get(app_id)
        if not app:
            return jsonify({'status': 'error', 'message': 'Application not found'}), 404
        
        app_name = app.name
        db.session.delete(app)
        db.session.commit()
        
        logger.info(f"Deleted application: {app_name}")
        
        return jsonify({
            'status': 'success',
            'message': f"Application '{app_name}' deleted successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete application: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Service Health Endpoints
@app.route('/api/v1/health/metrics', methods=['GET'])
def get_health_metrics():
    """Get recent health metrics"""
    try:
        limit = request.args.get('limit', 100, type=int)
        metrics = ServiceHealth.query.order_by(ServiceHealth.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'status': 'success',
            'data': [m.to_dict() for m in metrics],
            'count': len(metrics)
        }), 200
    except Exception as e:
        logger.error(f"Failed to get health metrics: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/v1/health/record', methods=['POST'])
def record_health_metric():
    """Record a health metric"""
    try:
        data = request.get_json()
        
        if not data or not data.get('service_name'):
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: service_name'
            }), 400
        
        # Create health record - Errors resolved by __init__
        health_record = ServiceHealth(
            service_name=data.get('service_name', ''),
            status=data.get('status', 'unknown'),
            response_time_ms=data.get('response_time_ms', 0)
        )
        
        db.session.add(health_record)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Health metric recorded',
            'data': health_record.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to record health metric: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Info and Metadata Endpoints
@app.route('/api/v1/info', methods=['GET'])
def app_info():
    """Get application metadata"""
    return jsonify({
        'application': 'Enterprise Cloud Infrastructure',
        'version': '1.0.0',
        'environment': os.getenv('FLASK_ENV', 'unknown'),
        'timestamp': datetime.utcnow().isoformat(),
        'endpoints': {
            'health': '/health',
            'deep_health': '/health/deep',
            'applications': '/api/v1/applications',
            'health_metrics': '/api/v1/health/metrics'
        }
    }), 200


@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'message': 'Enterprise IaC Deployment System API',
        'status': 'running',
        'version': '1.0.0',
        'documentation': 'See /api/v1/info for available endpoints'
    }), 200


# Initialize Database
def init_db():
    """Initialize database with tables"""
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")


if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('FLASK_ENV') == 'development'
    )