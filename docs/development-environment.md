# BioAlgoCompare Development Environment

This guide covers the setup and management of the BioAlgoCompare development environment.

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/bioalgocompare.git
   cd bioalgocompare
   ```

2. **Run the automated setup:**
   ```bash
   python scripts/setup_environment.py
   ```

   Or using the CLI (if already installed):
   ```bash
   bioalgo environment setup
   ```

3. **Activate the virtual environment:**
   ```bash
   # Linux/macOS
   source venv/bin/activate
   
   # Windows
   .\venv\Scripts\activate
   ```

4. **Verify installation:**
   ```bash
   bioalgo environment info
   bioalgo quality doctor
   ```

## Environment Management Commands

The `bioalgo environment` command group provides comprehensive environment management:

### Setup Command
```bash
# Full setup with all tools
bioalgo environment setup

# Minimal setup (faster, core dependencies only)
bioalgo environment setup --minimal

# Setup for Docker development
bioalgo environment setup --docker

# Force reinstall everything
bioalgo environment setup --force
```

### Information Commands
```bash
# Show detailed environment information
bioalgo environment info

# Export as JSON
bioalgo environment info --format json

# Generate comprehensive environment report
bioalgo environment report
bioalgo environment report --output my-env-report.md
```

### Dependencies Management
```bash
# Install/update all dependencies
bioalgo environment dependencies

# Check installed packages without installing
bioalgo environment dependencies --check
```

### Docker Development
```bash
# Start development container
bioalgo environment docker

# Start Jupyter Lab server
bioalgo environment docker --service jupyter

# Start testing environment
bioalgo environment docker --service test

# Build and start all services
bioalgo environment docker --service all --build
```

Available services:
- `dev`: Main development container
- `jupyter`: Jupyter Lab server (http://localhost:8888)
- `test`: Isolated testing environment
- `quality`: Quality checks container
- `all`: All services including PostgreSQL and Redis

### Interactive Shell
```bash
# Open Python shell with project context
bioalgo environment shell
```

This opens an IPython shell with commonly used modules pre-imported:
- All algorithms (HOA, FOA, EGTO, etc.)
- VRPProblem class
- Benchmarking utilities
- Visualization tools
- Results management

### Clean Environment
```bash
# Remove all generated files and caches
bioalgo environment clean
```

This removes:
- `__pycache__` directories
- `.pytest_cache`
- `.ruff_cache`
- `.mypy_cache`
- Build artifacts
- Coverage reports

## Manual Setup

If you prefer manual setup or need to customize the process:

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate  # Windows
```

### 2. Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install core dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Install project in editable mode
pip install -e .
```

### 3. Install Pre-commit Hooks
```bash
pre-commit install
```

### 4. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
```

### 5. Create Required Directories
```bash
mkdir -p results logs cache metadata checkpoints quality-reports docs/_build
```

## Docker Development

### Using Docker Compose

1. **Build images:**
   ```bash
   docker-compose build
   ```

2. **Start services:**
   ```bash
   # Start all services
   docker-compose up -d
   
   # Start specific service
   docker-compose up -d bioalgo-dev
   ```

3. **Access services:**
   - Development container: `docker exec -it bioalgo-dev bash`
   - Jupyter Lab: http://localhost:8888 (token: bioalgo2024)
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379

4. **Run commands in container:**
   ```bash
   docker-compose run --rm bioalgo-dev bioalgo run --algorithm hoa --instance E-n22-k4
   ```

### Using Devcontainer (VS Code)

1. Open project in VS Code
2. Install "Dev Containers" extension
3. Press F1 and select "Dev Containers: Reopen in Container"
4. VS Code will build and connect to the development container

## IDE Configuration

### VS Code

The setup script automatically configures VS Code with:
- Python interpreter path
- Linting with Ruff
- Formatting on save
- Test discovery with pytest
- Recommended extensions

Configuration files:
- `.vscode/settings.json`: Editor settings
- `.vscode/launch.json`: Debug configurations
- `.devcontainer/devcontainer.json`: Container development

### PyCharm

1. Open project
2. Configure interpreter: Settings → Project → Python Interpreter
3. Select virtual environment: `./venv/bin/python`
4. Enable pytest: Settings → Tools → Python Integrated Tools
5. Configure Ruff: Settings → External Tools

## Environment Variables

Key environment variables (configured in `.env`):

