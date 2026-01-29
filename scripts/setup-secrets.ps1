# WellnessWay Diet Planner - Secrets Setup Script (PowerShell)
# This script helps set up secrets for different environments

param(
    [Parameter(Position=0)]
    [ValidateSet("dev", "development", "prod", "production", "test", "testing", "validate", "help")]
    [string]$Command = "help"
)

# Colors for output
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    White = "White"
}

# Function to print colored output
function Write-Status {
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

# Function to generate secure random string
function Generate-Secret {
    param([int]$Length = 32)
    
    $chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    $secret = ""
    for ($i = 0; $i -lt $Length; $i++) {
        $secret += $chars[(Get-Random -Maximum $chars.Length)]
    }
    return $secret
}

# Function to setup development secrets
function Setup-Development {
    Write-Status "Setting up development environment secrets..."
    
    $projectRoot = Split-Path -Parent $PSScriptRoot
    Set-Location $projectRoot
    
    # Copy example env file if .env doesn't exist
    if (-not (Test-Path ".env")) {
        Copy-Item ".env.example" ".env"
        Write-Success "Created .env from .env.example"
    } else {
        Write-Warning ".env already exists, skipping copy"
    }
    
    # Generate development secret key if using default
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "your-secret-key-here-change-in-production") {
        $devSecret = Generate-Secret -Length 32
        $envContent = $envContent -replace "your-secret-key-here-change-in-production", "dev-secret-key-$devSecret"
        Set-Content ".env" $envContent
        Write-Success "Generated development secret key"
    }
    
    Write-Success "Development secrets setup complete!"
    Write-Warning "Remember to set your OPENAI_API_KEY in .env for AI features"
}

# Function to setup production secrets
function Setup-Production {
    Write-Status "Setting up production environment secrets..."
    
    $projectRoot = Split-Path -Parent $PSScriptRoot
    Set-Location $projectRoot
    
    # Create production env file
    Copy-Item ".env.production" ".env.prod"
    
    # Generate secure values
    $secretKey = Generate-Secret -Length 32
    
    # Update production env file
    $envContent = Get-Content ".env.prod" -Raw
    $envContent = $envContent -replace "CHANGE_ME_IN_PRODUCTION", $secretKey
    Set-Content ".env.prod" $envContent
    
    Write-Success "Production .env.prod file created"
    Write-Warning "Please update the following in .env.prod:"
    Write-Warning "  - DATABASE_URL (production database)"
    Write-Warning "  - OPENAI_API_KEY"
    Write-Warning "  - SENTRY_DSN (optional)"
    Write-Warning "  - CORS_ORIGINS (your production domains)"
    Write-Warning "  - REDIS_URL (production Redis)"
}

# Function to setup testing secrets
function Setup-Testing {
    Write-Status "Setting up testing environment secrets..."
    
    $projectRoot = Split-Path -Parent $PSScriptRoot
    Set-Location $projectRoot
    
    # Copy testing env file
    Copy-Item ".env.testing" ".env.test"
    
    Write-Success "Testing environment setup complete!"
    Write-Status "Test database will be created automatically during tests"
}

# Function to validate secrets
function Validate-Secrets {
    Write-Status "Validating secrets configuration..."
    
    $projectRoot = Split-Path -Parent $PSScriptRoot
    $backendPath = Join-Path $projectRoot "backend"
    $validationScript = Join-Path $backendPath "scripts\validate_config.py"
    
    if (Test-Path $validationScript) {
        Set-Location $backendPath
        python scripts/validate_config.py
    } else {
        Write-Warning "Configuration validation script not found"
    }
}

# Function to show help
function Show-Help {
    Write-Host "WellnessWay Diet Planner - Secrets Setup Script" -ForegroundColor $Colors.White
    Write-Host ""
    Write-Host "Usage: .\setup-secrets.ps1 [COMMAND]" -ForegroundColor $Colors.White
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor $Colors.White
    Write-Host "  dev, development    Setup development environment secrets" -ForegroundColor $Colors.White
    Write-Host "  prod, production    Setup production environment secrets" -ForegroundColor $Colors.White
    Write-Host "  test, testing       Setup testing environment secrets" -ForegroundColor $Colors.White
    Write-Host "  validate           Validate current secrets configuration" -ForegroundColor $Colors.White
    Write-Host "  help               Show this help message" -ForegroundColor $Colors.White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor $Colors.White
    Write-Host "  .\setup-secrets.ps1 dev              # Setup development secrets" -ForegroundColor $Colors.White
    Write-Host "  .\setup-secrets.ps1 production       # Setup production secrets" -ForegroundColor $Colors.White
    Write-Host "  .\setup-secrets.ps1 validate         # Validate current configuration" -ForegroundColor $Colors.White
}

# Main script logic
switch ($Command.ToLower()) {
    { $_ -in @("dev", "development") } {
        Setup-Development
    }
    { $_ -in @("prod", "production") } {
        Setup-Production
    }
    { $_ -in @("test", "testing") } {
        Setup-Testing
    }
    "validate" {
        Validate-Secrets
    }
    "help" {
        Show-Help
    }
    default {
        Write-Error "Unknown command: $Command"
        Show-Help
        exit 1
    }
}