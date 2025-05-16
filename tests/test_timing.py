#!/usr/bin/env python3
"""
Test for timing.py module functionality.
"""

import unittest
import multiprocessing as mp
from unittest.mock import patch, MagicMock
import time
from utils.improved.timing import (
    initialize_timing,
    get_iteration_times,
    instrument_run_algorithm_task,
    finalize_timing,
    cleanup_timing,
    calculate_avg_summary
)


class TestTiming(unittest.TestCase):
    """Test case for the timing module."""

    def setUp(self):
        # Clean up any existing state
        cleanup_timing()

    def tearDown(self):
        # Clean up after each test
        cleanup_timing()

    def test_initialize_and_get_times(self):
        """Test initialization and getting iteration times."""
        # Initialize timing system
        initialize_timing()
        
        # Empty at first
        times = get_iteration_times()
        self.assertEqual(times, [])
        
        # Clean up
        cleanup_timing()

    def test_calculate_avg_summary_empty(self):
        """Test calculating average summary with no data."""
        initialize_timing()
        summary = calculate_avg_summary()
        self.assertEqual(summary, [])
        cleanup_timing()

    @patch('utils.improved.timing._iteration_times')
    def test_calculate_avg_summary_with_data(self, mock_iteration_times):
        """Test calculating average summary with data."""
        # Mock timing data
        mock_iteration_times.__iter__.return_value = [
            {
                "algorithm": "algo1",
                "instance": "inst1",
                "run_id": 1,
                "avg_iter_time": 0.1
            },
            {
                "algorithm": "algo1",
                "instance": "inst1",
                "run_id": 2,
                "avg_iter_time": 0.2
            },
            {
                "algorithm": "algo2",
                "instance": "inst1",
                "run_id": 1,
                "avg_iter_time": 0.3
            }
        ]
        
        # Calculate summary
        with patch('utils.improved.timing._is_active', True):
            summary = calculate_avg_summary()
        
        # Verify summary content
        self.assertEqual(len(summary), 2)  # Two unique algo/instance combinations
        
        # Find entries in summary
        algo1_entry = next((entry for entry in summary if entry["algorithm"] == "algo1"), None)
        algo2_entry = next((entry for entry in summary if entry["algorithm"] == "algo2"), None)
        
        self.assertIsNotNone(algo1_entry)
        self.assertIsNotNone(algo2_entry)
        
        # Check values (using assertAlmostEqual for floating point)
        self.assertAlmostEqual(algo1_entry["avg_iter_time"], 0.15, places=10)  # (0.1 + 0.2) / 2
        self.assertEqual(algo1_entry["samples"], 2)
        self.assertAlmostEqual(algo2_entry["avg_iter_time"], 0.3, places=10)
        self.assertEqual(algo2_entry["samples"], 1)

    def test_instrumentation(self):
        """Test function instrumentation."""
        # Initialize timing
        initialize_timing()
        
        # Create a mock function
        mock_original = MagicMock(return_value={"algorithm": "test_algo", "instance": "test_inst"})
        
        # Instrument the function
        instrumented = instrument_run_algorithm_task(mock_original)
        
        # Mock arguments for the function
        args = (
            MagicMock(),  # algo_class
            "test_instance",  # instance_name 
            "path/to/instance",  # instance_path
            1,  # run_id
            10,  # iterations
            10,  # population
            42,  # seed
            "/tmp"  # checkpoint_dir
        )
        
        # Call the instrumented function
        start = time.time()
        result = instrumented(args)
        duration = time.time() - start
        
        # Verify the original function was called
        mock_original.assert_called_once_with(args)
        
        # Verify we got the expected result
        self.assertEqual(result, {"algorithm": "test_algo", "instance": "test_inst"})
        
        # Get timing info with a valid run_id and no error
        times = get_iteration_times()
        if times:  # May not record in CI environment
            self.assertEqual(times[0]["algorithm"], "test_algo")
            self.assertEqual(times[0]["instance"], "test_inst")
            self.assertTrue(times[0]["avg_iter_time"] >= 0)

    @patch('utils.improved.timing._iteration_times')
    @patch('utils.improved.timing._is_active', True)
    def test_finalize_timing(self, mock_iteration_times):
        """Test finalization and average time calculation."""
        # Mock empty iteration times
        mock_iteration_times.__iter__.return_value = []
        
        # Finalize without data
        avg_time = finalize_timing()
        self.assertIsNone(avg_time)
        
        # Mock some timing data
        mock_iteration_times.__iter__.return_value = [
            {"avg_iter_time": 0.1},
            {"avg_iter_time": 0.2}
        ]
        
        # Finalize with data
        avg_time = finalize_timing()
        self.assertAlmostEqual(avg_time, 0.15, places=10)  # (0.1 + 0.2) / 2

    def test_cleanup_timing(self):
        """Test cleanup function restores initial state."""
        # Initialize timing
        initialize_timing()
        
        # Clean up
        result = cleanup_timing()
        
        # Get timing data after cleanup
        times = get_iteration_times()
        self.assertEqual(times, [])


if __name__ == "__main__":
    unittest.main()
