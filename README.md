## Installation

```
# Clone the repository
git clone https://github.com/0xs3fo/deponpm.git

cd deponpm

# Install dependencies
pip install -r requirements.txt

```


## Usage

### Cross-Platform Usage

```
python3 deponpm.py ./package.json
```

### Command Line Options

- `source`: GitHub URL or local path to `package.json` file (required when not using --file or --org)
- `--file`, `-f`: Text file containing multiple URLs (one per line) (required when not using source or --org)
- `--org`, `-o`: GitHub organization name to analyze all repositories (required when not using source or --file)
- `--token`, `-t`: GitHub personal access token (required for organization access)
- `--comprehensive`, `-c`: Perform comprehensive analysis including commit history and deleted commits
- `--complete`: Perform complete analysis: collect all repos, all commits, restore deleted commits, analyze all files, collect all dependencies, check claimed/unclaimed with detailed paths
- `--verbose`, `-v`: Enable verbose output (optional)

**Note**: You must provide either a `source`, use `--file`, or use `--org`, but not multiple at once.

### Examples

#### Check GitHub Repository
```bash
python3 deponpm.py https://github.com/-------/package.json
```

#### Check GitHub Organization
```bash
python3 deponpm.py --org microsoft --token YOUR_GITHUB_TOKEN
```

#### Check GitHub Organization with Comprehensive Analysis
```bash
python3 deponpm.py --org microsoft --token YOUR_GITHUB_TOKEN --comprehensive
```

#### Check GitHub Organization with Complete Analysis
```bash
python3 deponpm.py --org microsoft --token YOUR_GITHUB_TOKEN --complete
```

#### Check Local Package
```bash
python3 deponpm.py ./package.json
```

#### Check Multiple URLs from File
```bash
python3 deponpm.py --file urls.txt
```

#### Verbose Mode
```bash
python3 deponpm.py --verbose ./package.json
```

#### Verbose Mode with Multiple URLs
```bash
python3 deponpm.py --verbose --file urls.txt
```

#### Verbose Mode with Organization
```bash
python3 deponpm.py --verbose --org microsoft --token YOUR_GITHUB_TOKEN
```

#### Comprehensive Analysis with Verbose Output
```bash
python3 deponpm.py --verbose --org microsoft --token YOUR_GITHUB_TOKEN --comprehensive
```

## GitHub Token Setup

To analyze GitHub organizations, you need a personal access token:

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate a new token with the following permissions:
   - `repo` (Full control of private repositories)
   - `read:org` (Read org and team membership)
3. Use the token with the `--token` or `-t` option

## Output Format

The tool provides clear output showing:

- **Claimed Dependencies**: Packages that exist on the NPM registry
- **Unclaimed Dependencies**: Packages that don't exist or are not found
- **Summary**: Total count and breakdown

When using the `--file` option with multiple URLs or `--org` option with organizations, the tool provides:
- Individual results for each source (in verbose mode)
- Aggregated results showing unique dependencies across all sources
- Source tracking showing which repositories contain each dependency
- Repository-by-repository analysis for organizations

## Comprehensive Analysis Mode

The `--comprehensive` flag enables advanced analysis features:

### Features:
- **Commit History Analysis**: Analyzes the last 365 days of commits for dependency changes
- **Deleted Commits Detection**: Finds commits that are no longer in the main branch
- **Dependency Timeline**: Tracks how dependencies have changed over time
- **Cross-Repository Analysis**: Analyzes all repositories in an organization
- **Detailed Reporting**: Provides commit links, timestamps, and change details

### What it analyzes:
- Current dependencies in all repositories
- Historical dependency changes in commits
- Commits that modified package.json, package-lock.json, or yarn.lock files
- Deleted commits from feature branches or merged PRs
- Dependency usage patterns across the organization

### Output includes:
- Total repositories and commits analyzed
- Dependency changes over time
- Deleted commits analysis
- Recent dependency changes with commit links
- Comprehensive repository-by-repository breakdown

## Complete Analysis Mode

The `--complete` flag performs the most thorough analysis following this exact workflow:

### Workflow:
1. **Collect all repositories** from the organization
2. **Collect all commits** from all repositories (not limited by date)
3. **Restore all deleted commits** (commits not in main branch)
4. **Analyze all files** and repositories and commits for dependencies
5. **Collect all dependencies** from all sources
6. **Check for claimed and unclaimed** dependencies
7. **Provide detailed summary** with exact paths where each dependency was found

### What it analyzes:
- **All repositories** in the organization
- **All commits** from all repositories (up to 1000 per repo)
- **All deleted commits** from feature branches
- **All package.json files** in current state and commit history
- **All dependency changes** across the entire organization history
- **Complete dependency inventory** with source tracking

### Output includes:
- **Step-by-step progress** showing each phase of analysis
- **Total counts**: repositories, commits, deleted commits, dependencies
- **Detailed dependency breakdown** with exact paths
- **Claimed vs unclaimed** with source locations
- **Complete audit trail** of where each dependency was found


