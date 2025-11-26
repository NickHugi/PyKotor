"""Tests for the improved designer controls.

These tests ensure that:
1. InputSmoother correctly smooths mouse input
2. InputAccelerator applies acceleration curves correctly
3. The control improvements don't break existing functionality

These tests are critical to ensure that the camera controls feel responsive
and professional, and that changes don't regress the user experience.
"""

from __future__ import annotations

import math
import unittest


class TestInputSmoother(unittest.TestCase):
    """Tests for the InputSmoother class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Import here to allow tests to run even if full toolset isn't available
        from toolset.gui.windows.designer_controls import InputSmoother
        self.InputSmoother = InputSmoother
    
    def test_initialization(self):
        """Test that InputSmoother initializes correctly."""
        smoother = self.InputSmoother(smoothing_factor=0.3)
        self.assertEqual(smoother.smoothing_factor, 0.3)
        self.assertFalse(smoother._initialized)
    
    def test_first_input_passthrough(self):
        """Test that first input is passed through unchanged."""
        smoother = self.InputSmoother(smoothing_factor=0.5)
        
        x, y = smoother.smooth(10.0, 20.0)
        
        self.assertEqual(x, 10.0)
        self.assertEqual(y, 20.0)
    
    def test_smoothing_reduces_jitter(self):
        """Test that smoothing reduces sudden changes."""
        smoother = self.InputSmoother(smoothing_factor=0.5)
        
        # Initial input
        smoother.smooth(0.0, 0.0)
        
        # Sudden large change
        x, y = smoother.smooth(100.0, 100.0)
        
        # Output should be between 0 and 100 (smoothed)
        self.assertGreater(x, 0)
        self.assertLess(x, 100)
        self.assertGreater(y, 0)
        self.assertLess(y, 100)
    
    def test_smoothing_converges(self):
        """Test that repeated inputs converge to target value."""
        smoother = self.InputSmoother(smoothing_factor=0.3)
        
        # Initialize
        smoother.smooth(0.0, 0.0)
        
        # Apply same input repeatedly
        for _ in range(50):
            x, y = smoother.smooth(100.0, 100.0)
        
        # Should be very close to target after many iterations
        self.assertAlmostEqual(x, 100.0, delta=1.0)
        self.assertAlmostEqual(y, 100.0, delta=1.0)
    
    def test_high_smoothing_is_slow(self):
        """Test that high smoothing factor means slower response."""
        slow_smoother = self.InputSmoother(smoothing_factor=0.9)
        fast_smoother = self.InputSmoother(smoothing_factor=0.1)
        
        # Initialize both
        slow_smoother.smooth(0.0, 0.0)
        fast_smoother.smooth(0.0, 0.0)
        
        # Apply same input
        slow_x, _ = slow_smoother.smooth(100.0, 100.0)
        fast_x, _ = fast_smoother.smooth(100.0, 100.0)
        
        # Slow smoother should have moved less
        self.assertLess(slow_x, fast_x)
    
    def test_reset(self):
        """Test that reset clears smoother state."""
        smoother = self.InputSmoother(smoothing_factor=0.5)
        
        # Use smoother
        smoother.smooth(50.0, 50.0)
        smoother.smooth(100.0, 100.0)
        
        # Reset
        smoother.reset()
        
        # Next input should be passthrough
        x, y = smoother.smooth(200.0, 200.0)
        self.assertEqual(x, 200.0)
        self.assertEqual(y, 200.0)
    
    def test_negative_values(self):
        """Test that negative values are handled correctly."""
        smoother = self.InputSmoother(smoothing_factor=0.3)
        
        smoother.smooth(0.0, 0.0)
        x, y = smoother.smooth(-50.0, -50.0)
        
        # Should be negative, between 0 and -50
        self.assertLess(x, 0)
        self.assertGreater(x, -50)


class TestInputAccelerator(unittest.TestCase):
    """Tests for the InputAccelerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        from toolset.gui.windows.designer_controls import InputAccelerator
        self.InputAccelerator = InputAccelerator
    
    def test_initialization(self):
        """Test that InputAccelerator initializes correctly."""
        accelerator = self.InputAccelerator(power=1.5, threshold=2.0)
        self.assertEqual(accelerator.power, 1.5)
        self.assertEqual(accelerator.threshold, 2.0)
    
    def test_below_threshold_linear(self):
        """Test that values below threshold are linear."""
        accelerator = self.InputAccelerator(power=2.0, threshold=10.0)
        
        # Input below threshold
        result = accelerator.accelerate(5.0)
        
        # Should be unchanged
        self.assertEqual(result, 5.0)
    
    def test_above_threshold_accelerated(self):
        """Test that values above threshold are accelerated."""
        accelerator = self.InputAccelerator(power=2.0, threshold=5.0)
        
        # Input above threshold
        result = accelerator.accelerate(10.0)
        
        # Should be greater than linear (10.0)
        self.assertGreater(result, 10.0)
    
    def test_negative_values_preserve_sign(self):
        """Test that negative values preserve their sign."""
        accelerator = self.InputAccelerator(power=2.0, threshold=5.0)
        
        # Negative input above threshold
        result = accelerator.accelerate(-10.0)
        
        # Should be negative
        self.assertLess(result, 0)
        
        # Magnitude should be accelerated
        self.assertLess(result, -10.0)
    
    def test_zero_unchanged(self):
        """Test that zero input produces zero output."""
        accelerator = self.InputAccelerator(power=2.0, threshold=5.0)
        
        result = accelerator.accelerate(0.0)
        
        self.assertEqual(result, 0.0)
    
    def test_power_affects_curve(self):
        """Test that different power values affect acceleration."""
        low_power = self.InputAccelerator(power=1.5, threshold=5.0)
        high_power = self.InputAccelerator(power=3.0, threshold=5.0)
        
        input_value = 15.0  # Well above threshold
        
        low_result = low_power.accelerate(input_value)
        high_result = high_power.accelerate(input_value)
        
        # Higher power should give more acceleration
        self.assertLess(low_result, high_result)
    
    def test_exact_threshold_linear(self):
        """Test that input exactly at threshold is linear."""
        accelerator = self.InputAccelerator(power=2.0, threshold=10.0)
        
        result = accelerator.accelerate(10.0)
        
        # At threshold, should be exactly linear
        self.assertEqual(result, 10.0)
    
    def test_acceleration_is_continuous(self):
        """Test that acceleration curve is continuous at threshold."""
        accelerator = self.InputAccelerator(power=2.0, threshold=10.0)
        
        # Just below threshold
        below = accelerator.accelerate(9.99)
        
        # Just above threshold
        above = accelerator.accelerate(10.01)
        
        # Should be very close (continuous)
        self.assertAlmostEqual(below, above, delta=0.1)


