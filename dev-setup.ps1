# PowerShell script for setting up development environment
Write-Host "Setting up AVF development environment..."

# Check if Python 3.8+ is installed
$pythonVersion = (python --version 2>&1)
if (-not $?) {
    Write-Error "Python 3.8 or higher is required but not found!"
    exit 1
}
Write-Host "Found $pythonVersion"

# Create virtual environment using UV
Write-Host "Creating virtual environment..."
uv venv

# Activate virtual environment
Write-Host "Activating virtual environment..."
.\.venv\Scripts\Activate

# Install dependencies with UV
Write-Host "Installing dependencies..."
uv pip install -e ".[dev]"

# Install development tools
Write-Host "Installing development tools..."
uv pip install ruff black mypy pytest

Write-Host "Development environment setup complete!"
Write-Host "To activate the environment, run: .\.venv\Scripts\Activate"
