#!/usr/bin/env python3
"""
Helper script to find the current Gentoo Linux cloud-init image URL.

Gentoo cloud images use timestamped URLs that change frequently. This script
helps locate the most recent working URL by testing common patterns and recent dates.

Usage:
    python3 find_gentoo_url.py

The script will output the working URL if found, which can then be manually
added to images.json.
"""
import urllib.request
import urllib.error
import sys
from datetime import datetime, timedelta


def test_url(url, timeout=10):
    """Test if a URL is accessible."""
    try:
        request = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
        )
        response = urllib.request.urlopen(request, timeout=timeout)
        return response.status == 200
    except Exception:
        return False


def find_latest_gentoo_url():
    """Try to find the latest Gentoo cloud-init image URL."""
    base_url = 'https://distfiles.gentoo.org/releases/amd64/autobuilds/current-di-amd64-cloudinit/'
    
    # Try common symlink patterns first
    patterns_to_try = [
        'latest.qcow2',
        'di-amd64-cloudinit-latest.qcow2',
        'di-amd64-cloudinit.qcow2',
    ]
    
    print("Checking for latest/symlink patterns...")
    for pattern in patterns_to_try:
        url = base_url + pattern
        print(f"  Trying: {pattern}")
        if test_url(url):
            print(f"  ✓ Found: {url}")
            return url
    
    # Try recent dates (last 14 days)
    print("\nChecking recent dated builds...")
    today = datetime.now()
    for days_ago in range(0, 15):
        date = today - timedelta(days=days_ago)
        date_str = date.strftime('%Y%m%d')
        
        print(f"  Trying: {date_str} ({date.strftime('%Y-%m-%d')})")
        # Try common build times (many projects build at specific times)
        for time_str in ['140056Z', '140000Z', '120000Z', '080000Z', '000000Z']:
            filename = f'di-amd64-cloudinit-{date_str}T{time_str}.qcow2'
            url = base_url + filename
            if test_url(url):
                print(f"  ✓ Found: {url}")
                return url
    
    return None


def main():
    print("="*80)
    print("Gentoo Linux Cloud-Init Image URL Finder")
    print("="*80)
    print("\nSearching for working Gentoo cloud-init image URL...\n")
    
    url = find_latest_gentoo_url()
    
    if url:
        print(f"\n{'='*80}")
        print("✓ Success! Working URL found:")
        print(f"{'='*80}")
        print(url)
        print("\nTo add this to images.json, use:")
        
        # Extract date from URL if it matches the expected pattern
        if 'di-amd64-cloudinit-' in url and '.qcow2' in url:
            try:
                timestamp = url.split('di-amd64-cloudinit-')[1].split('.qcow2')[0]
                # Validate timestamp has at least 8 characters (YYYYMMDD)
                if len(timestamp) >= 8 and timestamp[:8].isdigit():
                    date_str = timestamp[:8]  # YYYYMMDD
                    year, month, day = int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8])
                    
                    # Validate date components are in reasonable ranges
                    if not (1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31):
                        raise ValueError(f"Invalid date components: {year}-{month:02d}-{day:02d}")
                    
                    formatted_date = f"{year}-{month:02d}-{day:02d}"
                    
                    print(f"""
{{
    "Gentoo Linux": {{
        "tag": "gentoo",
        "versions": [
            {{
                "name": "{formatted_date}",
                "url": "{url}"
            }}
        ]
    }}
}}
""")
                else:
                    print(f"\nWarning: Could not extract date from URL format.")
                    print(f"Please manually format the entry for images.json.")
            except (IndexError, ValueError) as e:
                print(f"\nWarning: Could not parse URL format: {e}")
                print(f"Please manually format the entry for images.json.")
        else:
            print(f"\nNote: URL uses a symlink or non-standard format.")
            print(f"You can add it to images.json with an appropriate version name.")
        return 0
    else:
        print(f"\n{'='*80}")
        print("✗ No working URL found")
        print(f"{'='*80}")
        print("\nManual investigation required at:")
        print("https://distfiles.gentoo.org/releases/amd64/autobuilds/current-di-amd64-cloudinit/")
        print("\nLook for the latest file matching pattern:")
        print("  di-amd64-cloudinit-YYYYMMDDTHHMMSSZ.qcow2")
        return 1


if __name__ == '__main__':
    sys.exit(main())
