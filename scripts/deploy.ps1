# WellnessWay Deployment Script (PowerShell)
# Usage: .\deploy.ps1 -Environment staging -Version v1.0.0
# Example: .\deploy.ps1 -Environment production -Version latest

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("development", "staging", "production")]
    [string]$Environment = "staging",
    
    [Parameter(Mandatory=$false)]
    [string]$Version = "latest",
    
    [Parameter(Mandatory=$false)]
    [switch]$Rollback,
    
    [Parameter(Mandatory=$false)]
    [switch]$Help
)

# Configuration
$ProjectName = "health-buddy"
$Registry = "ghcr.io"
$RepoName = "health-buddy-diet-planner"

# Colors for output
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    White = "White"
}

# Logging functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Colors.Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Colors.Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Colors.Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Colors.Red
}

# Show help
function Show-Help {
    Write-Host "WellnessWay Deployment Script (PowerShell)" -ForegroundColor $Colors.Blue
    Write-Host ""
    Write-Host "Usage: .\deploy.ps1 -Environment <env> -Version <version>" -ForegroundColor $Colors.White
    Write-Host ""
    Write-Host "Parameters:" -ForegroundColor $Colors.White
    Write-Host "  -Environment    Target environment (development, staging, production)" -ForegroundColor $Colors.White
    Write-Host "  -Version        Version to deploy (default: latest)" -ForegroundColor $Colors.White
    Write-Host "  -Rollback       Rollback to previous version" -ForegroundColor $Colors.White
    Write-Host "  -Help           Show this help message" -ForegroundColor $Colors.White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor $Colors.White
    Write-Host "  .\deploy.ps1 -Environment staging -Version latest" -ForegroundColor $Colors.White
    Write-Host "  .\deploy.ps1 -Environment production -Version v1.0.0" -ForegroundColor $Colors.White
    Write-Host "  .\deploy.ps1 -Rollback" -ForegroundColor $Colors.White
}

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check if Docker is installed and running
    try {
        $dockerVersion = docker --version
        Write-Info "Docker found: $dockerVersion"
    }
    catch {
        Write-Error "Docker is not installed or not in PATH"
        exit 1
    }
    
    try {
        docker info | Out-Null
        Write-Info "Docker is running"
    }
    catch {
        Write-Error "Docker is not running"
        exit 1
    }
    
    # Check if Docker Compose is available
    try {
        $composeVersion = docker-compose --version
        Write-Info "Docker Compose found: $composeVersion"
    }
    catch {
        Write-Error "Docker Compose is not installed or not in PATH"
        exit 1
    }
    
    Write-Success "Prerequisites check passed"
}

# Load environment variables
function Set-Environment {
    Write-Info "Loading environment configuration..."
    
    switch ($Environment) {
        "development" {
            $script:EnvFile = ".env"
            $script:ComposeFile = "docker-compose.yml"
        }
        "staging" {
            $script:EnvFile = ".env.testing"
            $script:ComposeFile = "docker-compose.yml"
        }
        "production" {
            $script:EnvFile = ".env.production"
            $script:ComposeFile = "docker-compose.prod.yml"
        }
    }
    
    if (-not (Test-Path $script:EnvFile)) {
        Write-Error "Environment file $script:EnvFile not found"
        exit 1
    }
    
    # Load environment variables from file
    Get-Content $script:EnvFile | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
    
    Write-Success "Environment configuration loaded from $script:EnvFile"
}

# Pull latest images
function Get-DockerImages {
    Write-Info "Pulling latest Docker images..."
    
    try {
        if ($Version -ne "latest") {
            # Pull specific version
            docker pull "$Registry/$RepoName-backend:$Version"
            docker pull "$Registry/$RepoName-frontend:$Version"
        }
        else {
            # Pull latest images
            docker-compose -f $script:ComposeFile pull
        }
        Write-Success "Docker images pulled"
    }
    catch {
        Write-Warning "Some images could not be pulled: $_"
    }
}

# Run database migrations
function Invoke-DatabaseMigrations {
    Write-Info "Running database migrations..."
    
    try {
        # Start database service if not running
        docker-compose -f $script:ComposeFile up -d database
        
        # Wait for database to be ready
        Write-Info "Waiting for database to be ready..."
        Start-Sleep -Seconds 10
        
        # Run migrations
        docker-compose -f $script:ComposeFile run --rm backend alembic upgrade head
        
        Write-Success "Database migrations completed"
    }
    catch {
        Write-Error "Database migration failed: $_"
        throw
    }
}

