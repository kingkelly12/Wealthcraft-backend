# WSL Port Forwarding Setup for Flask Development
# Run this script in PowerShell as Administrator on Windows

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "🔧 Setting up WSL Port Forwarding" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Get WSL IP address
Write-Host "📡 Getting WSL IP address..." -ForegroundColor Yellow
$wslIp = (wsl hostname -I).Trim().Split()[0]

if (-not $wslIp) {
    Write-Host "❌ ERROR: Could not get WSL IP address" -ForegroundColor Red
    Write-Host "   Make sure WSL is running" -ForegroundColor Red
    exit 1
}

Write-Host "✅ WSL IP: $wslIp" -ForegroundColor Green
Write-Host ""

# Remove existing port forwarding (if any)
Write-Host "🧹 Removing existing port forwarding rules..." -ForegroundColor Yellow
try {
    netsh interface portproxy delete v4tov4 listenport=5000 listenaddress=0.0.0.0 2>$null
} catch {
    # Ignore errors if rule doesn't exist
}

# Add port forwarding from Windows to WSL
Write-Host "➕ Adding port forwarding rule..." -ForegroundColor Yellow
Write-Host "   Windows 0.0.0.0:5000 → WSL ${wslIp}:5000" -ForegroundColor Gray

try {
    netsh interface portproxy add v4tov4 listenport=5000 listenaddress=0.0.0.0 connectport=5000 connectaddress=$wslIp
    Write-Host "✅ Port forwarding configured!" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Failed to add port forwarding" -ForegroundColor Red
    Write-Host "   Make sure you're running PowerShell as Administrator" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Add firewall rule to allow incoming connections
Write-Host "🔥 Configuring Windows Firewall..." -ForegroundColor Yellow

# Remove existing firewall rule (if any)
try {
    Remove-NetFirewallRule -DisplayName "Flask Dev Server" -ErrorAction SilentlyContinue
} catch {
    # Ignore errors if rule doesn't exist
}

# Add new firewall rule
try {
    New-NetFirewallRule -DisplayName "Flask Dev Server" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow | Out-Null
    Write-Host "✅ Firewall rule added!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  WARNING: Could not add firewall rule" -ForegroundColor Yellow
    Write-Host "   You may need to manually allow port 5000 in Windows Firewall" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Get Windows WiFi IP
Write-Host "📱 Your Windows WiFi IP Address:" -ForegroundColor Cyan
$wifiAdapter = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -like "*Wi-Fi*" -or $_.InterfaceAlias -like "*Wireless*" } | Select-Object -First 1

if ($wifiAdapter) {
    $windowsIp = $wifiAdapter.IPAddress
    Write-Host "   $windowsIp" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 Mobile App Configuration:" -ForegroundColor Cyan
    Write-Host "   Update mobile/.env with:" -ForegroundColor Gray
    Write-Host "   EXPO_PUBLIC_API_URL=http://${windowsIp}:5000" -ForegroundColor Yellow
} else {
    Write-Host "   Could not auto-detect WiFi IP" -ForegroundColor Yellow
    Write-Host "   Run 'ipconfig' and look for 'Wireless LAN adapter Wi-Fi'" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🔍 To view port forwarding rules:" -ForegroundColor Cyan
Write-Host "   netsh interface portproxy show all" -ForegroundColor Gray
Write-Host ""
Write-Host "🗑️  To remove port forwarding:" -ForegroundColor Cyan
Write-Host "   netsh interface portproxy delete v4tov4 listenport=5000 listenaddress=0.0.0.0" -ForegroundColor Gray
Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Start Flask in WSL: cd my_flask_app && ./run_local.sh" -ForegroundColor Gray
Write-Host "   2. Test from phone browser: http://${windowsIp}:5000/health" -ForegroundColor Gray
Write-Host "   3. Update mobile app .env with the IP above" -ForegroundColor Gray
Write-Host "   4. Build and install mobile app on phone" -ForegroundColor Gray
Write-Host ""
