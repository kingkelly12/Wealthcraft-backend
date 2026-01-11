#!/bin/bash

# 🚀 Local Flask Development Server for Mobile App Testing
# This script runs Flask on your local network so your phone can connect to it

set -e  # Exit on error

export FLASK_CONFIG=development
export FLASK_APP=run.py
export FLASK_DEBUG=1

# Get local IP addresses
WSL_IP=$(hostname -I | awk '{print $1}')

echo "========================================="
echo "🚀 Starting Flask Development Server"
echo "========================================="
echo ""
echo "📱 Mobile App Configuration:"
echo ""
echo "   WSL IP (for testing from WSL):"
echo "   EXPO_PUBLIC_API_URL=http://${WSL_IP}:5000"
echo ""
echo "   Windows WiFi IP (for phone testing):"
echo "   1. Open PowerShell on Windows"
echo "   2. Run: ipconfig"
echo "   3. Find 'Wireless LAN adapter Wi-Fi' → IPv4 Address"
echo "   4. Set EXPO_PUBLIC_API_URL=http://[THAT_IP]:5000"
echo ""
echo "🌐 Server will be accessible at:"
echo "   - Local: http://localhost:5000"
echo "   - WSL Network: http://${WSL_IP}:5000"
echo "   - Windows Network: http://[WINDOWS_IP]:5000 (after port forwarding)"
echo ""
echo "⚠️  Important Steps:"
echo "   1. Run setup_wsl_port_forward.ps1 on Windows (as Administrator)"
echo "   2. Make sure your phone is on the same WiFi network"
echo "   3. Update mobile/.env with your Windows WiFi IP"
echo ""
echo "🔍 Testing:"
echo "   From phone browser: http://[WINDOWS_IP]:5000/health"
echo ""
echo "========================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  WARNING: .env file not found!"
    echo "   Please create .env file with DATABASE_URL and other config"
    echo ""
fi

# Run Flask with network access (0.0.0.0 makes it accessible on all interfaces)
echo "Starting Flask on 0.0.0.0:5000..."
echo ""
python3 run.py --host=0.0.0.0 --port=5000
