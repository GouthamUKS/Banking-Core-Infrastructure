#!/bin/bash
# Deployment wrapper script for easy management

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_SCRIPT="$PROJECT_ROOT/src/deploy.py"
CONFIG_FILE="${1:-$PROJECT_ROOT/config/deployment.yaml}"
ACTION="${2:-deploy}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Deploy script not found at $PYTHON_SCRIPT"
    exit 1
fi

echo -e "${BLUE}Enterprise IaC Deployment Manager${NC}"
echo "Action: $ACTION"
echo "Config: $CONFIG_FILE"
echo ""

# Execute deployment
python3 "$PYTHON_SCRIPT" "$ACTION" --config "$CONFIG_FILE"
