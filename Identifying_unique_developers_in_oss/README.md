# SDMO Project 1 – Identifying unique developers in OSS

This project aims to identify duplicate developer identities across commits in open-source repositories,
based on the approach of Bird et al. (MSR 2006).
## developers
- Amirhossein Ayoubi
- Antti Moilanen
- Mashrabboy Abdusalomov
- Hina Shaukat
- Ritu Basak 

## Structure

- `src/` — all source code (collection, preprocessing, baseline, improved methods, evaluation)
- `data/` — input and output datasets
- `tests/` — unit tests for each module

## Setup

### Option 1: Local Development

1. Create a Python virtual environment (Python ≥ 3.10).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Option 2: Docker (recommended)

Prerequisites: Docker and Docker Compose installed.

Quick start (analyze a repo and get outputs in `output/`):

```bash
# Build the app image
docker compose build app

# Run analysis (replace repo URL and params as needed)
docker compose run --rm app \
  python src/main.py \
  --repo https://github.com/numpy/numpy \
  --threshold 0.85 \
  --max-commits 2000 \
  --max-pairs 1000

# Outputs will appear in ./output
```

Run unit tests with coverage (artifacts in project root):

```bash
docker compose run --rm -v "$PWD:/usr/src" app \
  sh -lc "pytest tests -q --junitxml=/usr/src/test-results.xml --cov=src --cov-report xml:/usr/src/coverage.xml"
```

SonarQube analysis (optional):

```bash
# Start SonarQube stack and wait (first run may take ~1-2 minutes)
docker compose up -d sonarqube postgres

# Generate reports (if you haven't already)
docker compose run --rm -v "$PWD:/usr/src" app \
  sh -lc "pytest tests -q --junitxml=/usr/src/test-results.xml --cov=src --cov-report xml:/usr/src/coverage.xml"
docker compose run --rm -v "$PWD:/usr/src" app \
  sh -lc 'pylint src || true' > pylint-report.txt

# Run the scanner
docker compose run --rm sonar-scanner

# SonarQube UI: http://localhost:9000
```

Cleanup (optional):

```bash
docker compose down
# Remove old orphaned scanner containers if warned
docker compose run --rm --remove-orphans sonar-scanner
```

## SonarQube Code Analysis

This project includes a preconfigured SonarQube stack (SonarQube + PostgreSQL + scanner). Default UI is at http://localhost:9000. The scanner reads `coverage.xml`, `test-results.xml`, and `pylint-report.txt` from the project root.

### SonarQube Configuration

The project includes a `sonar-project.properties` with:
- Project key: `unique-developers-oss`
- Source code: `src/` directory
- Tests: `tests/` directory
- Python version: 3.10
- Exclusions: `__pycache__`, `venv`, `output`, `data`, `reports` directories
 - Pylint report path: `pylint-report.txt`
 - Coverage and xUnit report paths: `coverage.xml`, `test-results.xml`

### Code Quality Reports

After running SonarQube analysis, you can:
1. View detailed code quality metrics in the SonarQube web interface
2. Download reports in various formats (PDF, CSV, etc.)
3. Set up quality gates for continuous integration
4. Track technical debt and code smells

## Usage

### Basic Usage

```bash
# Analyze a repository
python src/main.py --repo https://github.com/numpy/numpy --threshold 0.85

# With Docker Compose
docker compose run --rm app \
  python src/main.py --repo https://github.com/numpy/numpy --threshold 0.85
```

### Advanced Options

```bash
# Limit commits and pairs for faster analysis
python src/main.py --repo https://github.com/torvalds/linux --threshold 0.8 --max-commits 5000 --max-pairs 2000

# Skip extraction and use existing data (requires a prior run to create processed CSV)
python src/main.py --repo https://github.com/microsoft/vscode --skip-extraction --threshold 0.9

# Clean repository after analysis
python src/main.py --repo https://github.com/numpy/numpy --clean-repo
```

## Output

The analysis generates several output files in the `output/` directory:
- `{repo_name}_bird_duplicates.csv` - Duplicates found by Bird heuristic
- `{repo_name}_improved_duplicates.csv` - Duplicates found by improved heuristic
- `{repo_name}_summary.json` - Complete analysis results
- `{repo_name}_report.md` - Human-readable report

