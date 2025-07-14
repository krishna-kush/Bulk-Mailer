#!/usr/bin/env python3
# ================================================================================
# BULK_MAILER - Professional Email Campaign Manager
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: Test script for per_run_gap_randomizer feature
#
# ================================================================================

import sys
import os
# Add the parent directory to the path to import modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from modules.rate_limiter.rate_limiter import RateLimiter
import time

def test_randomization():
    """Test the per_run_gap_randomizer feature."""
    print("Testing per_run_gap_randomizer feature...")
    print("=" * 60)
    
    # Test data with different randomization settings
    test_senders = [
        {
            'email': 'test1@example.com',
            'per_run_gap': 30,
            'per_run_gap_randomizer': 0  # No randomization
        },
        {
            'email': 'test2@example.com', 
            'per_run_gap': 30,
            'per_run_gap_randomizer': 5  # ±5 seconds randomization
        },
        {
            'email': 'test3@example.com',
            'per_run_gap': 30,
            'per_run_gap_randomizer': 10  # ±10 seconds randomization
        }
    ]
    
    # Create rate limiter
    rate_limiter = RateLimiter(test_senders, global_limit=0)
    
    # Test each sender
    for sender in test_senders:
        email = sender['email']
        base_gap = sender['per_run_gap']
        randomizer = sender['per_run_gap_randomizer']
        
        print(f"\nTesting {email}:")
        print(f"  Base gap: {base_gap}s, Randomizer: ±{randomizer}s")
        
        if randomizer == 0:
            print(f"  Expected range: {base_gap}s (no randomization)")
        else:
            min_gap = max(1.0, base_gap - randomizer)
            max_gap = base_gap + randomizer
            print(f"  Expected range: {min_gap:.1f}s - {max_gap:.1f}s")
        
        # Generate 10 randomized gap times
        gaps = []
        for _ in range(10):
            gap = rate_limiter.get_randomized_gap_time(email)
            gaps.append(gap)
        
        print(f"  Generated gaps: {[f'{g:.1f}' for g in gaps]}")
        print(f"  Min: {min(gaps):.1f}s, Max: {max(gaps):.1f}s, Avg: {sum(gaps)/len(gaps):.1f}s")
        
        # Test average gap time (for queue calculations)
        avg_gap = rate_limiter.get_average_gap_time(email)
        print(f"  Average gap time (for queues): {avg_gap:.1f}s")
    
    print("\n" + "=" * 60)
    print("Testing gap satisfaction with randomization...")
    
    # Test gap satisfaction
    test_email = 'test2@example.com'
    
    # Simulate sending an email and checking gap satisfaction
    print(f"\nSimulating email send for {test_email}:")
    
    # Record a send (this generates the next randomized gap)
    rate_limiter.record_sent(test_email)
    next_gap = rate_limiter.next_gap_time[test_email]
    print(f"  Next required gap: {next_gap:.2f}s")
    
    # Check gap satisfaction immediately (should be False)
    is_satisfied = rate_limiter.is_gap_satisfied(test_email)
    wait_time = rate_limiter.get_gap_wait_time(test_email)
    print(f"  Gap satisfied immediately: {is_satisfied}")
    print(f"  Wait time required: {wait_time:.2f}s")
    
    # Simulate waiting half the time
    half_wait = wait_time / 2
    print(f"\n  Simulating {half_wait:.1f}s wait...")
    time.sleep(half_wait)
    
    is_satisfied = rate_limiter.is_gap_satisfied(test_email)
    remaining_wait = rate_limiter.get_gap_wait_time(test_email)
    print(f"  Gap satisfied after {half_wait:.1f}s: {is_satisfied}")
    print(f"  Remaining wait time: {remaining_wait:.2f}s")
    
    print("\n" + "=" * 60)
    print("Randomization test completed successfully!")

if __name__ == "__main__":
    test_randomization()
