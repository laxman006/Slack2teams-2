#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Monitor rebuild and track errors
"""

import subprocess
import sys
import re
from datetime import datetime
from collections import defaultdict

print("=" * 80)
print("  MONITORING VECTORSTORE REBUILD - ERROR TRACKING")
print("=" * 80)
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Error tracking
errors = defaultdict(list)
warnings = defaultdict(list)
processed_files = {'blogs': 0, 'sharepoint': 0, 'emails': 0}
failed_files = []
current_phase = "Starting"

# Start server process
process = subprocess.Popen(
    [sys.executable, "server.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True,
    bufsize=1
)

print("\n[*] Server started, monitoring output...\n")

try:
    for line in iter(process.stdout.readline, ''):
        if not line:
            break
        
        line = line.strip()
        if not line:
            continue
        
        # Print the line
        print(line)
        
        # Track phases
        if "PROCESSING BLOG POSTS" in line or "Fetching blog posts" in line:
            current_phase = "Blogs"
            print("\n" + "=" * 80)
            print("  PHASE: PROCESSING BLOGS")
            print("=" * 80)
        elif "SHAREPOINT" in line and "EXTRACTION" in line:
            current_phase = "SharePoint"
            print("\n" + "=" * 80)
            print("  PHASE: PROCESSING SHAREPOINT")
            print("=" * 80)
        elif "OUTLOOK" in line and ("PROCESSING" in line or "EMAIL" in line):
            current_phase = "Outlook"
            print("\n" + "=" * 80)
            print("  PHASE: PROCESSING OUTLOOK EMAILS")
            print("=" * 80)
        
        # Track successful file processing
        if "[OK] Extracted file:" in line:
            filename = line.split("[OK] Extracted file:")[-1].strip()
            processed_files['sharepoint'] += 1
            
        if "Page" in line and "fetched" in line and "blog" in line.lower():
            processed_files['blogs'] += 1
            
        if "[OK] Fetched" in line and "emails" in line:
            match = re.search(r'Fetched (\d+) emails', line)
            if match:
                processed_files['emails'] = int(match.group(1))
        
        # Track errors
        if "[ERROR]" in line:
            error_msg = line
            errors[current_phase].append(error_msg)
            print(f"\n⚠️  ERROR DETECTED in {current_phase}: {error_msg}\n")
            
            # Try to extract filename if present
            if "file:" in line.lower() or "File" in line:
                failed_files.append((current_phase, error_msg))
        
        # Track warnings
        if "[WARNING]" in line or "[WARN]" in line:
            warnings[current_phase].append(line)
        
        # Track failures
        if "Failed" in line or "failed" in line:
            if "[OK]" not in line:  # Don't count success messages
                errors[current_phase].append(line)
        
        # Track skipped files
        if "[SKIP]" in line or "Skipping" in line:
            warnings[current_phase].append(line)
        
        # Detect completion
        if "Uvicorn running on" in line or "Application startup complete" in line:
            print("\n" + "=" * 80)
            print("  ✅ SERVER STARTUP COMPLETE")
            print("=" * 80)
            break

except KeyboardInterrupt:
    print("\n\n[!] Monitoring stopped by user")
    process.terminate()

# Print summary
print("\n" + "=" * 80)
print("  REBUILD SUMMARY")
print("=" * 80)

print(f"\n📊 Files Processed:")
print(f"  - Blog posts: {processed_files['blogs']}")
print(f"  - SharePoint files: {processed_files['sharepoint']}")
print(f"  - Emails: {processed_files['emails']}")

if errors:
    print(f"\n❌ Errors Found: {sum(len(v) for v in errors.values())}")
    for phase, error_list in errors.items():
        if error_list:
            print(f"\n  {phase} Errors ({len(error_list)}):")
            for i, err in enumerate(error_list[:5], 1):  # Show first 5
                print(f"    {i}. {err[:100]}...")
            if len(error_list) > 5:
                print(f"    ... and {len(error_list) - 5} more")
else:
    print("\n✅ No errors detected!")

if warnings:
    print(f"\n⚠️  Warnings Found: {sum(len(v) for v in warnings.values())}")
    for phase, warn_list in warnings.items():
        if warn_list:
            print(f"\n  {phase} Warnings ({len(warn_list)}):")
            for i, warn in enumerate(warn_list[:3], 1):  # Show first 3
                print(f"    {i}. {warn[:100]}...")
            if len(warn_list) > 3:
                print(f"    ... and {len(warn_list) - 3} more")
else:
    print("\n✅ No warnings!")

if failed_files:
    print(f"\n🚫 Failed Files: {len(failed_files)}")
    for phase, error in failed_files[:10]:
        print(f"  - {phase}: {error[:80]}...")

print("\n" + "=" * 80)
print(f"Monitoring ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Write detailed error report
if errors or warnings or failed_files:
    with open("rebuild_errors.log", "w", encoding="utf-8") as f:
        f.write("REBUILD ERROR REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("ERRORS:\n")
        f.write("-" * 80 + "\n")
        for phase, error_list in errors.items():
            f.write(f"\n{phase} ({len(error_list)} errors):\n")
            for err in error_list:
                f.write(f"  - {err}\n")
        
        f.write("\n\nWARNINGS:\n")
        f.write("-" * 80 + "\n")
        for phase, warn_list in warnings.items():
            f.write(f"\n{phase} ({len(warn_list)} warnings):\n")
            for warn in warn_list:
                f.write(f"  - {warn}\n")
        
        f.write("\n\nFAILED FILES:\n")
        f.write("-" * 80 + "\n")
        for phase, error in failed_files:
            f.write(f"{phase}: {error}\n")
    
    print("\n📝 Detailed error log saved to: rebuild_errors.log")

