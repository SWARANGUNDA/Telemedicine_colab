"""
ai/shims.py — Compatibility shims for unpickling historical model artifacts.
"""

import sys
import types

def register_compatibility_shims():
    if "expert_models" not in sys.modules or getattr(sys.modules["expert_models"], "__path__", None) is None:
        expert_models_pkg = types.ModuleType("expert_models")
        expert_models_pkg.__path__ = []
        sys.modules["expert_models"] = expert_models_pkg

    if "fusion_engine" not in sys.modules or getattr(sys.modules["fusion_engine"], "__path__", None) is None:
        fusion_engine_pkg = types.ModuleType("fusion_engine")
        fusion_engine_pkg.__path__ = []
        sys.modules["fusion_engine"] = fusion_engine_pkg

    try:
        from ai.training.clinical import trainer, preprocessing, artifact_manager, data_loader, split, baselines
        from ai.training.fusion import meta_trainer, oof_generator, train_v4_fusion, fusion_data_loader
        from ai.evaluation import calibration, metrics, threshold_tuner, fusion_evaluator
        from ai.inference import expert_inference, fusion_inference
        from ai.explainability import expert_explainer, fusion_explainer
        from ai.config import expert_config, fusion_config

        sys.modules["expert_models.trainer"] = trainer
        sys.modules["expert_models.preprocessing"] = preprocessing
        sys.modules["expert_models.artifact_manager"] = artifact_manager
        sys.modules["expert_models.data_loader"] = data_loader
        sys.modules["expert_models.split"] = split
        sys.modules["expert_models.baselines"] = baselines
        sys.modules["expert_models.calibration"] = calibration
        sys.modules["expert_models.metrics"] = metrics
        sys.modules["expert_models.threshold_tuner"] = threshold_tuner
        sys.modules["expert_models.inference"] = expert_inference
        sys.modules["expert_models.explainer"] = expert_explainer
        sys.modules["expert_models.config"] = expert_config

        sys.modules["fusion_engine.meta_trainer"] = meta_trainer
        sys.modules["fusion_engine.oof_generator"] = oof_generator
        sys.modules["fusion_engine.train_v4_fusion"] = train_v4_fusion
        sys.modules["fusion_engine.fusion_data_loader"] = fusion_data_loader
        sys.modules["fusion_engine.config"] = fusion_config
        sys.modules["fusion_engine.inference"] = fusion_inference
        sys.modules["fusion_engine.fusion_explainer"] = fusion_explainer
        sys.modules["fusion_engine.evaluator"] = fusion_evaluator
    except Exception:
        pass

register_compatibility_shims()
