#!/usr/bin/env python3
"""
DEPONPM - NPM Dependency Checker Tool

This tool checks package.json files for unclaimed or non-existent NPM dependencies.
It supports GitHub URLs, local file paths, and GitHub organization analysis.

Features:
- Check individual package.json files from GitHub URLs or local paths
- Analyze all repositories in a GitHub organization
- Extract dependencies from multiple sources
- Check for claimed and unclaimed dependencies
- Cross-platform compatible: Windows, Linux, macOS
"""

import argparse
import json
import sys
import re
import os
import platform
from typing import Dict, List, Set, Tuple, Optional
from urllib.parse import urlparse
import requests
from pathlib import Path


def print_banner():
    """Print the DEPONPM banner."""
    banner = """
    ================================================================
    
    ????????????????????? ?????????????????????????????????????????????  ????????????????????? ????????????   ?????????????????????   ?????????????????????   ?????????
    ??????????????????????????????????????????????????????????????????????????????????????????????????????????????????  ????????????????????????  ????????????????????????  ?????????
    ?????????  ???????????????????????????  ?????????????????????????????????   ??????????????????????????? ??????????????????????????? ??????????????????????????? ?????????
    ?????????  ???????????????????????????  ????????????????????? ?????????   ???????????????????????????????????????????????????????????????????????????????????????????????????
    ?????????????????????????????????????????????????????????     ???????????????????????????????????? ??????????????????????????? ??????????????????????????? ??????????????????
    ????????????????????? ?????????????????????????????????      ????????????????????? ?????????  ????????????????????????  ????????????????????????  ???????????????
   
              NPM Dependency Checker Tool
              
    ================================================================
    """
    print(banner)


