# WellnessWay Diet Planner - Development Environment Setup Script (PowerShell)

Write-Host "🏥 WellnessWay Diet Planner - Development Setup" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# Check if Docker is installed
try {
    docker --version | Out-Null
    Write-Host "✅ Docker is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is installed
try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose is not installed. Please install Docker Compose first." -ForegroundColor Red
    exit 1
}

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ .env file created. Please update it with your configuration." -ForegroundColor Green
} else {
    Write-Host "✅ .env file already exists." -ForegroundColor Green
}

# Build and start services
Write-Host "🔨 Building Docker containers..." -ForegroundColor Yellow
docker-compose build

Write-Host "🚀 Starting services..." -ForegroundColor Yellow
docker-compose up -d

# Wait for services to be ready
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Check if services are healthy
Write-Host "🔍 Checking service health..." -ForegroundColor Yellow

# Check backend
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Backend is ready" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Backend is not ready" -ForegroundColor Red
}

# Check frontend
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Frontend is ready" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Frontend is not ready (this is normal if it's still starting)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Development environment setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📱 Access your application:" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "   Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "   API Documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "🛠️  Useful commands:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f    - View application logs" -ForegroundColor White
Write-Host "   docker-compose down       - Stop services" -ForegroundColor White
Write-Host "   docker-compose down -v    - Clean up everything" -ForegroundColor White
Write-Host ""
Write-Host "📚 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Update your .env file with API keys" -ForegroundColor White
Write-Host "   2. Start developing!" -ForegroundColor White