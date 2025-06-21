#!/usr/bin/env python3
"""
Log Monitor Script - Monitor all production logs in real-time
Usage: python scripts/monitor_logs.py [--filter LEVEL] [--component COMPONENT]
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

def get_log_files():
    """Get all log files in the logs directory"""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        print("❌ Logs directory not found")
        return []
    
    log_files = []
    for file_path in logs_dir.rglob("*.log"):
        if file_path.is_file():
            log_files.append(file_path)
    
    return sorted(log_files)

def monitor_logs(filter_level=None, component=None):
    """Monitor logs with optional filtering"""
    log_files = get_log_files()
    
    if not log_files:
        print("❌ No log files found in logs/ directory")
        return
    
    print("📊 PRODUCTION LOG MONITOR")
    print("=" * 50)
    print(f"📁 Found {len(log_files)} log files:")
    
    for log_file in log_files:
        size = log_file.stat().st_size / 1024  # KB
        print(f"  📄 {log_file} ({size:.1f} KB)")
    
    print("\n🔍 Monitoring logs... (Press Ctrl+C to stop)")
    print("=" * 50)
    
    # Build tail command for multiple files
    if component:
        # Filter by component
        filtered_files = [f for f in log_files if component in str(f)]
        if not filtered_files:
            print(f"❌ No log files found for component: {component}")
            return
        log_files = filtered_files
    
    # Use tail -f to follow multiple files
    try:
        cmd = ["tail", "-f"] + [str(f) for f in log_files]
        
        if filter_level:
            # If filtering by level, pipe through grep
            tail_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            for line in tail_process.stdout:
                if filter_level.upper() in line:
                    print(line.rstrip())
        else:
            # No filtering, show all
            subprocess.run(cmd)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Log monitoring stopped")
    except FileNotFoundError:
        print("❌ 'tail' command not found. Falling back to Python monitoring...")
        python_monitor_logs(log_files, filter_level)

def python_monitor_logs(log_files, filter_level=None):
    """Python-based log monitoring (fallback)"""
    # Simple implementation for systems without tail
    try:
        file_positions = {f: f.stat().st_size for f in log_files}
        
        while True:
            for log_file in log_files:
                if log_file.exists():
                    current_size = log_file.stat().st_size
                    last_position = file_positions.get(log_file, 0)
                    
                    if current_size > last_position:
                        with open(log_file, 'r') as f:
                            f.seek(last_position)
                            for line in f:
                                if not filter_level or filter_level.upper() in line:
                                    print(f"[{log_file.name}] {line.rstrip()}")
                        file_positions[log_file] = current_size
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Log monitoring stopped")

def show_log_summary():
    """Show summary of all log files"""
    log_files = get_log_files()
    
    print("📊 LOG FILES SUMMARY")
    print("=" * 60)
    
    total_size = 0
    for log_file in log_files:
        size = log_file.stat().st_size
        total_size += size
        
        # Get last modified time
        mtime = log_file.stat().st_mtime
        last_modified = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
        
        print(f"📄 {log_file}")
        print(f"   Size: {size/1024:.1f} KB")
        print(f"   Modified: {last_modified}")
        
        # Show last few lines
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    print(f"   Last entry: {lines[-1].strip()}")
                else:
                    print("   Last entry: (empty)")
        except Exception as e:
            print(f"   Last entry: (error reading: {e})")
        print()
    
    print(f"📊 Total log size: {total_size/1024:.1f} KB")

def main():
    parser = argparse.ArgumentParser(description="Monitor production logs")
    parser.add_argument("--filter", help="Filter by log level (INFO, ERROR, DEBUG)")
    parser.add_argument("--component", help="Filter by component (arbitrage, performance, etc.)")
    parser.add_argument("--summary", action="store_true", help="Show log summary instead of monitoring")
    
    args = parser.parse_args()
    
    # Change to project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    if args.summary:
        show_log_summary()
    else:
        monitor_logs(args.filter, args.component)

if __name__ == "__main__":
    main()