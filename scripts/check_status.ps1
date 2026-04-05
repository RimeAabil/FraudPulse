# FraudPulse Platform - System Health Diagnostics Tool
# 🚀 Run this script to verify your entire stack is healthy.

Clear-Host
Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
Write-Host "🕵️  FraudPulse : System Reliability Audit" -ForegroundColor Cyan
Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
Write-Host ""

$SuccessCount = 0
$TotalChecks = 6

# 1. Check Docker Containers
Write-Host "[1/6] Checking Docker Containers..." -NoNewline
$Containers = docker ps --format "{{.Names}}"
$RequiredContainers = @("kafka-1", "kafka-2", "kafka-3", "mongodb", "spark-master", "spark-consumer", "mlflow", "dashboard", "producer")
$Missing = @()

foreach ($c in $RequiredContainers) {
    if ($Containers -notcontains $c) { $Missing += $c }
}

if ($Missing.Count -eq 0) {
    Write-Host " ✅ All Up!" -ForegroundColor Green
    $SuccessCount++
} else {
    Write-Host " ❌ Missing: $($Missing -join ', ')" -ForegroundColor Red
}

# 2. Check Model Files
Write-Host "[2/6] Verifying Machine Learning Models..." -NoNewline
$ModelPath = "models/fraud_model.json"
if (Test-Path $ModelPath) {
    $Size = (Get-Item $ModelPath).Length / 1KB
    Write-Host " ✅ Found ($([math]::Round($Size, 1)) KB)" -ForegroundColor Green
    $SuccessCount++
} else {
    Write-Host " ❌ MISSING (Run: python src/ml/train.py)" -ForegroundColor Red
}

# 3. Check Kafka Topics
Write-Host "[3/6] Pinging Kafka Cluster..." -NoNewline
try {
    $Topics = docker exec kafka-1 /usr/bin/kafka-topics --bootstrap-server localhost:9092 --list 2>$null
    if ($Topics -like "*fraud-transactions*") {
        Write-Host " ✅ Topics Ready" -ForegroundColor Green
        $SuccessCount++
    } else {
        Write-Host " ⚠️  Waiting for Initialization..." -ForegroundColor Yellow
    }
} catch {
    Write-Host " ❌ Kafka Unreachable" -ForegroundColor Red
}

# 4. Check MLflow Health
Write-Host "[4/6] Auditing MLflow API..." -NoNewline
try {
    $Response = Invoke-WebRequest -Uri "http://localhost:5000" -Method Get -TimeoutSec 2 -UseBasicParsing 2>$null
    if ($Response.StatusCode -eq 200) {
        Write-Host " ✅ http://localhost:5000 (Up)" -ForegroundColor Green
        $SuccessCount++
    } else {
        Write-Host " ❌ Error ($($Response.StatusCode))" -ForegroundColor Red
    }
} catch {
    Write-Host " ❌ Offline" -ForegroundColor Red
}

# 5. Check Dashboard Health
Write-Host "[5/6] Checking Streamlit Dashboard..." -NoNewline
try {
    $Response = Invoke-WebRequest -Uri "http://localhost:8501" -Method Get -TimeoutSec 2 -UseBasicParsing 2>$null
    if ($Response.StatusCode -eq 200) {
        Write-Host " ✅ http://localhost:8501 (Up)" -ForegroundColor Green
        $SuccessCount++
    } else {
        Write-Host " ❌ Offline" -ForegroundColor Red
    }
} catch {
    Write-Host " ❌ Offline" -ForegroundColor Red
}

# 6. Check Spark Consumer Logs for Exceptions
Write-Host "[6/6] Reviewing Spark Consumer Health..." -NoNewline
$Logs = docker logs spark-consumer --tail 100 2>&1
if ($Logs -match "Exception" -or $Logs -match "Error" -or $Logs -match "terminated") {
    Write-Host " ❌ RESTART NEEDED (docker compose restart spark-consumer)" -ForegroundColor Red
} else {
    Write-Host " ✅ Query Running Smoothly" -ForegroundColor Green
    $SuccessCount++
}

Write-Host ""
Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
if ($SuccessCount -eq $TotalChecks) {
    Write-Host "🌟 SYSTEM STATUS: PERFECT (Ready for Presentation)" -ForegroundColor Green -BackgroundColor Black
} else {
    Write-Host "⚠️  SYSTEM STATUS: WARNING ($SuccessCount/$TotalChecks Successful)" -ForegroundColor Yellow
    Write-Host "Tip: Follow the guide in brain/SYSTEM_OPERATIONS_GUIDE.md" -ForegroundColor Gray
}
Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
Write-Host ""
