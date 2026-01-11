#!/bin/bash

###############################################################################
# WealthCraft Production Server Startup Script
###############################################################################
#
# 🎓 LEARNING: This script starts your Flask app with Gunicorn in production
#
# Usage:
#   ./start_production.sh          # Start in foreground
#   ./start_production.sh &         # Start in background
#   ./start_production.sh --daemon  # Start as daemon
#
###############################################################################

# Exit on any error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

###############################################################################
# CONFIGURATION
###############################################################################

# Environment (development, production, testing)
export FLASK_CONFIG="${FLASK_CONFIG:-production}"

# Load environment variables
if [ -f .env ]; then
    echo -e "${BLUE}📄 Loading environment from .env${NC}"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}⚠️  No .env file found, using defaults${NC}"
fi

# Gunicorn settings
CONFIG_FILE="gunicorn_config.py"
APP_MODULE="run:app"

###############################################################################
# PRE-FLIGHT CHECKS
###############################################################################

echo -e "${BLUE}🔍 Running pre-flight checks...${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}🐍 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo -e "${YELLOW}⚠️  Gunicorn not found. Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

# Check if gevent is installed (required for async workers)
if ! python -c "import gevent" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Gevent not found. Installing...${NC}"
    pip install gevent
fi

# Check if required environment variables are set
if [ -z "$SUPABASE_JWT_SECRET" ]; then
    echo -e "${RED}❌ ERROR: SUPABASE_JWT_SECRET not set${NC}"
    echo -e "${YELLOW}   Please set it in .env file${NC}"
    exit 1
fi

if [ -z "$SUPABASE_URL" ]; then
    echo -e "${RED}❌ ERROR: SUPABASE_URL not set${NC}"
    exit 1
fi

if [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    echo -e "${RED}❌ ERROR: SUPABASE_SERVICE_ROLE_KEY not set${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All pre-flight checks passed!${NC}"

###############################################################################
# START SERVER
###############################################################################

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║         🚀 Starting WealthCraft Production Server         ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo -e "  Environment: ${GREEN}${FLASK_CONFIG}${NC}"
echo -e "  Config File: ${GREEN}${CONFIG_FILE}${NC}"
echo -e "  App Module:  ${GREEN}${APP_MODULE}${NC}"
echo ""

# Check for daemon flag
if [[ "$1" == "--daemon" ]]; then
    echo -e "${BLUE}🔧 Starting in daemon mode...${NC}"
    gunicorn -c "$CONFIG_FILE" "$APP_MODULE" --daemon
    echo -e "${GREEN}✅ Server started in background${NC}"
    echo -e "${YELLOW}   Check logs with: tail -f gunicorn.log${NC}"
    echo -e "${YELLOW}   Stop with: pkill -f gunicorn${NC}"
else
    echo -e "${BLUE}🔧 Starting in foreground mode...${NC}"
    echo -e "${YELLOW}   Press Ctrl+C to stop${NC}"
    echo ""
    
    # Start Gunicorn
    # 🎓 EXPLANATION:
    #   -c gunicorn_config.py = Use our configuration file
    #   run:app = Module:variable (run.py file, app variable)
    gunicorn -c "$CONFIG_FILE" "$APP_MODULE"
fi

###############################################################################
# NOTES
###############################################################################
#
# 🎓 WHAT HAPPENS WHEN YOU RUN THIS:
#
# 1. Checks environment and dependencies
# 2. Activates Python virtual environment
# 3. Loads environment variables from .env
# 4. Starts Gunicorn with configuration from gunicorn_config.py
# 5. Gunicorn spawns multiple worker processes
# 6. Each worker can handle 1000+ concurrent connections
# 7. Server listens on 0.0.0.0:5000
#
# MONITORING:
#   - Watch logs: tail -f gunicorn.log
#   - Check processes: ps aux | grep gunicorn
#   - Test endpoint: curl http://localhost:5000/health
#
# STOPPING:
#   - Foreground: Press Ctrl+C
#   - Background: pkill -f gunicorn
#   - Graceful: kill -TERM $(cat gunicorn.pid)
#
# RELOADING (without downtime):
#   - kill -HUP $(cat gunicorn.pid)
#
###############################################################################