```bash
# Environment type
BIOALGO_ENV=development

# Logging
BIOALGO_LOG_LEVEL=INFO
BIOALGO_LOG_FILE=bioalgo.log

# Performance
BIOALGO_MAX_WORKERS=0  # Auto-detect CPUs
BIOALGO_MEMORY_LIMIT=8G

# Reproducibility
BIOALGO_DEFAULT_SEED=42
BIOALGO_ENFORCE_REPRODUCIBILITY=true

# Quality Gates
BIOALGO_QUALITY_REQUIRED_ONLY=false
BIOALGO_MAX_COMPLEXITY=15

# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost:5432/bioalgo
REDIS_URL=redis://localhost:6379/0
```

## Makefile Commands

The project includes a comprehensive Makefile:

```bash
# Setup
make setup
make install-dev

# Quality
make lint
make format
make typecheck
make test
make quality

# Docker
make docker-build
make docker-up
make docker-down

# Cleaning
make clean
make clean-all
```

## Troubleshooting

### Common Issues

1. **Import errors:**
   ```bash
   # Ensure project is installed in editable mode
   pip install -e .
   ```

2. **Pre-commit hook failures:**
   ```bash
   # Update hooks
   pre-commit autoupdate
   
   # Run manually
   pre-commit run --all-files
   ```

3. **Docker build errors:**
   ```bash
   # Clean and rebuild
   docker-compose down -v
   docker-compose build --no-cache
   ```

4. **Permission errors (Linux/macOS):**
   ```bash
   # Add user to docker group
   sudo usermod -aG docker $USER
   # Log out and back in
   ```

### Getting Help

```bash
# Check installation
bioalgo tools check-installation

# Environment doctor
bioalgo quality doctor

# Generate diagnostic report
bioalgo environment report --output diagnostic.md
```

## Best Practices

1. **Always use virtual environment**
   - Isolates dependencies
   - Prevents system conflicts
   - Easy to recreate

2. **Keep dependencies updated**
   ```bash
   # Check outdated packages
   pip list --outdated
   
   # Update all packages
   pip install --upgrade -r requirements.txt
   ```

3. **Use pre-commit hooks**
   - Ensures code quality
   - Prevents bad commits
   - Maintains consistency

4. **Regular environment cleanup**
   ```bash
   # Weekly cleanup
   bioalgo environment clean
   
   # Remove old results
   bioalgo tools clean --older-than 30
   ```

5. **Document environment changes**
   - Update requirements files
   - Document new dependencies
   - Update setup instructions

## Development Workflow

1. **Start your day:**
   ```bash
   # Activate environment
   source venv/bin/activate
   
   # Update dependencies
   git pull
   pip install -r requirements-dev.txt
   
   # Run quality checks
   bioalgo quality check
   ```

2. **Before committing:**
   ```bash
   # Run quality gates
   bioalgo quality gate
   
   # Run tests
   pytest
   ```

3. **End of day:**
   ```bash
   # Clean temporary files
   bioalgo environment clean
   
   # Generate status report
   bioalgo environment report
   ```

## Advanced Configuration

### Custom Docker Development

Create `docker-compose.override.yml` for local customizations:

```yaml
version: '3.8'

services:
  bioalgo-dev:
    environment:
      - BIOALGO_DEBUG=true
    volumes:
      - ./custom-scripts:/app/custom-scripts
```

### Performance Tuning

For large-scale experiments:

```bash
# Increase memory limit
export BIOALGO_MEMORY_LIMIT=16G

# Use all CPU cores
export BIOALGO_MAX_WORKERS=0

# Enable profiling
export BIOALGO_PROFILE=true
```

### Remote Development

For SSH/remote development:

1. **Install on remote server:**
   ```bash
   ssh user@server
   git clone https://github.com/yourusername/bioalgocompare.git
   cd bioalgocompare
   python scripts/setup_environment.py
   ```

2. **Use VS Code Remote-SSH:**
   - Install "Remote - SSH" extension
   - Connect to server
   - Open project folder

3. **Use Jupyter remotely:**
   ```bash
   # On server
   bioalgo environment docker --service jupyter
   
   # On local machine
   ssh -L 8888:localhost:8888 user@server
   # Access http://localhost:8888
   ```

## Contributing

When contributing to BioAlgoCompare:

1. **Setup development environment:**
   ```bash
   bioalgo environment setup
   ```

2. **Create feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

3. **Ensure quality:**
   ```bash
   bioalgo quality gate
   ```

4. **Update documentation:**
   - Update this guide if adding environment features
   - Document new dependencies
   - Update setup scripts if needed

For more information, see the [Contributing Guide](contributing.md).