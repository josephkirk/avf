# Clean previous builds
Remove-Item -Path "dist" -Recurse -ErrorAction SilentlyContinue
Remove-Item -Path "build" -Recurse -ErrorAction SilentlyContinue
Remove-Item -Path "*.egg-info" -Recurse -ErrorAction SilentlyContinue

# Create dist directory
New-Item -ItemType Directory -Force -Path "dist"

# Build package
uv pip install --upgrade build
python -m build

# Create wheel
uv pip wheel . -w dist
