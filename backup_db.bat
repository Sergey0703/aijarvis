@echo off
setlocal enabledelayedexpansion

:: 1. Robust Date Parsing
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set "dt=%%I"
set "YYYY=%dt:~0,4%"
set "MM=%dt:~4,2%"
set "DD=%dt:~6,2%"
set "BACKUP_DIR=mongodb_backup_%YYYY%%MM%%DD%"

:: 2. Connection Strings
set "SRV_URI=mongodb+srv://appadmin:fDXtmowD2Z2PWfYx@cluster0.1lssu.mongodb.net/cluster0?retryWrites=true&w=majority"
set "SHARD_URI=mongodb://appadmin:fDXtmowD2Z2PWfYx@cluster0-shard-00-00.1lssu.mongodb.net:27017,cluster0-shard-00-01.1lssu.mongodb.net:27017,cluster0-shard-00-02.1lssu.mongodb.net:27017/?ssl=true&replicaSet=atlas-6h6fu5-shard-0&authSource=admin&retryWrites=true&w=majority"

echo ========================================
echo        MONGODB CLUSTER DIAGNOSTICS
echo ========================================
echo.
echo [1/3] Testing SRV DNS resolution...
nslookup -q=SRV _mongodb._tcp.cluster0.1lssu.mongodb.net
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ATTENTION: DNS SRV resolution failed ^(Error 11001^).
    echo This means your ISP or local DNS blocks MongoDB Atlas records.
    echo ACTION: Change your Windows DNS to 8.8.8.8 ^(Google^) or 1.1.1.1 ^(Cloudflare^).
)

echo.
echo [2/3] Checking shard connectivity...
ping -n 1 cluster0-shard-00-00.1lssu.mongodb.net | find "Reply" > nul
if %ERRORLEVEL% NEQ 0 (
    echo Shard 00 is unreachable. 
) else (
    echo Shard 00 is ALIVE.
)

echo.
echo [3/3] Starting Backup...
echo Running: mongodump --uri="..." --out="%BACKUP_DIR%"
mongodump --uri="%SRV_URI%" --out="%BACKUP_DIR%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Backup saved to folder: %BACKUP_DIR%
) else (
    echo.
    echo [ERROR] Backup failed. 
    echo Check your MongoDB Atlas Network Access ^(WhiteList^).
)
echo.
pause
