"""ML utilities package for DevScope.

Modules provided:
- feature_engineering.py: preprocessing and feature creation
- model_training.py: training pipelines and model persistence
- prediction_service.py: load model and predict
- matching_service.py: job matching logic
- comparison_routes.py: Flask blueprint for ML pages
"""

__all__ = [
    "feature_engineering",
    "model_training",
    "prediction_service",
    "matching_service",
    "comparison_routes",
]