# Deploy services
function Start-Services {
    Write-Info "Deploying services..."
    
    try {
        # Stop existing services
        docker-compose -f $script:ComposeFile down
        
        # Start services
        docker-compose -f $script:ComposeFile up -d
        
        Write-Success "Services deployed"
    }
    catch {
        Write-Error "Service deployment failed: $_"
        throw
    }
}

# Health check
function Test-ServiceHealth {
    Write-Info "Performing health checks..."
    
    # Wait for services to start
    Start-Sleep -Seconds 30
    
    # Check backend health
    $BackendUrl = "http://localhost:8000"
    if ($Environment -eq "production") {
        $BackendUrl = "https://api.wellnessway.com"
    }
    
    $backendHealthy = $false
    for ($i = 1; $i -le 10; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "$BackendUrl/health" -UseBasicParsing -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Success "Backend health check passed"
                $backendHealthy = $true
                break
            }
        }
        catch {
            Write-Warning "Backend health check failed (attempt $i/10)"
            Start-Sleep -Seconds 10
        }
    }
    
    if (-not $backendHealthy) {
        Write-Error "Backend health check failed after 10 attempts"
        throw "Backend health check failed"
    }
    
    # Check frontend
    $FrontendUrl = "http://localhost:3000"
    if ($Environment -eq "production") {
        $FrontendUrl = "https://wellnessway.com"
    }
    
    $frontendHealthy = $false
    for ($i = 1; $i -le 10; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $FrontendUrl -UseBasicParsing -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Success "Frontend health check passed"
                $frontendHealthy = $true
                break
            }
        }
        catch {
            Write-Warning "Frontend health check failed (attempt $i/10)"
            Start-Sleep -Seconds 10
        }
    }
    
    if (-not $frontendHealthy) {
        Write-Error "Frontend health check failed after 10 attempts"
        throw "Frontend health check failed"
    }
    
    Write-Success "All health checks passed"
}

# Cleanup old images
function Remove-OldImages {
    Write-Info "Cleaning up old Docker images..."
    
    try {
        # Remove dangling images
        docker image prune -f
        
        Write-Success "Cleanup completed"
    }
    catch {
        Write-Warning "Cleanup failed: $_"
    }
}

# Rollback function
function Invoke-Rollback {
    Write-Warning "Rolling back deployment..."
    
    try {
        # Stop current services
        docker-compose -f $script:ComposeFile down
        
        # Start with previous version
        docker-compose -f $script:ComposeFile up -d
        
        Write-Success "Rollback completed"
    }
    catch {
        Write-Error "Rollback failed: $_"
        throw
    }
}

# Main deployment function
function Start-Deployment {
    Write-Info "Starting deployment of WellnessWay Diet Planner"
    Write-Info "Environment: $Environment"
    Write-Info "Version: $Version"
    
    try {
        Test-Prerequisites
        Set-Environment
        Get-DockerImages
        Invoke-DatabaseMigrations
        Start-Services
        Test-ServiceHealth
        Remove-OldImages
        
        Write-Success "Deployment completed successfully!"
        Write-Info "Application is now running:"
        
        switch ($Environment) {
            "development" {
                Write-Info "  Frontend: http://localhost:3000"
                Write-Info "  Backend: http://localhost:8000"
                Write-Info "  API Docs: http://localhost:8000/docs"
            }
            "staging" {
                Write-Info "  Frontend: http://staging.wellnessway.com"
                Write-Info "  Backend: http://api-staging.wellnessway.com"
                Write-Info "  API Docs: http://api-staging.wellnessway.com/docs"
            }
            "production" {
                Write-Info "  Frontend: https://wellnessway.com"
                Write-Info "  Backend: https://api.wellnessway.com"
                Write-Info "  API Docs: https://api.wellnessway.com/docs"
            }
        }
    }
    catch {
        Write-Error "Deployment failed: $_"
        Write-Warning "Attempting rollback..."
        try {
            Invoke-Rollback
        }
        catch {
            Write-Error "Rollback also failed: $_"
        }
        exit 1
    }
}

# Main script execution
if ($Help) {
    Show-Help
    exit 0
}

if ($Rollback) {
    Set-Environment
    Invoke-Rollback
    exit 0
}

Start-Deployment