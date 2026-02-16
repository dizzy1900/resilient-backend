"""Unit tests for loading the trained AI model."""

import os
import pickle
import unittest

import numpy as np


class TestModelLoading(unittest.TestCase):
    """Tests for loading the ag_surrogate.pkl model file."""

    MODEL_PATH = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "ag_surrogate.pkl"
    )

    def test_model_file_exists(self):
        """Model file should exist on disk."""
        self.assertTrue(
            os.path.exists(self.MODEL_PATH),
            f"Model file not found at {self.MODEL_PATH}",
        )

    def test_model_loads_without_errors(self):
        """Model should load successfully without raising exceptions."""
        with open(self.MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        self.assertIsNotNone(model)

    def test_model_has_predict_method(self):
        """Loaded model should have a predict method."""
        with open(self.MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        self.assertTrue(hasattr(model, "predict"), "Model should have a predict method")
        self.assertTrue(callable(model.predict), "predict should be callable")

    def test_model_accepts_expected_input_shape(self):
        """Model should accept input with shape (n_samples, 3) for temp, rain, seed_type."""
        with open(self.MODEL_PATH, "rb") as f:
            model = pickle.load(f)

        # Test with valid input shape
        X = np.array([[25.0, 500.0, 0]])  # temp, rain, seed_type
        try:
            prediction = model.predict(X)
            self.assertEqual(len(prediction), 1, "Should return one prediction per sample")
        except Exception as e:
            self.fail(f"Model failed to predict with valid input: {e}")


if __name__ == "__main__":
    unittest.main()
