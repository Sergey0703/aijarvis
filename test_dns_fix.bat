@echo off
echo ========================================
echo       ADVANCED DNS CONNECTIVITY TEST
echo ========================================
echo.

set "TARGET=cluster0.llssu.mongodb.net"
set "SRV_TARGET=_mongodb._tcp.cluster0.llssu.mongodb.net"

echo [TEST 1] Testing your CURRENT DNS...
nslookup %TARGET%
echo.

echo [TEST 2] Testing via GOOGLE DNS (8.8.8.8)...
nslookup %TARGET% 8.8.8.8
echo.

echo [TEST 3] Testing SRV RECORD via GOOGLE DNS...
nslookup -q=SRV %SRV_TARGET% 8.8.8.8
echo.

echo [TEST 4] Testing via CLOUDFLARE DNS (1.1.1.1)...
nslookup %TARGET% 1.1.1.1
echo.

echo ========================================
echo IF TEST 2, 3 or 4 PASSED:
echo Your current DNS (10.205.155.34) is blocking MongoDB.
echo.
echo SOLUTION: 
echo 1. Open Network Connections.
echo 2. Right-click your adapter -> Properties -> IPv4 -> Properties.
echo 3. Set Preferred DNS to 8.8.8.8.
echo 4. Set Alternate DNS to 1.1.1.1.
echo ========================================
pause