class DEPONPM:
    """Main class for checking NPM dependencies."""
    
    def __init__(self, github_token: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DEPONPM/1.0'
        })
        self.github_token = github_token
        if github_token:
            self.session.headers.update({
                'Authorization': f'token {github_token}'
            })
    
    def fetch_github_raw_url(self, github_url: str) -> str:
        """
        Convert GitHub URL to raw file URL.
        
        Args:
            github_url: GitHub URL pointing to a file
            
        Returns:
            Raw file URL
        """
        # Pattern to match GitHub URLs
        pattern = r'https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)'
        match = re.match(pattern, github_url)
        
        if not match:
            raise ValueError(f"Invalid GitHub URL format: {github_url}")
        
        owner, repo, branch, file_path = match.groups()
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
        return raw_url
    
    def fetch_package_json_from_url(self, url: str) -> Dict:
        """
        Fetch and parse package.json from URL.
        
        Args:
            url: URL to package.json file
            
        Returns:
            Parsed package.json as dictionary
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            try:
                return json.loads(response.text)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in package.json: {e}")
                
        except requests.RequestException as e:
            raise ValueError(f"Failed to fetch package.json from {url}: {e}")
    
    def fetch_package_json_from_file(self, file_path: str) -> Dict:
        """
        Read and parse package.json from local file.
        
        Args:
            file_path: Path to local package.json file
            
        Returns:
            Parsed package.json as dictionary
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in package.json: {e}")
        except Exception as e:
            raise ValueError(f"Failed to read file {file_path}: {e}")
    
    def extract_dependencies(self, package_data: Dict) -> Set[str]:
        """
        Extract all dependency names from package.json.
        
        Args:
            package_data: Parsed package.json data
            
        Returns:
            Set of dependency names
        """
        dependencies = set()
        
        # Check different dependency types
        dependency_types = ['dependencies', 'devDependencies', 'peerDependencies']
        
        for dep_type in dependency_types:
            if dep_type in package_data and isinstance(package_data[dep_type], dict):
                dependencies.update(package_data[dep_type].keys())
        
        return dependencies
    
    def check_npm_package_exists(self, package_name: str) -> Tuple[bool, str]:
        """
        Check if a package exists on NPM registry.
        
        Args:
            package_name: Name of the package to check
            
        Returns:
            Tuple of (exists, status_message)
        """
        registry_url = f"https://registry.npmjs.com/{package_name}"
        
        try:
            response = self.session.get(registry_url, timeout=10)
            
            if response.status_code == 200:
                return True, "Package exists"
            elif response.status_code == 404:
                return False, "Package not found"
            else:
                return False, f"Unexpected status: {response.status_code}"
                
        except requests.RequestException as e:
            return False, f"Request failed: {e}"
    
    def check_dependencies(self, package_data: Dict) -> Dict[str, Dict]:
        """
        Check all dependencies against NPM registry.
        
        Args:
            package_data: Parsed package.json data
            
        Returns:
            Dictionary with dependency check results
        """
        dependencies = self.extract_dependencies(package_data)
        results = {}
        
        print(f"Checking {len(dependencies)} dependencies...")
        
        for i, dep_name in enumerate(sorted(dependencies), 1):
            print(f"[{i}/{len(dependencies)}] Checking {dep_name}...", end=' ')
            
            exists, status = self.check_npm_package_exists(dep_name)
            results[dep_name] = {
                'exists': exists,
                'status': status
            }
            
            print("OK" if exists else "FAIL")
        
        return results
    
    def read_urls_from_file(self, file_path: str) -> List[str]:
        """
        Read URLs from a text file.
        
        Args:
            file_path: Path to text file containing URLs
            
        Returns:
            List of URLs from the file
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        urls = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):  # Skip empty lines and comments
                        urls.append(line)
        except Exception as e:
            raise ValueError(f"Failed to read file {file_path}: {e}")
        
        if not urls:
            raise ValueError(f"No URLs found in file: {file_path}")
        
        return urls
    
    def get_github_repositories(self, org_name: str) -> List[Dict]:
        """
        Get all repositories from a GitHub organization.
        
        Args:
            org_name: Name of the GitHub organization
            
        Returns:
            List of repository information dictionaries
        """
        if not self.github_token:
            raise ValueError("GitHub token is required for organization access")
        
        repos = []
        page = 1
        per_page = 100
        
        print(f"Fetching repositories from organization: {org_name}")
        
        while True:
            url = f"https://api.github.com/orgs/{org_name}/repos"
            params = {
                'page': page,
                'per_page': per_page,
                'type': 'all'  # Include both public and private repos
            }
            
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                page_repos = response.json()
                
                if not page_repos:
                    break
                
                for repo in page_repos:
                    repo_info = {
                        'name': repo['name'],
                        'full_name': repo['full_name'],
                        'clone_url': repo['clone_url'],
                        'html_url': repo['html_url'],
                        'default_branch': repo['default_branch'],
                        'private': repo['private']
                    }
                    repos.append(repo_info)
                
                page += 1
                
            except requests.RequestException as e:
                raise ValueError(f"Failed to fetch repositories from organization {org_name}: {e}")
        
        print(f"Found {len(repos)} repositories")
        return repos
    
    def fetch_package_json_from_repo(self, repo_info: Dict) -> Optional[Dict]:
        """
        Fetch package.json from a GitHub repository.
        
        Args:
            repo_info: Repository information dictionary
            
        Returns:
            Parsed package.json as dictionary, or None if not found
        """
        try:
            # Try to get package.json from the default branch
            url = f"https://api.github.com/repos/{repo_info['full_name']}/contents/package.json"
            params = {'ref': repo_info['default_branch']}
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                content_data = response.json()
                if content_data.get('type') == 'file':
                    # Decode base64 content
                    import base64
                    content = base64.b64decode(content_data['content']).decode('utf-8')
                    package_data = json.loads(content)
                    return package_data
            
            elif response.status_code == 404:
                # package.json not found in root, try to find it
                url = f"https://api.github.com/repos/{repo_info['full_name']}/contents"
                params = {'ref': repo_info['default_branch']}
                
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    contents = response.json()
                    for item in contents:
                        if item.get('name') == 'package.json' and item.get('type') == 'file':
                            # Found package.json, fetch its content
                            content_response = self.session.get(item['download_url'], timeout=30)
                            if content_response.status_code == 200:
                                package_data = json.loads(content_response.text)
                                return package_data
                
                return None
            else:
                print(f"  Error accessing repository {repo_info['name']}: HTTP {response.status_code}")
                return None
                
        except requests.RequestException as e:
            print(f"  Error accessing repository {repo_info['name']}: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"  Error parsing package.json from {repo_info['name']}: {e}")
            return None
    
    def process_github_organization(self, org_name: str) -> Dict[str, Dict[str, Dict]]:
        """
        Process all repositories in a GitHub organization.
        
        Args:
            org_name: Name of the GitHub organization
            
        Returns:
            Dictionary mapping repository names to their dependency results
        """
        repos = self.get_github_repositories(org_name)
        all_results = {}
        
        print(f"\nProcessing {len(repos)} repositories...")
        
        for i, repo_info in enumerate(repos, 1):
            print(f"\n[{i}/{len(repos)}] Processing repository: {repo_info['name']}")
            
            package_data = self.fetch_package_json_from_repo(repo_info)
            
            if package_data:
                print(f"  Found package.json - {package_data.get('name', 'Unknown')} v{package_data.get('version', 'Unknown')}")
                
                # Check dependencies
                results = self.check_dependencies(package_data)
                all_results[repo_info['name']] = results
            else:
                print(f"  No package.json found")
        
        return all_results
    
    def get_repository_commits(self, repo_info: Dict, since_days: int = 365) -> List[Dict]:
        """
        Get commit history for a repository.
        
        Args:
            repo_info: Repository information dictionary
            since_days: Number of days to look back for commits
            
        Returns:
            List of commit information dictionaries
        """
        commits = []
        page = 1
        per_page = 100
        
        # Calculate since date
        from datetime import datetime, timedelta
        since_date = datetime.now() - timedelta(days=since_days)
        since_str = since_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        print(f"  Fetching commits from {since_date.strftime('%Y-%m-%d')}...")
        
        while True:
            url = f"https://api.github.com/repos/{repo_info['full_name']}/commits"
            params = {
                'page': page,
                'per_page': per_page,
                'since': since_str
            }
            
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                page_commits = response.json()
                
                if not page_commits:
                    break
                
                for commit in page_commits:
                    commit_info = {
                        'sha': commit['sha'],
                        'message': commit['commit']['message'],
                        'author': commit['commit']['author']['name'],
                        'date': commit['commit']['author']['date'],
                        'url': commit['html_url']
                    }
                    commits.append(commit_info)
                
                page += 1
                
                # Limit to prevent excessive API calls
                if len(commits) >= 1000:
                    break
                    
            except requests.RequestException as e:
                print(f"  Error fetching commits: {e}")
                break
        
        print(f"  Found {len(commits)} commits")
        return commits
    
    def analyze_commit_for_dependencies(self, repo_info: Dict, commit_sha: str) -> Optional[Dict]:
        """
        Analyze a specific commit for dependency changes.
        
        Args:
            repo_info: Repository information dictionary
            commit_sha: SHA of the commit to analyze
            
        Returns:
            Dictionary with dependency information or None
        """
        try:
            # Get commit details
            url = f"https://api.github.com/repos/{repo_info['full_name']}/commits/{commit_sha}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            commit_data = response.json()
            
            # Look for package.json changes in the commit
            package_json_changes = []
            
            for file_change in commit_data.get('files', []):
                filename = file_change.get('filename', '')
                if filename.endswith('package.json') or filename.endswith('package-lock.json') or filename.endswith('yarn.lock'):
                    change_info = {
                        'filename': filename,
                        'status': file_change.get('status', ''),
                        'additions': file_change.get('additions', 0),
                        'deletions': file_change.get('deletions', 0),
                        'changes': file_change.get('changes', 0),
                        'patch': file_change.get('patch', '')
                    }
                    package_json_changes.append(change_info)
            
            if package_json_changes:
                return {
                    'commit_sha': commit_sha,
                    'message': commit_data['commit']['message'],
                    'date': commit_data['commit']['author']['date'],
                    'author': commit_data['commit']['author']['name'],
                    'url': commit_data['html_url'],
                    'changes': package_json_changes
                }
            
            return None
            
        except requests.RequestException as e:
            print(f"    Error analyzing commit {commit_sha}: {e}")
            return None
    
    def get_deleted_commits(self, repo_info: Dict) -> List[Dict]:
        """
        Get information about deleted commits (commits that are no longer in the main branch).
        
        Args:
            repo_info: Repository information dictionary
            
        Returns:
            List of deleted commit information
        """
        deleted_commits = []
        
        try:
            # Get all branches
            url = f"https://api.github.com/repos/{repo_info['full_name']}/branches"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            branches = response.json()
            
            # Get commits from all branches
            all_commits = set()
            branch_commits = {}
            
            for branch in branches:
                branch_name = branch['name']
                branch_url = f"https://api.github.com/repos/{repo_info['full_name']}/commits"
                params = {'sha': branch_name, 'per_page': 100}
                
                try:
                    branch_response = self.session.get(branch_url, params=params, timeout=30)
                    branch_response.raise_for_status()
                    commits = branch_response.json()
                    
                    branch_commits[branch_name] = commits
                    for commit in commits:
                        all_commits.add(commit['sha'])
                        
                except requests.RequestException:
                    continue
            
            # Find commits that might be "deleted" (not in main branch)
            main_branch = repo_info['default_branch']
            main_commits = set()
            
            if main_branch in branch_commits:
                for commit in branch_commits[main_branch]:
                    main_commits.add(commit['sha'])
            
            # Commits not in main branch could be considered "deleted"
            for commit_sha in all_commits:
                if commit_sha not in main_commits:
                    # Find which branch this commit is in
                    for branch_name, commits in branch_commits.items():
                        if branch_name != main_branch:
                            for commit in commits:
                                if commit['sha'] == commit_sha:
                                    deleted_commits.append({
                                        'sha': commit_sha,
                                        'message': commit['commit']['message'],
                                        'date': commit['commit']['author']['date'],
                                        'author': commit['commit']['author']['name'],
                                        'branch': branch_name,
                                        'url': commit['html_url']
                                    })
                                    break
            
        except requests.RequestException as e:
            print(f"  Error fetching deleted commits: {e}")
        
        return deleted_commits
    
    def comprehensive_repository_analysis(self, repo_info: Dict) -> Dict:
        """
        Perform comprehensive analysis of a repository including commit history.
        
        Args:
            repo_info: Repository information dictionary
            
        Returns:
            Dictionary with comprehensive analysis results
        """
        analysis = {
            'repo_name': repo_info['name'],
            'current_dependencies': {},
            'commit_history': [],
            'deleted_commits': [],
            'dependency_timeline': [],
            'total_commits_analyzed': 0
        }
        
        print(f"  Performing comprehensive analysis...")
        
        # Get current package.json
        current_package = self.fetch_package_json_from_repo(repo_info)
        if current_package:
            current_deps = self.extract_dependencies(current_package)
            analysis['current_dependencies'] = {dep: True for dep in current_deps}
        
        # Get commit history
        commits = self.get_repository_commits(repo_info)
        analysis['total_commits_analyzed'] = len(commits)
        
        # Analyze recent commits for dependency changes
        dependency_changes = []
        for i, commit in enumerate(commits[:50]):  # Limit to last 50 commits for performance
            if i % 10 == 0:
                print(f"    Analyzing commit {i+1}/{min(50, len(commits))}...")
            
            commit_analysis = self.analyze_commit_for_dependencies(repo_info, commit['sha'])
            if commit_analysis:
                dependency_changes.append(commit_analysis)
        
        analysis['commit_history'] = dependency_changes
        
        # Get deleted commits
        deleted_commits = self.get_deleted_commits(repo_info)
        analysis['deleted_commits'] = deleted_commits
        
        return analysis
    
    def complete_organization_analysis(self, org_name: str) -> Dict:
        """
        Complete analysis following the exact workflow:
        1. Collect all repos and all commits
        2. Restore all deleted commits
        3. Analyze all files and repos and commits
        4. Collect all dependencies
        5. Check for claimed and unclaimed
        6. Provide detailed summary with paths
        """
        print(f"\n{'='*80}")
        print(f"COMPLETE ORGANIZATION ANALYSIS: {org_name}")
        print(f"{'='*80}")
        
        # Step 1: Collect all repositories
        print(f"\nSTEP 1: Collecting all repositories...")
        repos = self.get_github_repositories(org_name)
        print(f"[OK] Found {len(repos)} repositories")
        
        # Step 2: Collect all commits from all repositories
        print(f"\nSTEP 2: Collecting all commits from all repositories...")
        all_commits = {}
        total_commits = 0
        
        for i, repo_info in enumerate(repos, 1):
            print(f"  [{i}/{len(repos)}] Collecting commits from: {repo_info['name']}")
            commits = self.get_all_repository_commits(repo_info)
            all_commits[repo_info['name']] = commits
            total_commits += len(commits)
            print(f"    [OK] Found {len(commits)} commits")
        
        print(f"[OK] Total commits collected: {total_commits}")
        
        # Step 3: Restore deleted commits
        print(f"\nSTEP 3: Restoring deleted commits...")
        all_deleted_commits = {}
        total_deleted = 0
        
        for i, repo_info in enumerate(repos, 1):
            print(f"  [{i}/{len(repos)}] Restoring deleted commits from: {repo_info['name']}")
            deleted_commits = self.get_deleted_commits(repo_info)
            all_deleted_commits[repo_info['name']] = deleted_commits
            total_deleted += len(deleted_commits)
            print(f"    [OK] Restored {len(deleted_commits)} deleted commits")
        
        print(f"[OK] Total deleted commits restored: {total_deleted}")
        
        # Step 4: Analyze all files and collect dependencies
        print(f"\nSTEP 4: Analyzing all files and collecting dependencies...")
        all_dependencies = {}
        dependency_sources = {}  # Track where each dependency was found
        
        for i, repo_info in enumerate(repos, 1):
            print(f"  [{i}/{len(repos)}] Analyzing files from: {repo_info['name']}")
            
            # Analyze current files
            current_deps = self.analyze_repository_files(repo_info)
            if current_deps:
                all_dependencies[repo_info['name']] = current_deps
                for dep in current_deps:
                    if dep not in dependency_sources:
                        dependency_sources[dep] = []
                    dependency_sources[dep].append(f"{repo_info['name']} (current)")
            
            # Analyze commits for dependency changes
            repo_commits = all_commits.get(repo_info['name'], [])
            for commit in repo_commits[:100]:  # Limit to prevent excessive API calls
                commit_deps = self.analyze_commit_dependencies(repo_info, commit['sha'])
                if commit_deps:
                    for dep in commit_deps:
                        if dep not in dependency_sources:
                            dependency_sources[dep] = []
                        dependency_sources[dep].append(f"{repo_info['name']} (commit: {commit['sha'][:8]})")
            
            # Analyze deleted commits
            deleted_commits = all_deleted_commits.get(repo_info['name'], [])
            for commit in deleted_commits[:50]:  # Limit deleted commits analysis
                commit_deps = self.analyze_commit_dependencies(repo_info, commit['sha'])
                if commit_deps:
                    for dep in commit_deps:
                        if dep not in dependency_sources:
                            dependency_sources[dep] = []
                        dependency_sources[dep].append(f"{repo_info['name']} (deleted: {commit['sha'][:8]})")
        
        print(f"[OK] Dependency analysis completed")
        
        # Step 5: Check claimed and unclaimed
        print(f"\nSTEP 5: Checking claimed and unclaimed dependencies...")
        claimed_deps = []
        unclaimed_deps = []
        
        unique_deps = set(dependency_sources.keys())
        print(f"  Checking {len(unique_deps)} unique dependencies...")
        
        for i, dep in enumerate(sorted(unique_deps), 1):
            print(f"  [{i}/{len(unique_deps)}] Checking {dep}...", end=' ')
            exists, status = self.check_npm_package_exists(dep)
            
            if exists:
                claimed_deps.append((dep, dependency_sources[dep]))
                print("CLAIMED")
            else:
                unclaimed_deps.append((dep, dependency_sources[dep], status))
                print("UNCLAIMED")
        
        # Step 6: Final summary
        print(f"\nSTEP 6: Generating final summary...")
        self.print_complete_analysis_summary(
            org_name, repos, total_commits, total_deleted, 
            claimed_deps, unclaimed_deps, dependency_sources
        )
        
        return {
            'organization': org_name,
            'repositories': len(repos),
            'total_commits': total_commits,
            'total_deleted_commits': total_deleted,
            'total_dependencies': len(unique_deps),
            'claimed_dependencies': len(claimed_deps),
            'unclaimed_dependencies': len(unclaimed_deps),
            'claimed_deps': claimed_deps,
            'unclaimed_deps': unclaimed_deps,
            'dependency_sources': dependency_sources
        }
    
    def get_all_repository_commits(self, repo_info: Dict) -> List[Dict]:
        """
        Get ALL commits from a repository (not limited by date).
        """
        commits = []
        page = 1
        per_page = 100
        
        while True:
            url = f"https://api.github.com/repos/{repo_info['full_name']}/commits"
            params = {
                'page': page,
                'per_page': per_page
            }
            
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                page_commits = response.json()
                
                if not page_commits:
                    break
                
                for commit in page_commits:
                    commit_info = {
                        'sha': commit['sha'],
                        'message': commit['commit']['message'],
                        'author': commit['commit']['author']['name'],
                        'date': commit['commit']['author']['date'],
                        'url': commit['html_url']
                    }
                    commits.append(commit_info)
                
                page += 1
                
                # Limit to prevent excessive API calls (adjust as needed)
                if len(commits) >= 1000:
                    break
                    
            except requests.RequestException as e:
                print(f"    Error fetching commits: {e}")
                break
        
        return commits
    
    def analyze_repository_files(self, repo_info: Dict) -> List[str]:
        """
        Analyze all files in a repository for dependencies.
        """
        dependencies = []
        
        try:
            # Get current package.json
            package_data = self.fetch_package_json_from_repo(repo_info)
            if package_data:
                deps = self.extract_dependencies(package_data)
                dependencies.extend(deps)
            
            # Look for other package manager files
            url = f"https://api.github.com/repos/{repo_info['full_name']}/contents"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                contents = response.json()
                for item in contents:
                    filename = item.get('name', '')
                    if filename in ['yarn.lock', 'pnpm-lock.yaml', 'package-lock.json']:
                        # These files contain dependency information
                        # For now, we'll focus on package.json analysis
                        pass
            
        except requests.RequestException as e:
            print(f"    Error analyzing files: {e}")
        
        return dependencies
    
    def analyze_commit_dependencies(self, repo_info: Dict, commit_sha: str) -> List[str]:
        """
        Analyze a specific commit for dependencies.
        """
        dependencies = []
        
        try:
            url = f"https://api.github.com/repos/{repo_info['full_name']}/commits/{commit_sha}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            commit_data = response.json()
            
            # Look for package.json changes
            for file_change in commit_data.get('files', []):
                filename = file_change.get('filename', '')
                if filename.endswith('package.json'):
                    patch = file_change.get('patch', '')
                    if patch:
                        # Extract dependencies from patch (simplified)
                        deps = self.extract_dependencies_from_patch(patch)
                        dependencies.extend(deps)
            
        except requests.RequestException as e:
            pass  # Skip errors for individual commits
        
        return dependencies
    
    def extract_dependencies_from_patch(self, patch: str) -> List[str]:
        """
        Extract dependency names from a git patch.
        """
        dependencies = []
        lines = patch.split('\n')
        
        for line in lines:
            if line.startswith('+') and '"' in line and ':' in line:
                # Look for dependency lines like: +    "package-name": "version"
                try:
                    if line.strip().startswith('+    "') and '":' in line:
                        dep_name = line.split('"')[1]
                        if dep_name and not dep_name.startswith('@'):
                            dependencies.append(dep_name)
                except:
                    pass
        
        return dependencies
    
    def print_complete_analysis_summary(self, org_name: str, repos: List[Dict], 
                                      total_commits: int, total_deleted: int,
                                      claimed_deps: List, unclaimed_deps: List, 
                                      dependency_sources: Dict):
        """
        Print the final comprehensive summary.
        """
        print(f"\n{'='*100}")
        print(f"FINAL COMPREHENSIVE ANALYSIS SUMMARY")
        print(f"{'='*100}")
        
        print(f"\nORGANIZATION: {org_name}")
        print(f"REPOSITORIES ANALYZED: {len(repos)}")
        print(f"TOTAL COMMITS COLLECTED: {total_commits}")
        print(f"TOTAL DELETED COMMITS RESTORED: {total_deleted}")
        
        total_unique_deps = len(set(dependency_sources.keys()))
        print(f"TOTAL UNIQUE DEPENDENCIES FOUND: {total_unique_deps}")
        print(f"CLAIMED DEPENDENCIES: {len(claimed_deps)}")
        print(f"UNCLAIMED DEPENDENCIES: {len(unclaimed_deps)}")
        
        print(f"\n{'='*100}")
        print(f"DETAILED DEPENDENCY BREAKDOWN")
        print(f"{'='*100}")
        
        print(f"\nCLAIMED DEPENDENCIES ({len(claimed_deps)}):")
        for dep, sources in claimed_deps:
            print(f"\n  [CLAIMED] {dep}")
            for source in sources:
                print(f"    -> Found in: {source}")
        
        print(f"\nUNCLAIMED DEPENDENCIES ({len(unclaimed_deps)}):")
        for dep, sources, status in unclaimed_deps:
            print(f"\n  [UNCLAIMED] {dep} ({status})")
            for source in sources:
                print(f"    -> Found in: {source}")
        
        print(f"\n{'='*100}")
        print(f"ANALYSIS COMPLETE")
        print(f"{'='*100}")
    
    def process_github_organization_comprehensive(self, org_name: str) -> Dict[str, Dict]:
        """
        Process all repositories in a GitHub organization with comprehensive analysis.
        
        Args:
            org_name: Name of the GitHub organization
            
        Returns:
            Dictionary mapping repository names to their comprehensive analysis results
        """
        repos = self.get_github_repositories(org_name)
        all_analyses = {}
        
        print(f"\nPerforming comprehensive analysis on {len(repos)} repositories...")
        
        for i, repo_info in enumerate(repos, 1):
            print(f"\n[{i}/{len(repos)}] Comprehensive analysis: {repo_info['name']}")
            
            analysis = self.comprehensive_repository_analysis(repo_info)
            all_analyses[repo_info['name']] = analysis
        
        return all_analyses
    
    def print_comprehensive_results(self, all_analyses: Dict[str, Dict]):
        """
        Print comprehensive analysis results.
        
        Args:
            all_analyses: Dictionary mapping repository names to their analysis results
        """
        print("\n" + "="*100)
        print("COMPREHENSIVE DEPENDENCY ANALYSIS RESULTS")
        print("="*100)
        
        total_repos = len(all_analyses)
        repos_with_deps = sum(1 for analysis in all_analyses.values() if analysis['current_dependencies'])
        total_commits_analyzed = sum(analysis['total_commits_analyzed'] for analysis in all_analyses.values())
        
        print(f"\nOVERVIEW:")
        print(f"  Total repositories analyzed: {total_repos}")
        print(f"  Repositories with dependencies: {repos_with_deps}")
        print(f"  Total commits analyzed: {total_commits_analyzed}")
        
        # Aggregate all current dependencies
        all_current_deps = set()
        for analysis in all_analyses.values():
            all_current_deps.update(analysis['current_dependencies'].keys())
        
        print(f"  Total unique dependencies found: {len(all_current_deps)}")
        
        # Show dependency changes over time
        print(f"\nDEPENDENCY CHANGES OVER TIME:")
        total_dependency_changes = 0
        for repo_name, analysis in all_analyses.items():
            if analysis['commit_history']:
                changes_count = len(analysis['commit_history'])
                total_dependency_changes += changes_count
                print(f"  {repo_name}: {changes_count} commits with dependency changes")
        
        print(f"  Total dependency-related commits: {total_dependency_changes}")
        
        # Show deleted commits
        print(f"\nDELETED COMMITS ANALYSIS:")
        total_deleted_commits = 0
        for repo_name, analysis in all_analyses.items():
            if analysis['deleted_commits']:
                deleted_count = len(analysis['deleted_commits'])
                total_deleted_commits += deleted_count
                print(f"  {repo_name}: {deleted_count} deleted commits")
        
        print(f"  Total deleted commits found: {total_deleted_commits}")
        
        # Detailed repository analysis
        print(f"\nDETAILED REPOSITORY ANALYSIS:")
        for repo_name, analysis in all_analyses.items():
            print(f"\n  Repository: {repo_name}")
            print(f"    Current dependencies: {len(analysis['current_dependencies'])}")
            print(f"    Commits analyzed: {analysis['total_commits_analyzed']}")
            print(f"    Dependency changes: {len(analysis['commit_history'])}")
            print(f"    Deleted commits: {len(analysis['deleted_commits'])}")
            
            # Show recent dependency changes
            if analysis['commit_history']:
                print(f"    Recent dependency changes:")
                for change in analysis['commit_history'][:5]:  # Show last 5 changes
                    date_str = change['date'][:10]  # Just the date part
                    print(f"      - {date_str}: {change['message'][:60]}...")
                    print(f"        Commit: {change['url']}")
    
    def print_results(self, results: Dict[str, Dict], source_name: str = ""):
        """
        Print formatted results.
        
        Args:
            results: Dictionary with dependency check results
            source_name: Name of the source being processed
        """
        claimed = []
        unclaimed = []
        
        for dep_name, info in results.items():
            if info['exists']:
                claimed.append(dep_name)
            else:
                unclaimed.append((dep_name, info['status']))
        
        if source_name:
            print(f"\n" + "="*60)
            print(f"RESULTS FOR: {source_name}")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("DEPENDENCY CHECK RESULTS")
            print("="*60)
        
        print(f"\nCLAIMED DEPENDENCIES ({len(claimed)}):")
        if claimed:
            for dep in sorted(claimed):
                print(f"  - {dep}")
        else:
            print("  None")
        
        print(f"\nUNCLAIMED DEPENDENCIES ({len(unclaimed)}):")
        if unclaimed:
            for dep, status in sorted(unclaimed):
                print(f"  - {dep} ({status})")
        else:
            print("  None")
        
        print(f"\nSUMMARY:")
        print(f"  Total dependencies: {len(results)}")
        print(f"  Claimed: {len(claimed)}")
        print(f"  Unclaimed: {len(unclaimed)}")
    
    def print_aggregated_results(self, all_results: Dict[str, Dict[str, Dict]]):
        """
        Print aggregated results from multiple sources.
        
        Args:
            all_results: Dictionary mapping source names to their results
        """
        # Aggregate all dependencies
        all_deps = set()
        dep_sources = {}  # Track which source each dependency comes from
        
        for source_name, results in all_results.items():
            for dep_name in results.keys():
                all_deps.add(dep_name)
                if dep_name not in dep_sources:
                    dep_sources[dep_name] = []
                dep_sources[dep_name].append(source_name)
        
        # Check each unique dependency
        claimed = []
        unclaimed = []
        
        for dep_name in sorted(all_deps):
            # Check if dependency exists in any source
            exists_anywhere = any(results[dep_name]['exists'] for results in all_results.values() if dep_name in results)
            
            if exists_anywhere:
                claimed.append((dep_name, dep_sources[dep_name]))
            else:
                # Get status from first source that has this dependency
                first_source = dep_sources[dep_name][0]
                status = all_results[first_source][dep_name]['status']
                unclaimed.append((dep_name, status, dep_sources[dep_name]))
        
        print("\n" + "="*80)
        print("AGGREGATED DEPENDENCY CHECK RESULTS")
        print("="*80)
        
        print(f"\nCLAIMED DEPENDENCIES ({len(claimed)}):")
        if claimed:
            for dep, sources in claimed:
                sources_str = ", ".join(sources)
                print(f"  - {dep} (from: {sources_str})")
        else:
            print("  None")
        
        print(f"\nUNCLAIMED DEPENDENCIES ({len(unclaimed)}):")
        if unclaimed:
            for dep, status, sources in unclaimed:
                sources_str = ", ".join(sources)
                print(f"  - {dep} ({status}) (from: {sources_str})")
        else:
            print("  None")
        
        print(f"\nAGGREGATED SUMMARY:")
        print(f"  Total unique dependencies: {len(all_deps)}")
        print(f"  Claimed: {len(claimed)}")
        print(f"  Unclaimed: {len(unclaimed)}")
        print(f"  Sources processed: {len(all_results)}")


def main():
    """Main entry point."""
    # Print banner
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="DEPONPM - Check package.json for unclaimed NPM dependencies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check from GitHub URL
  deponpm https://github.com/user/repo/blob/main/package.json
  
  # Check local file
  deponpm ./package.json
  
  # Check multiple URLs from file
  deponpm --file urls.txt
  
  # Check GitHub organization (requires token)
  deponpm --org microsoft --token YOUR_GITHUB_TOKEN
  
  # Comprehensive analysis with commit history
  deponpm --org microsoft --token YOUR_GITHUB_TOKEN --comprehensive
  
  # Complete analysis (collect all repos, commits, restore deleted, analyze all)
  deponpm --org microsoft --token YOUR_GITHUB_TOKEN --complete
  
  # Check with verbose output
  deponpm --verbose ./package.json
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        'source',
        nargs='?',
        help='GitHub URL or local path to package.json file'
    )
    group.add_argument(
        '--file', '-f',
        help='Text file containing multiple URLs (one per line)'
    )
    group.add_argument(
        '--org', '-o',
        help='GitHub organization name to analyze all repositories'
    )
    
    parser.add_argument(
        '--token', '-t',
        help='GitHub personal access token (required for organization access)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--comprehensive', '-c',
        action='store_true',
        help='Perform comprehensive analysis including commit history and deleted commits'
    )
    
    parser.add_argument(
        '--complete',
        action='store_true',
        help='Perform complete analysis: collect all repos, all commits, restore deleted commits, analyze all files, collect all dependencies, check claimed/unclaimed with detailed paths'
    )
    
    args = parser.parse_args()
    
    # Initialize checker with GitHub token if provided
    checker = DEPONPM(github_token=args.token)
    
    try:
        if args.org:
            # Process GitHub organization
            if not args.token:
                print("Error: GitHub token is required for organization access", file=sys.stderr)
                print("Please provide a token using --token or -t", file=sys.stderr)
                sys.exit(1)
            
            print(f"Analyzing GitHub organization: {args.org}")
            
            if args.complete:
                # Perform complete analysis following exact workflow
                print("Running complete analysis mode...")
                result = checker.complete_organization_analysis(args.org)
                
                if not result:
                    print("No repositories found in the organization")
                    sys.exit(0)
                
                # Exit with success (complete mode provides detailed summary)
                sys.exit(0)
            elif args.comprehensive:
                # Perform comprehensive analysis
                print("Running comprehensive analysis mode...")
                all_analyses = checker.process_github_organization_comprehensive(args.org)
                
                if not all_analyses:
                    print("No repositories found in the organization")
                    sys.exit(0)
                
                # Print comprehensive results
                checker.print_comprehensive_results(all_analyses)
                
                # Exit with success (comprehensive mode doesn't check for unclaimed deps)
                sys.exit(0)
            else:
                # Standard analysis
                all_results = checker.process_github_organization(args.org)
                
                if not all_results:
                    print("No repositories with package.json files found in the organization")
                    sys.exit(0)
                
                # Print aggregated results
                checker.print_aggregated_results(all_results)
                
                # Exit with error code if unclaimed dependencies found
                total_unclaimed = 0
                for results in all_results.values():
                    total_unclaimed += sum(1 for info in results.values() if not info['exists'])
                
                if total_unclaimed > 0:
                    sys.exit(1)
                else:
                    sys.exit(0)
        
        elif args.file:
            # Process multiple URLs from file
            urls = checker.read_urls_from_file(args.file)
            all_results = {}
            total_unclaimed = 0
            
            print(f"Processing {len(urls)} URLs from file: {args.file}")
            
            for i, url in enumerate(urls, 1):
                print(f"\n[{i}/{len(urls)}] Processing: {url}")
                
                try:
                    # Determine if source is URL or file path
                    parsed_url = urlparse(url)
                    
                    if parsed_url.scheme in ['http', 'https']:
                        # GitHub URL
                        if 'github.com' in parsed_url.netloc:
                            raw_url = checker.fetch_github_raw_url(url)
                            if args.verbose:
                                print(f"  Fetching from GitHub raw URL: {raw_url}")
                            package_data = checker.fetch_package_json_from_url(raw_url)
                        else:
                            # Direct URL
                            if args.verbose:
                                print(f"  Fetching from URL: {url}")
                            package_data = checker.fetch_package_json_from_url(url)
                    else:
                        # Local file
                        if args.verbose:
                            print(f"  Reading local file: {url}")
                        package_data = checker.fetch_package_json_from_file(url)
                    
                    if args.verbose:
                        print(f"  Package name: {package_data.get('name', 'Unknown')}")
                        print(f"  Package version: {package_data.get('version', 'Unknown')}")
                    
                    # Check dependencies
                    results = checker.check_dependencies(package_data)
                    source_name = package_data.get('name', f'Source {i}')
                    all_results[source_name] = results
                    
                    # Print individual results if verbose
                    if args.verbose:
                        checker.print_results(results, source_name)
                    
                    # Count unclaimed dependencies
                    unclaimed_count = sum(1 for info in results.values() if not info['exists'])
                    total_unclaimed += unclaimed_count
                    
                except Exception as e:
                    print(f"  Error processing {url}: {e}")
                    continue
            
            # Print aggregated results
            checker.print_aggregated_results(all_results)
            
            # Exit with error code if unclaimed dependencies found
            if total_unclaimed > 0:
                sys.exit(1)
            else:
                sys.exit(0)
        
        else:
            # Process single source (original behavior)
            parsed_url = urlparse(args.source)
            
            if parsed_url.scheme in ['http', 'https']:
                # GitHub URL
                if 'github.com' in parsed_url.netloc:
                    raw_url = checker.fetch_github_raw_url(args.source)
                    if args.verbose:
                        print(f"Fetching from GitHub raw URL: {raw_url}")
                    package_data = checker.fetch_package_json_from_url(raw_url)
                else:
                    # Direct URL
                    if args.verbose:
                        print(f"Fetching from URL: {args.source}")
                    package_data = checker.fetch_package_json_from_url(args.source)
            else:
                # Local file
                if args.verbose:
                    print(f"Reading local file: {args.source}")
                package_data = checker.fetch_package_json_from_file(args.source)
            
            if args.verbose:
                print(f"Package name: {package_data.get('name', 'Unknown')}")
                print(f"Package version: {package_data.get('version', 'Unknown')}")
            
            # Check dependencies
            results = checker.check_dependencies(package_data)
            
            # Print results
            checker.print_results(results)
            
            # Exit with error code if unclaimed dependencies found
            unclaimed_count = sum(1 for info in results.values() if not info['exists'])
            if unclaimed_count > 0:
                sys.exit(1)
            else:
                sys.exit(0)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
