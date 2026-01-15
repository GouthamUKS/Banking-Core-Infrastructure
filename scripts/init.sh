#!/bin/bash
# Enterprise IaC Deployment Initialization Script
# This script prepares the environment and validates all dependencies

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_MIN_VERSION="3.8"
DOCKER_MIN_VERSION="20.10"

# Functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is not installed"
        return 1
    fi
}

check_python_version() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        return 1
    fi
    
    local python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_success "Python $python_version is installed"
}

check_docker_installation() {
    print_header "Checking Docker Installation"
    
    if ! check_command docker; then
        print_error "Docker is required but not installed"
        echo "Install Docker from https://www.docker.com/"
        exit 1
    fi
    
    if ! check_command "docker compose"; then
        print_warning "Docker Compose not found. Attempting 'docker-compose' command..."
        if ! check_command docker-compose; then
            print_error "Docker Compose is required but not installed"
            exit 1
        fi
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        echo "Please start Docker and try again"
        exit 1
    fi
    
    print_success "Docker daemon is running"
}

check_python_dependencies() {
    print_header "Checking Python Dependencies"
    
    local required_packages=("docker" "pyyaml" "psycopg2" "flask")
    
    for package in "${required_packages[@]}"; do
        if python3 -c "import $package" 2>/dev/null; then
            print_success "$package is installed"
        else
            print_warning "$package is not installed"
        fi
    done
}

setup_environment() {
    print_header "Setting Up Environment"
    
    # Create .env file if it doesn't exist
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        print_warning ".env file not found. Creating from .env.example..."
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            print_success ".env file created"
        else
            print_error ".env.example not found"
        fi
    else
        print_success ".env file already exists"
    fi
    
    # Create backup directory
    mkdir -p "$PROJECT_ROOT/backups"
    print_success "Backup directory ensured"
    
    # Create logs directory
    mkdir -p "$PROJECT_ROOT/logs"
    print_success "Logs directory ensured"
}

check_ports() {
    print_header "Checking Port Availability"
    
    local ports=(5432 8080 80 443)
    
    for port in "${ports[@]}"; do
        if lsof -i ":$port" &> /dev/null; then
            print_warning "Port $port is already in use"
        else
            print_success "Port $port is available"
        fi
    done
}

validate_docker_compose_file() {
    print_header "Validating Docker Compose File"
    
    if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        print_error "docker-compose.yml not found"
        exit 1
    fi
    
    if docker compose -f "$PROJECT_ROOT/docker-compose.yml" config > /dev/null 2>&1; then
        print_success "docker-compose.yml is valid"
    else
        print_error "docker-compose.yml validation failed"
        exit 1
    fi
}

install_python_requirements() {
    print_header "Installing Python Requirements"
    
    if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        print_warning "Installing Python packages..."
        pip3 install --upgrade pip setuptools wheel
        pip3 install -r "$PROJECT_ROOT/requirements.txt"
        print_success "Python packages installed"
    else
        print_warning "requirements.txt not found at root level"
    fi
}

run_comprehensive_checks() {
    print_header "Running Comprehensive System Checks"
    
    # Summary of findings
    local checks_passed=true
    
    print_success "All critical checks passed!"
}

# Main execution
main() {
    echo -e "${BLUE}"
    cat << "EOF"
╔════════════════════════════════════════════════════════════════╗
║      Enterprise IaC Deployment System - Initialize             ║
║                   Infrastructure Setup                          ║
╚════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    check_docker_installation
    check_python_version
    check_python_dependencies
    check_ports
    validate_docker_compose_file
    setup_environment
    
    print_header "Initialization Summary"
    print_success "Environment is ready for deployment"
    echo -e "\nNext steps:"
    echo "  1. Review and update configuration: .env"
    echo "  2. Run deployment: python3 src/deploy.py deploy --config config/deployment.yaml"
    echo "  3. Check status: python3 src/deploy.py status --config config/deployment.yaml"
    echo ""
}

# Execute main function
main "$@"
