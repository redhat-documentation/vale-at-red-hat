#!/usr/bin/env python3
"""
Check for broken links in an external HTML page.

This script fetches an HTML page from a URL, extracts all links,
and checks if they are accessible.
"""

import argparse
import sys
import time
from urllib.parse import urljoin, urlparse
from typing import List, Tuple, Set
import requests
from bs4 import BeautifulSoup


def fetch_html(url: str, timeout: int = 30) -> str:
    """Fetch HTML content from a URL."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        sys.exit(1)


def extract_links(html: str, base_url: str) -> List[str]:
    """Extract all links from HTML content."""
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    
    # Extract links from <a> tags
    for tag in soup.find_all('a', href=True):
        href = tag['href']
        # Skip anchors and javascript links
        if href.startswith('#') or href.startswith('javascript:'):
            continue
        # Convert relative URLs to absolute
        absolute_url = urljoin(base_url, href)
        links.append(absolute_url)
    
    # Extract links from <img> tags
    for tag in soup.find_all('img', src=True):
        src = tag['src']
        absolute_url = urljoin(base_url, src)
        links.append(absolute_url)
    
    # Extract links from <link> tags (CSS, etc.)
    for tag in soup.find_all('link', href=True):
        href = tag['href']
        absolute_url = urljoin(base_url, href)
        links.append(absolute_url)
    
    # Extract links from <script> tags
    for tag in soup.find_all('script', src=True):
        src = tag['src']
        absolute_url = urljoin(base_url, src)
        links.append(absolute_url)
    
    return links


def check_link(url: str, timeout: int = 60) -> Tuple[bool, str]:
    """Check if a link is accessible."""
    try:
        # Use HEAD request first (faster)
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        
        # Some servers don't support HEAD, try GET
        if response.status_code == 405 or response.status_code == 404:
            response = requests.get(url, timeout=timeout, allow_redirects=True, stream=True)
        
        if response.status_code >= 400:
            return False, f"HTTP {response.status_code}"
        
        return True, "OK"
    
    except requests.Timeout:
        return False, "Timeout"
    except requests.ConnectionError:
        return False, "Connection Error"
    except requests.RequestException as e:
        return False, str(e)


def check_links(
    url: str,
    timeout: int = 60,
    delay: float = 0.5,
    verbose: bool = False
) -> Tuple[List[str], int]:
    """
    Check all links in a page.
    
    Returns:
        Tuple of (broken_links, total_links_checked)
    """
    print(f"Fetching page: {url}")
    html = fetch_html(url, timeout=timeout)
    
    print("Extracting links...")
    all_links = extract_links(html, url)
    
    # Deduplicate links
    unique_links = list(set(all_links))
    print(f"Found {len(all_links)} total links ({len(unique_links)} unique)")
    
    broken_links = []
    
    for i, link in enumerate(unique_links, 1):
        if verbose:
            print(f"[{i}/{len(unique_links)}] Checking {link}...", end=" ")
        
        is_ok, message = check_link(link, timeout=timeout)
        
        if verbose:
            print(message)
        
        if not is_ok:
            broken_links.append((link, message))
            if not verbose:
                print(f"✗ {link}: {message}")
        
        # Add delay to avoid overwhelming servers
        if i < len(unique_links):
            time.sleep(delay)
    
    return broken_links, len(unique_links)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Check for broken links in an external HTML page'
    )
    parser.add_argument(
        'url',
        help='URL of the HTML page to check'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        help='Timeout for each request in seconds (default: 60)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=0.5,
        help='Delay between requests in seconds (default: 0.5)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Show all link check results, not just broken ones'
    )
    
    args = parser.parse_args()
    
    print(f"Checking links in: {args.url}\n")
    
    broken_links, total_links = check_links(
        args.url,
        timeout=args.timeout,
        delay=args.delay,
        verbose=args.verbose
    )
    
    print("\n" + "=" * 80)
    print(f"Summary: Found {len(broken_links)} broken link(s) out of {total_links} checked")
    print("=" * 80)
    
    if broken_links:
        print("\nBroken links:")
        for link, reason in broken_links:
            print(f"  ✗ {link}")
            print(f"    Reason: {reason}")
        sys.exit(1)
    else:
        print("\n✓ All links are working!")
        sys.exit(0)


if __name__ == '__main__':
    main()