class TestControlsIntegration(unittest.TestCase):
    """Integration tests for the improved controls."""
    
    def test_smoother_and_accelerator_together(self):
        """Test that smoother and accelerator work well together."""
        from toolset.gui.windows.designer_controls import InputSmoother, InputAccelerator
        
        smoother = InputSmoother(smoothing_factor=0.2)
        accelerator = InputAccelerator(power=1.5, threshold=3.0)
        
        # Initialize smoother
        smoother.smooth(0.0, 0.0)
        
        # Simulate a sequence of mouse movements
        results = []
        for i in range(10):
            # Raw input: gradually increasing
            raw_x = i * 2.0
            raw_y = i * 2.0
            
            # Apply smoothing first
            smooth_x, smooth_y = smoother.smooth(raw_x, raw_y)
            
            # Then acceleration
            accel_x = accelerator.accelerate(smooth_x)
            accel_y = accelerator.accelerate(smooth_y)
            
            results.append((accel_x, accel_y))
        
        # Verify monotonically increasing (mostly)
        for i in range(1, len(results)):
            # Allow small variance due to smoothing
            self.assertGreaterEqual(
                results[i][0], results[i-1][0] - 1.0,
                f"X should generally increase: {results[i][0]} < {results[i-1][0]}"
            )
    
    def test_realistic_mouse_movement(self):
        """Test with realistic mouse movement patterns."""
        from toolset.gui.windows.designer_controls import InputSmoother, InputAccelerator
        
        smoother = InputSmoother(smoothing_factor=0.3)
        accelerator = InputAccelerator(power=1.3, threshold=3.0)
        
        # Simulate realistic mouse movement (small variations with occasional large moves)
        movements = [
            (1, 2), (2, 1), (3, 3), (2, 2), (1, 3),  # Small precise movements
            (15, 10), (14, 11), (16, 9),  # Fast movement
            (0, 0), (1, 0), (0, 1),  # Return to precise
        ]
        
        smoother.smooth(0.0, 0.0)  # Initialize
        
        for raw_x, raw_y in movements:
            smooth_x, smooth_y = smoother.smooth(float(raw_x), float(raw_y))
            accel_x = accelerator.accelerate(smooth_x)
            accel_y = accelerator.accelerate(smooth_y)
            
            # Results should be finite and reasonable
            self.assertTrue(math.isfinite(accel_x))
            self.assertTrue(math.isfinite(accel_y))


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and boundary conditions."""
    
    def setUp(self):
        """Set up test fixtures."""
        from toolset.gui.windows.designer_controls import InputSmoother, InputAccelerator
        self.InputSmoother = InputSmoother
        self.InputAccelerator = InputAccelerator
    
    def test_smoother_with_zero_factor(self):
        """Test smoother with zero smoothing factor."""
        smoother = self.InputSmoother(smoothing_factor=0.0)
        
        smoother.smooth(0.0, 0.0)
        x, y = smoother.smooth(100.0, 100.0)
        
        # With zero smoothing, should immediately reach target
        self.assertEqual(x, 100.0)
        self.assertEqual(y, 100.0)
    
    def test_smoother_with_one_factor(self):
        """Test smoother with maximum smoothing factor."""
        smoother = self.InputSmoother(smoothing_factor=1.0)
        
        smoother.smooth(0.0, 0.0)
        x, y = smoother.smooth(100.0, 100.0)
        
        # With maximum smoothing, should stay at initial value
        self.assertEqual(x, 0.0)
        self.assertEqual(y, 0.0)
    
    def test_accelerator_with_power_one(self):
        """Test accelerator with power of 1 (linear)."""
        accelerator = self.InputAccelerator(power=1.0, threshold=0.0)
        
        # Should be linear
        result = accelerator.accelerate(10.0)
        self.assertEqual(result, 10.0)
    
    def test_very_large_values(self):
        """Test with very large input values."""
        smoother = self.InputSmoother(smoothing_factor=0.3)
        accelerator = self.InputAccelerator(power=1.5, threshold=3.0)
        
        smoother.smooth(0.0, 0.0)
        
        # Large values
        smooth_x, smooth_y = smoother.smooth(1000000.0, 1000000.0)
        accel_x = accelerator.accelerate(smooth_x)
        
        # Should be finite
        self.assertTrue(math.isfinite(accel_x))
    
    def test_very_small_values(self):
        """Test with very small input values."""
        smoother = self.InputSmoother(smoothing_factor=0.3)
        accelerator = self.InputAccelerator(power=1.5, threshold=0.001)
        
        smoother.smooth(0.0, 0.0)
        
        # Very small values
        smooth_x, smooth_y = smoother.smooth(0.0001, 0.0001)
        accel_x = accelerator.accelerate(smooth_x)
        
        # Should be finite and close to input
        self.assertTrue(math.isfinite(accel_x))
        self.assertAlmostEqual(accel_x, smooth_x, delta=0.001)


if __name__ == "__main__":
    unittest.main()

