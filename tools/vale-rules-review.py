#!/usr/bin/env python3

"""
Vale Rules Review - Automated false positive detection and rule improvement

Created with Claude Code v2.0.46.

This script clones a repository, runs Vale with RedHat rules, identifies
duplicate errors, and uses Claude CLI to review and improve Vale rules by
filtering out false positives.

Example run:
python tools/vale-rules-review.py https://github.com/openshift/openshift-docs

Copyright (c) 2025 Red Hat, Inc.
This program and the accompanying materials are made
available under the terms of the Eclipse Public License 2.0
which is available at https://www.eclipse.org/legal/epl-2.0/

SPDX-License-Identifier: EPL-2.0
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set
import tempfile
from multiprocessing import Pool, cpu_count, Manager
from functools import partial


class ValeRuleImprover:
    """Main class for Vale rule improvement workflow"""

    def __init__(self, repo_url: str, verbose: bool = True, num_workers: int = None,
                 file_types: List[str] = None, force_vale: bool = False):
        self.repo_url = repo_url
        self.verbose = verbose
        self.num_workers = num_workers or min(16, cpu_count())
        self.file_types = file_types or ["adoc"]
        self.force_vale = force_vale
        self.repo_name = self._extract_repo_name(repo_url)
        self.tmp_dir = Path("./tmp")
        self.clone_dir = self.tmp_dir / self.repo_name
        self.vale_dir = Path(".vale")
        self.redhat_styles_dir = self.vale_dir / "styles" / "RedHat"
        self.fixtures_dir = self.vale_dir / "fixtures" / "RedHat"
        self.errors_json = {}
        self.unique_errors = defaultdict(list)

    def _extract_repo_name(self, url: str) -> str:
        """Extract repository name from URL"""
        name = url.rstrip('/').split('/')[-1]
        if name.endswith('.git'):
            name = name[:-4]
        return name

    def _log(self, message: str, level: str = "INFO"):
        """Log message if verbose mode is enabled"""
        if self.verbose or level == "ERROR":
            print(f"[{level}] {message}")

    def setup_tmp_directory(self):
        """Create tmp directory if it doesn't exist"""
        self.tmp_dir.mkdir(exist_ok=True)
        self._log(f"Ensured tmp directory exists: {self.tmp_dir}")

    def clone_repository(self, skip_if_exists: bool = True):
        """Clone the repository to tmp directory"""
        # Check if already exists
        if self.clone_dir.exists() and skip_if_exists:
            self._log(f"Repository already cloned at: {self.clone_dir}")
            self._log("Skipping clone. Use --force-clone to re-clone.")
            return

        # Remove existing clone if present
        if self.clone_dir.exists():
            self._log(f"Removing existing clone: {self.clone_dir}")
            shutil.rmtree(self.clone_dir)

        self._log(f"Cloning repository: {self.repo_url}")
        try:
            subprocess.run(
                ["git", "clone", self.repo_url, str(self.clone_dir)],
                check=True,
                capture_output=True,
                text=True
            )
            self._log(f"Successfully cloned to: {self.clone_dir}")
        except subprocess.CalledProcessError as e:
            self._log(f"Failed to clone repository: {e.stderr}", "ERROR")
            raise

    def _find_documentation_files(self) -> List[Path]:
        """Find all documentation files in the cloned repository"""
        patterns = [f"**/*.{ext}" for ext in self.file_types]
        files = []
        for pattern in patterns:
            files.extend(self.clone_dir.glob(pattern))
        return sorted(files)

    def _get_repo_size(self) -> str:
        """Get human-readable repository size"""
        try:
            result = subprocess.run(
                ["du", "-sh", str(self.clone_dir)],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.split()[0]
        except Exception:
            return "unknown"

    def _hide_existing_vale_configs(self) -> List[tuple]:
        """Temporarily hide existing Vale config files in the cloned repo"""
        config_names = [".vale.ini", "vale.ini", ".vale"]
        hidden_configs = []

        for config_name in config_names:
            config_path = self.clone_dir / config_name
            if config_path.exists():
                # Rename to temporary name
                hidden_path = config_path.parent / f".{config_name}.tmp-hidden"
                self._log(f"Temporarily hiding {config_path}")
                config_path.rename(hidden_path)
                hidden_configs.append((hidden_path, config_path))

        return hidden_configs

    def _restore_vale_configs(self, hidden_configs: List[tuple]):
        """Restore hidden Vale config files"""
        for hidden_path, original_path in hidden_configs:
            if hidden_path.exists():
                self._log(f"Restoring {original_path}")
                hidden_path.rename(original_path)

    def _run_vale_on_batch(self, file_batch: List[Path], batch_id: int, vale_config: Path,
                           progress_dict: Dict = None) -> Dict:
        """Run Vale on a batch of files and return JSON results"""
        start_time = time.time()

        # Create a temporary file list
        file_list = self.tmp_dir / f"vale-files-batch-{batch_id}.txt"
        with open(file_list, 'w') as f:
            for file_path in file_batch:
                f.write(f"{file_path}\n")

        self._log(f"Processing batch {batch_id} ({len(file_batch)} files)...")

        try:
            # Run vale on the batch
            result = subprocess.run(
                [
                    "vale",
                    "--config", str(vale_config),
                    "--output", "JSON",
                    "--no-exit",
                ] + [str(f) for f in file_batch],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout per batch
            )

            # Update progress
            if progress_dict is not None:
                progress_dict['completed'] += 1
                elapsed = time.time() - start_time
                progress_dict['total_time'] += elapsed

            # Parse JSON output
            if result.stdout.strip():
                try:
                    batch_result = json.loads(result.stdout)
                    self._log(f"Batch {batch_id}: Completed in {elapsed:.1f}s, found {len(batch_result)} files with errors")
                    return batch_result
                except json.JSONDecodeError:
                    self._log(f"Batch {batch_id}: Invalid JSON output", "ERROR")
                    return {}
            return {}

        except subprocess.TimeoutExpired:
            self._log(f"Batch {batch_id}: Timeout after 10 minutes", "ERROR")
            if progress_dict is not None:
                progress_dict['completed'] += 1
            return {}
        except Exception as e:
            self._log(f"Batch {batch_id}: Error - {str(e)}", "ERROR")
            if progress_dict is not None:
                progress_dict['completed'] += 1
            return {}
        finally:
            # Cleanup temp file
            if file_list.exists():
                file_list.unlink()

    def run_vale(self) -> Path:
        """Run Vale on the cloned repository with RedHat rules only (parallel)"""
        self._log("Running Vale on cloned repository with parallel processing...")

        # Hide any existing Vale configs in the cloned repository
        hidden_configs = self._hide_existing_vale_configs()

        try:
            # Create a temporary vale config that only uses RedHat rules
            vale_config = self._create_redhat_only_config()

            # Get repo size
            repo_size = self._get_repo_size()
            self._log(f"Repository size: {repo_size}")

            # Find all documentation files
            all_files = self._find_documentation_files()
            file_types_str = ", ".join(self.file_types)
            self._log(f"Found {len(all_files)} documentation files ({file_types_str})")

            if not all_files:
                self._log("No documentation files found", "ERROR")
                output_file = self.tmp_dir / f"vale-{self.repo_name}.json"
                with open(output_file, 'w') as f:
                    f.write("{}")
                return output_file

            # Split files into batches for parallel processing
            batch_size = max(1, len(all_files) // self.num_workers)
            batches = [all_files[i:i + batch_size] for i in range(0, len(all_files), batch_size)]

            self._log(f"Processing {len(all_files)} files in parallel...")

            # Process batches in parallel with progress tracking
            merged_results = {}
            start_time = time.time()

            with Manager() as manager:
                # Shared progress dictionary
                progress = manager.dict()
                progress['completed'] = 0
                progress['total_time'] = 0.0

                with Pool(processes=self.num_workers) as pool:
                    # Create partial function with vale_config and progress
                    worker_func = partial(self._run_vale_on_batch_wrapper,
                                        vale_config=vale_config, progress_dict=progress)

                    # Start processing batches asynchronously
                    async_results = [pool.apply_async(worker_func, (batch, i))
                                   for i, batch in enumerate(batches)]

                    # Monitor progress
                    last_completed = 0
                    while any(not r.ready() for r in async_results):
                        time.sleep(2)
                        completed = progress['completed']
                        if completed > last_completed:
                            # Calculate progress and ETA
                            percent = (completed / len(batches)) * 100
                            avg_time_per_batch = progress['total_time'] / completed if completed > 0 else 0
                            remaining = len(batches) - completed
                            eta_seconds = avg_time_per_batch * remaining

                            eta_str = f"{int(eta_seconds // 60)}m {int(eta_seconds % 60)}s" if eta_seconds > 0 else "calculating..."

                            self._log(f"Progress: {completed}/{len(batches)} batches ({percent:.1f}%) | "
                                    f"Avg: {avg_time_per_batch:.1f}s/batch | ETA: {eta_str}")
                            last_completed = completed

                    # Collect results
                    results = [r.get() for r in async_results]

                    # Merge results
                    for batch_result in results:
                        if batch_result:
                            merged_results.update(batch_result)

            total_time = time.time() - start_time

            # Save merged JSON output
            output_file = self.tmp_dir / f"vale-{self.repo_name}.json"
            with open(output_file, 'w') as f:
                json.dump(merged_results, f, indent=2)

            self._log(f"Vale results saved to: {output_file}")
            self._log(f"Total files with errors: {len(merged_results)}")
            self._log(f"Total processing time: {int(total_time // 60)}m {int(total_time % 60)}s")

            return output_file

        finally:
            # Restore hidden Vale configs
            self._restore_vale_configs(hidden_configs)

    def _run_vale_on_batch_wrapper(self, batch: List[Path], batch_id: int, vale_config: Path,
                                   progress_dict: Dict = None) -> Dict:
        """Wrapper for multiprocessing compatibility"""
        return self._run_vale_on_batch(batch, batch_id, vale_config, progress_dict)

    def _create_redhat_only_config(self) -> Path:
        """Create a temporary Vale config that only uses RedHat rules"""
        # Use absolute path to styles directory
        styles_path = self.vale_dir.absolute() / "styles"

        config_content = f"""StylesPath = {styles_path}

MinAlertLevel = suggestion

IgnoredScopes = code, tt, img, url, a, body.id

SkippedScopes = script, style, pre, figure, code, tt, blockquote, listingblock, literalblock

Packages = RedHat

[*.adoc]
BasedOnStyles = RedHat

[*.md]
BasedOnStyles = RedHat
TokenIgnores = (\\x60[^\\n\\x60]+\\x60), ([^\\n]+=[^\\n]*), (\\+[^\\n]+\\+), (http[^\\n]+\\[)

[*.ini]
BasedOnStyles = RedHat
TokenIgnores = (\\x60[^\\n\\x60]+\\x60), ([^\\n]+=[^\\n]*), (\\+[^\\n]+\\+), (http[^\\n]+\\[)
"""
        config_file = self.tmp_dir / "vale-redhat-only.ini"
        with open(config_file, 'w') as f:
            f.write(config_content)

        self._log(f"Created temporary Vale config: {config_file}")
        return config_file

    def parse_and_deduplicate_errors(self, json_file: Path):
        """Parse Vale JSON output and deduplicate errors"""
        self._log("Parsing and deduplicating errors...")

        with open(json_file, 'r') as f:
            content = f.read().strip()

        # Handle empty or invalid JSON
        if not content:
            self._log("Vale output is empty. No errors to process.", "ERROR")
            return

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            self._log(f"Failed to parse Vale JSON output: {e}", "ERROR")
            self._log(f"Content preview: {content[:500]}", "ERROR")
            raise

        # Check if this is an error response from Vale
        if isinstance(data, dict) and "Code" in data and data.get("Code") == "E100":
            self._log(f"Vale runtime error: {data.get('Text', 'Unknown error')}", "ERROR")
            raise RuntimeError(f"Vale error: {data.get('Text', 'Unknown error')}")

        self.errors_json = data

        # Deduplicate by creating a unique key from the error details
        # (excluding file path and line number)
        seen_errors = set()

        for file_path, errors in self.errors_json.items():
            for error in errors:
                # Create unique identifier based on Check, Message, and Match
                error_key = (
                    error.get('Check', ''),
                    error.get('Message', ''),
                    error.get('Match', ''),
                    error.get('Severity', '')
                )

                if error_key not in seen_errors:
                    seen_errors.add(error_key)
                    rule_name = error.get('Check', 'Unknown')
                    self.unique_errors[rule_name].append({
                        'message': error.get('Message', ''),
                        'match': error.get('Match', ''),
                        'severity': error.get('Severity', ''),
                        'link': error.get('Link', ''),
                        'example_file': file_path,
                        'line': error.get('Line', 0)
                    })

        total_errors = sum(len(errors) for errors in self.errors_json.values())
        unique_count = sum(len(errors) for errors in self.unique_errors.values())

        self._log(f"Total errors: {total_errors}")
        self._log(f"Unique errors: {unique_count}")
        self._log(f"Rules with errors: {len(self.unique_errors)}")

        # Save deduplicated errors for inspection
        dedup_file = self.tmp_dir / f"vale-{self.repo_name}-deduplicated.json"
        with open(dedup_file, 'w') as f:
            json.dump(dict(self.unique_errors), f, indent=2)
        self._log(f"Deduplicated errors saved to: {dedup_file}")

    def review_with_claude(self):
        """Use Claude CLI to review errors and suggest rule improvements"""
        self._log("Starting Claude CLI review of errors...")

        total_rules = len(self.unique_errors)
        rules_processed = 0
        rules_modified = 0

        for rule_name, errors in self.unique_errors.items():
            if not errors:
                continue

            rules_processed += 1
            self._log(f"Reviewing rule {rules_processed}/{total_rules}: {rule_name} ({len(errors)} unique errors)")

            # Get the rule file path
            rule_file = self._get_rule_file(rule_name)
            if not rule_file or not rule_file.exists():
                self._log(f"Rule file not found for: {rule_name}", "ERROR")
                continue

            # Prepare the prompt for Claude
            was_modified = self._ask_claude_to_review(rule_name, rule_file, errors)

            if was_modified:
                rules_modified += 1
                self._log(f"✓ Claude modified {rule_name} (file changed)", "INFO")
            else:
                self._log(f"✗ No changes made to {rule_name}", "INFO")

        self._log(f"Review complete: {rules_modified}/{total_rules} rules modified")

    def _get_rule_file(self, rule_name: str) -> Path:
        """Get the path to a rule file from its name"""
        # Rule names are like "RedHat.TermsErrors"
        if not rule_name.startswith("RedHat."):
            return None

        rule_basename = rule_name.replace("RedHat.", "")
        rule_file = self.redhat_styles_dir / f"{rule_basename}.yml"
        return rule_file

    def _get_fixture_dir(self, rule_name: str) -> Path:
        """Get the path to the fixture directory for a rule"""
        if not rule_name.startswith("RedHat."):
            return None

        rule_basename = rule_name.replace("RedHat.", "")
        fixture_dir = self.fixtures_dir / rule_basename
        return fixture_dir

    def _ask_claude_to_review(self, rule_name: str, rule_file: Path, errors: List[Dict]) -> bool:
        """Use Claude CLI to review if errors are false positives and update the rule"""

        # Read the current rule content
        with open(rule_file, 'r') as f:
            rule_content = f.read()

        # Get fixture directory and files
        fixture_dir = self._get_fixture_dir(rule_name)
        testinvalid_file = fixture_dir / "testinvalid.adoc" if fixture_dir else None
        testvalid_file = fixture_dir / "testvalid.adoc" if fixture_dir else None

        # Check if fixture files exist
        fixtures_info = ""
        if fixture_dir and fixture_dir.exists():
            fixtures_info = f"\n\nTest Fixtures Directory: {fixture_dir}"
            if testinvalid_file and testinvalid_file.exists():
                fixtures_info += f"\n- Invalid examples file (should trigger rule): {testinvalid_file}"
            if testvalid_file and testvalid_file.exists():
                fixtures_info += f"\n- Valid examples file (should NOT trigger rule): {testvalid_file}"

        # Format errors for the prompt
        errors_summary = "\n".join([
            f"- Match: '{e['match']}' | Message: {e['message']} | Example: {e['example_file']}:{e['line']}"
            for e in errors[:20]  # Limit to first 20 errors to avoid token limits
        ])

        if len(errors) > 20:
            errors_summary += f"\n... and {len(errors) - 20} more similar errors"

        # Create the prompt for Claude
        prompt = f"""Review the following Vale rule and its errors to identify false positives.

Rule: {rule_name}
Rule file: {rule_file}{fixtures_info}

Current rule content:
```yaml
{rule_content}
```

Errors detected (unique, deduplicated):
{errors_summary}

Task:
1. Review each unique error and determine if it's a false positive
2. If you find false positives, update the rule to exclude them
3. You can:
   - Add exceptions to existing patterns
   - Modify swap mappings
   - Add negative lookaheads/lookbehinds
   - Update the rule's pattern to be more specific

4. IMPORTANT - Regex Simplicity Guidelines:
   - Keep regex patterns SIMPLE and READABLE
   - If a regex pattern becomes overly complex, labyrinthine, or verbose, it is likely "slop" and should NOT be added
   - Prefer simple, straightforward patterns over complex ones
   - If you cannot express the fix with a simple regex, consider if the rule should be modified differently
   - Complex nested lookaheads/lookbehinds are a red flag - keep patterns minimal
   - Example of GOOD (simple): '(?i)\\bfoo\\b'
   - Example of BAD (overly complex): '(?i)(?<!\\w)(?:foo|bar)(?!\\w)(?:(?<=\\s)|(?=\\s))(?!.*(?:baz|qux))'

5. IMPORTANT - Update test fixtures when removing false positives:
   - When you remove a term/pattern as a false positive from the rule, you should also update the test fixtures:
     a. Remove the false positive examples from {testinvalid_file} (if they exist there)
     b. Add the false positive examples to {testvalid_file} to ensure they won't be flagged
   - Each fixture file contains plain text terms/examples to test the rule
   - The testinvalid.adoc file should contain examples that SHOULD trigger the rule
   - The testvalid.adoc file should contain examples that should NOT trigger the rule

If you identify false positives and make changes:
- Edit the rule file {rule_file}
- Update fixture files if they exist: {testinvalid_file} and/or {testvalid_file}

IMPORTANT: Only modify the rule if you're confident that the errors are false positives. Be conservative.
IMPORTANT: Any regex you create must be simple and not overly verbose. Complex regex is a sign of poor quality.

After your analysis, provide a summary of:
- How many errors are false positives
- What changes you made to the rule (if any)
- What changes you made to test fixtures (if any)
- Reasoning for the changes
- Confirmation that any regex added is simple and readable
"""

        self._log(f"Asking Claude to review {rule_name}...")

        try:
            # Use Claude CLI in print mode with the prompt via stdin
            # Use --dangerously-skip-permissions to avoid interactive prompts
            # Specify tools to allow Edit, Write, Read, and Grep
            result = subprocess.run(
                [
                    "claude",
                    "--print",
                    "--dangerously-skip-permissions",
                    "--tools", "Edit,Write,Read,Grep,Glob"
                ],
                input=prompt,  # Pass prompt via stdin
                capture_output=True,
                text=True,
                cwd=str(Path.cwd())  # Run from repo root
            )

            # Check for errors
            if result.returncode != 0:
                self._log(f"Claude CLI returned non-zero exit code: {result.returncode}", "ERROR")
                if result.stderr:
                    self._log(f"Error output: {result.stderr}", "ERROR")
                if result.stdout:
                    self._log(f"Standard output: {result.stdout}")
                return False

            if result.stdout:
                # Print the full output
                print("=" * 80)
                print(f"Claude review for {rule_name}:")
                print("=" * 80)
                print(result.stdout)
                print("=" * 80)
            else:
                self._log("No output from Claude CLI", "ERROR")
                if result.stderr:
                    self._log(f"Stderr: {result.stderr}", "ERROR")

            # Check if the rule file or fixture files were modified
            # We'll use git to check if any files changed
            files_to_check = [str(rule_file)]
            if testinvalid_file and testinvalid_file.exists():
                files_to_check.append(str(testinvalid_file))
            if testvalid_file and testvalid_file.exists():
                files_to_check.append(str(testvalid_file))

            git_status = subprocess.run(
                ["git", "status", "--porcelain"] + files_to_check,
                capture_output=True,
                text=True
            )

            return bool(git_status.stdout.strip())

        except FileNotFoundError:
            self._log("Claude CLI not found. Is 'claude' in your PATH?", "ERROR")
            return False
        except Exception as e:
            self._log(f"Claude CLI execution failed: {str(e)}", "ERROR")
            return False

    def _generate_change_justifications(self) -> str:
        """Generate line-by-line justifications for changes using git diff"""
        self._log("Generating change justifications...")

        try:
            # Get the diff for staged changes
            diff_result = subprocess.run(
                ["git", "diff", "--cached", "--unified=0",
                 str(self.redhat_styles_dir), str(self.fixtures_dir)],
                capture_output=True,
                text=True,
                check=True
            )

            if not diff_result.stdout.strip():
                return "No changes to document."

            justifications = []
            current_file = None

            for line in diff_result.stdout.split('\n'):
                # Track which file we're in
                if line.startswith('+++'):
                    # Extract file path from +++ b/path/to/file
                    current_file = line[6:].strip() if len(line) > 6 else "unknown"
                    file_name = Path(current_file).name
                    continue

                # Process added lines
                if line.startswith('+') and not line.startswith('+++'):
                    content = line[1:].strip()
                    if content:  # Skip empty lines
                        # Generate justification based on content
                        justification = self._generate_line_justification(content, file_name, "added")
                        if justification:
                            justifications.append(f"- {file_name}: {justification}")

                # Process removed lines
                elif line.startswith('-') and not line.startswith('---'):
                    content = line[1:].strip()
                    if content:  # Skip empty lines
                        justification = self._generate_line_justification(content, file_name, "removed")
                        if justification:
                            justifications.append(f"- {file_name}: {justification}")

            if not justifications:
                return "Changes made to improve rule accuracy and reduce false positives."

            # Remove duplicates while preserving order
            seen = set()
            unique_justifications = []
            for j in justifications:
                if j not in seen:
                    seen.add(j)
                    unique_justifications.append(j)

            return '\n'.join(unique_justifications)

        except subprocess.CalledProcessError as e:
            self._log(f"Failed to generate change justifications: {e}", "ERROR")
            return "Changes made to improve rule accuracy and reduce false positives."

    def _generate_line_justification(self, content: str, file_name: str, change_type: str) -> str:
        """Generate a justification for a single line change"""
        # Rule files (.yml)
        if file_name.endswith('.yml'):
            if change_type == "removed":
                # Check if it's a term being removed
                if content.startswith('- '):
                    term = content[2:].strip('\'"')
                    return f"Removed '{term}' as false positive"
                elif ':' in content:
                    # Could be a swap mapping or other YAML key
                    key = content.split(':')[0].strip()
                    return f"Removed '{key}' pattern as false positive"
            elif change_type == "added":
                if 'exceptions:' in content.lower():
                    return "Added exceptions list to filter false positives"
                elif content.startswith('- '):
                    term = content[2:].strip('\'"')
                    return f"Added exception for '{term}'"
                elif 'negative lookahead' in content or '(?!' in content:
                    return "Added negative lookahead to exclude false positive context"
                elif 'negative lookbehind' in content or '(?<!' in content:
                    return "Added negative lookbehind to exclude false positive context"
                elif ':' in content and 'swap' not in content.lower():
                    return "Updated pattern to be more specific"

        # Fixture files (.adoc)
        elif file_name.endswith('.adoc'):
            if change_type == "removed" and 'testinvalid' in file_name:
                return f"Removed false positive example: '{content[:50]}...'"
            elif change_type == "added" and 'testvalid' in file_name:
                return f"Added valid usage example that should not trigger rule: '{content[:50]}...'"
            elif change_type == "added" and 'testinvalid' in file_name:
                return f"Added example that should trigger rule: '{content[:50]}...'"
            elif change_type == "removed" and 'testvalid' in file_name:
                return f"Removed example from valid cases: '{content[:50]}...'"

        return None

    def create_pull_request(self):
        """Create a pull request with the rule changes"""
        self._log("Checking for modified rules and fixtures...")

        # Check if there are any changes in rules or fixtures
        rules_result = subprocess.run(
            ["git", "status", "--porcelain", str(self.redhat_styles_dir)],
            capture_output=True,
            text=True
        )

        fixtures_result = subprocess.run(
            ["git", "status", "--porcelain", str(self.fixtures_dir)],
            capture_output=True,
            text=True
        )

        if not rules_result.stdout.strip() and not fixtures_result.stdout.strip():
            self._log("No rule or fixture changes detected. Skipping PR creation.")
            return

        self._log("Creating pull request with rule improvements...")

        # Create a new branch
        branch_name = f"vale-rule-improvements-{self.repo_name}"

        try:
            # Check if we're already on the target branch
            current_branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = current_branch_result.stdout.strip()

            if current_branch == branch_name:
                self._log(f"Already on branch: {branch_name}")
            else:
                # Check if branch exists
                branch_check = subprocess.run(
                    ["git", "rev-parse", "--verify", branch_name],
                    capture_output=True,
                    text=True
                )

                if branch_check.returncode == 0:
                    # Branch exists, switch to it
                    self._log(f"Switching to existing branch: {branch_name}")
                    subprocess.run(["git", "checkout", branch_name], check=True)
                else:
                    # Create new branch
                    self._log(f"Creating new branch: {branch_name}")
                    subprocess.run(["git", "checkout", "-b", branch_name], check=True)

            # Stage changes (both rules and fixtures)
            subprocess.run(
                ["git", "add", str(self.redhat_styles_dir), str(self.fixtures_dir)],
                check=True
            )

            # Generate change justifications before committing
            change_justifications = self._generate_change_justifications()

            # Commit changes
            commit_message = f"""Improve Vale rules based on {self.repo_name} analysis

Analyzed {self.repo_name} repository and identified false positives
in RedHat Vale rules. This commit updates rules and test fixtures to
reduce false positives while maintaining accuracy.

Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

            subprocess.run(
                ["git", "commit", "-m", commit_message],
                check=True
            )

            # Push branch
            subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                check=True
            )

            # Create PR using gh CLI
            pr_body = f"""## Summary
- Analyzed the {self.repo_name} repository for Vale rule false positives
- Identified and filtered duplicate errors across files
- Used automated review to improve RedHat Vale rules
- Updated both rule files and test fixtures
- Reduced false positives while maintaining rule accuracy

## Changes
This PR contains updates to:
- Vale rules in `.vale/styles/RedHat/`
- Test fixtures in `.vale/fixtures/RedHat/`

All changes are based on analysis of errors found in {self.repo_name}.

## Detailed Change Justifications
{change_justifications}

## Test Plan
- [ ] Run Vale on {self.repo_name} and verify reduced false positives
- [ ] Run Vale on test fixtures to ensure they pass/fail as expected
- [ ] Run Vale on existing test cases to ensure no regressions
- [ ] Review rule and fixture changes for correctness

Generated with [Claude Code](https://claude.com/claude-code)
"""

            result = subprocess.run(
                [
                    "gh", "pr", "create",
                    "--title", f"Improve Vale rules based on {self.repo_name} analysis",
                    "--body", pr_body
                ],
                capture_output=True,
                text=True
            )

            self._log(f"Pull request created successfully!")
            print(result.stdout)

        except subprocess.CalledProcessError as e:
            self._log(f"Failed to create PR: {e.stderr}", "ERROR")
            raise

    def cleanup(self):
        """Clean up temporary files"""
        if self.clone_dir.exists():
            self._log(f"Cleaning up: {self.clone_dir}")
            # Don't remove by default, user might want to inspect
            # shutil.rmtree(self.clone_dir)

    def run(self):
        """Execute the full workflow"""
        try:
            self.setup_tmp_directory()
            self.clone_repository()

            # Check if deduplicated results already exist (unless forced)
            dedup_file = self.tmp_dir / f"vale-{self.repo_name}-deduplicated.json"
            json_file = self.tmp_dir / f"vale-{self.repo_name}.json"

            if dedup_file.exists() and not self.force_vale:
                self._log(f"Found existing deduplicated results: {dedup_file}")
                self._log("Skipping Vale run. Use --force-vale to run Vale again.")
                # Load the existing deduplicated results
                with open(dedup_file, 'r') as f:
                    self.unique_errors = defaultdict(list, json.load(f))
            else:
                if self.force_vale and dedup_file.exists():
                    self._log("Forcing new Vale run (--force-vale specified)")
                json_file = self.run_vale()
                self.parse_and_deduplicate_errors(json_file)

            if not self.unique_errors:
                self._log("No errors found. Nothing to review.")
                return

            self.review_with_claude()
            self.create_pull_request()

        except Exception as e:
            self._log(f"Workflow failed: {str(e)}", "ERROR")
            raise
        finally:
            # Don't cleanup automatically, let user inspect
            pass


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Vale Rules Review - Automated false positive detection and rules improvement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://github.com/example/repo
  %(prog)s https://github.com/example/repo -j 8 -t adoc
  %(prog)s https://github.com/example/repo -t adoc,md
        """
    )

    parser.add_argument(
        "repo_url",
        help="URL of the repository to analyze"
    )

    parser.add_argument(
        "-j", "--jobs",
        type=int,
        default=None,
        help="Number of parallel workers (default: min(16, CPU count))"
    )

    parser.add_argument(
        "-t", "--file-types",
        type=str,
        default="adoc",
        help="Comma-separated list of file extensions to process (default: adoc)"
    )

    parser.add_argument(
        "--force-vale",
        action="store_true",
        help="Force a new Vale run even if cached results exist"
    )

    args = parser.parse_args()

    # Parse file types
    file_types = [ext.strip() for ext in args.file_types.split(',')]

    improver = ValeRuleImprover(args.repo_url,
                                num_workers=args.jobs, file_types=file_types,
                                force_vale=args.force_vale)
    improver.run()


if __name__ == "__main__":
    main()
