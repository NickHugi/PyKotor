#!/usr/bin/env python3
"""Comprehensive profile analysis with detailed breakdowns."""
import pstats
import sys
from pathlib import Path

prof_file = Path("../../tslpatchdata/test_kotordiff_profile.prof").resolve()
if not prof_file.exists():
    print(f"Profile file not found: {prof_file}")
    sys.exit(1)

stats = pstats.Stats(str(prof_file))
stats.strip_dirs()

# Output file
output_file = Path("../../tslpatchdata/profile_analysis_detailed.txt")
output_file.parent.mkdir(parents=True, exist_ok=True)

with output_file.open("w", encoding="utf-8") as f:
    # Redirect stdout to file
    import sys
    original_stdout = sys.stdout
    sys.stdout = f
    
    print("=" * 100)
    print("COMPREHENSIVE PROFILE ANALYSIS")
    print("=" * 100)
    print(f"\nProfile file: {prof_file}")
    print(f"Analysis time: {Path(__file__).stat().st_mtime}")
    print()
    
    # Get total stats
    total_calls = stats.total_calls
    total_time = stats.total_tt
    print(f"Total function calls: {total_calls:,}")
    print(f"Total execution time: {total_time:.2f} seconds")
    print(f"Total cumulative time: {stats.total_tt:.2f} seconds")
    print()
    
    print("=" * 100)
    print("TOP 100 FUNCTIONS BY CUMULATIVE TIME")
    print("=" * 100)
    print("(Includes time spent in called functions)")
    stats.sort_stats("cumulative")
    stats.print_stats(100)
    
    print("\n" + "=" * 100)
    print("TOP 100 FUNCTIONS BY TOTAL TIME (Self Time)")
    print("=" * 100)
    print("(Time spent in the function itself, excluding called functions)")
    stats.sort_stats("tottime")
    stats.print_stats(100)
    
    print("\n" + "=" * 100)
    print("TOP 50 FUNCTIONS BY CALL COUNT")
    print("=" * 100)
    stats.sort_stats("ncalls")
    stats.print_stats(50)
    
    print("\n" + "=" * 100)
    print("CALLERS ANALYSIS - TOP 50 (Who calls the hot functions)")
    print("=" * 100)
    stats.sort_stats("cumulative")
    stats.print_callers(50)
    
    print("\n" + "=" * 100)
    print("CALLEES ANALYSIS - TOP 50 (What the hot functions call)")
    print("=" * 100)
    stats.sort_stats("cumulative")
    stats.print_callees(50)
    
    # Restore stdout
    sys.stdout = original_stdout

print(f"Analysis complete. Results written to: {output_file}")

