"""
engine.py — Main Pipeline Orchestrator for IMDIE.

Combines all 15 modules into a seamless, modular, scalable intake engine:
1. Document Classification
2. Data Extraction
3. Feature Mapping
4. Unit Normalization
5. Duplicate Resolution
6. Feature Validation
7. Data Quality Assessment
8 & 9. Mandatory/Optional Logic & Missing Assistant
10. Multi-Report Fusion
11. Feature Routing Engine
12. Expert Availability Check
13. Adaptive Prediction Protocol
14. Prediction Confidence Scoring
15. Audit Logging
"""

import logging
from typing import Any, Dict, List, Union

from . import (
    adaptive_strategy,
    audit_logger,
    availability,
    classifier,
    config,
    confidence,
    extractor,
    fuser,
    mapper,
    missing_assistant,
    normalizer,
    prediction_orchestrator,
    prediction_reliability_layer,
    quality_scorer,
    router,
    template_detector,
    validator,
)

logger = logging.getLogger("imdie.engine")


class MultimodalIntakeEngine:
    """Intelligent Multimodal Data Intake Engine (IMDIE)."""

    def __init__(self):
        self.audit = audit_logger.AuditLogger()

    def process_reports(
        self,
        reports_input: List[Union[str, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Execute complete 15-stage IMDIE pipeline on input reports.

        Args:
            reports_input: List of filepaths, text strings, or raw dictionaries.

        Returns:
            Structured JSON result containing patient profile, quality scores,
            missing assistant guidance, routed expert payloads, availability checks,
            adaptive strategy, prediction confidence, and audit trail.
        """
        self.audit.log_step("Pipeline Execution", "STARTED", f"Processing {len(reports_input)} uploaded documents")

        processed_reports: List[Dict[str, Any]] = []

        # Process each document independently through stages 1 to 6
        for idx, doc_item in enumerate(reports_input):
            doc_label = f"Document_{idx+1}"

            # Stage 1: Document Classification
            doc_type = classifier.classify_text_or_dict(doc_item)
            self.audit.log_step("Document Classification", "COMPLETED", {"doc": doc_label, "type": doc_type.value})

            # Stage 2: Data Extraction
            raw_extracted = extractor.extract_from_file_or_data(doc_item)
            self.audit.log_step("Data Extraction", "COMPLETED", {"doc": doc_label, "keys_extracted": len(raw_extracted)})

            # Stage 3: Feature Mapping
            mapped = mapper.map_extracted_features(raw_extracted)
            self.audit.log_step("Feature Mapping", "COMPLETED", {"doc": doc_label, "mapped_keys": sum(len(v) for k, v in mapped.items() if k != "UNMAPPED")})

            # Stage 2: Document Classification (evaluated strictly on primary non-demographic features)
            primary_clin_cnt = len([k for k in mapped.get("CLINICAL", {}).keys() if k not in ("Patient_ID", "Age", "Gender", "Height", "Weight", "BMI")])
            primary_wear_cnt = len(mapped.get("WEARABLE", {}))
            primary_gut_cnt = len(mapped.get("GUT_MICROBIOME", {}))

            active_mod_count = sum([primary_clin_cnt > 0, primary_wear_cnt > 0, primary_gut_cnt > 0])
            if active_mod_count > 1:
                doc_type = classifier.DocumentType.MULTIMODAL
            elif primary_gut_cnt > 0:
                doc_type = classifier.DocumentType.GUT_MICROBIOME
            elif primary_wear_cnt > 0:
                doc_type = classifier.DocumentType.WEARABLE
            elif primary_clin_cnt > 0:
                doc_type = classifier.DocumentType.CLINICAL
            else:
                doc_type = classifier.DocumentType.UNKNOWN

            self.audit.log_step("Document Classification", "COMPLETED", {"doc": doc_label, "type": doc_type.value})

            # Stage 4: Unit Normalization
            normalized = normalizer.normalize_mapped_dict(mapped)
            self.audit.log_step("Unit Normalization", "COMPLETED", {"doc": doc_label})

            # Stage 6: Feature Validation (Per-document clean)
            clean_normalized = {}
            doc_errors = []
            doc_warnings = []
            doc_verify = {}

            if "_error" in raw_extracted:
                doc_errors.append(raw_extracted["_error"])

            for mod, feat_dict in normalized.items():
                if mod == "UNMAPPED":
                    clean_normalized[mod] = feat_dict
                    continue
                clean_f, errs, warns, v_flags = validator.validate_feature_dict(feat_dict)
                clean_normalized[mod] = clean_f
                doc_errors.extend(errs)
                doc_warnings.extend(warns)
                doc_verify.update(v_flags)

            self.audit.log_step("Feature Validation", "COMPLETED", {"doc": doc_label, "errors": len(doc_errors), "warnings": len(doc_warnings)})

            doc_status = "EXTRACTED"
            if raw_extracted.get("_unreadable"):
                doc_status = "UNREADABLE"
            elif raw_extracted.get("_error"):
                doc_status = "PARSE_FAILED"
            elif len(doc_errors) > 0:
                doc_status = "FAILED"
            elif len(doc_verify) > 0:
                doc_status = "NEEDS_VERIFICATION"
            elif len(mapped.get("UNMAPPED", {})) > 0:
                doc_status = "PARTIAL"

            clean_normalized["metadata"] = {
                "document_index": idx,
                "filename": getattr(doc_item, "name", str(doc_item)),
                "source_file": getattr(doc_item, "name", str(doc_item)),
                "document_type": doc_type.value,
                "modality": doc_type.value,
                "detected_mime": extractor.detect_file_format_by_header(str(doc_item)),
                "parser_used": "pypdf" if str(doc_item).endswith(".pdf") else "python-docx" if str(doc_item).endswith(".docx") else "openpyxl" if str(doc_item).endswith(".xlsx") else "ocr_pillow" if str(doc_item).endswith((".jpg", ".jpeg", ".png", ".webp", ".tiff", ".heic")) else "regex_parser",
                "ocr_used": str(doc_item).lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".tiff", ".heic")) or "scanned" in str(doc_item).lower(),
                "raw_fields_count": len(raw_extracted),
                "mapped_canonical_fields": sum(len(v) for k, v in mapped.items() if k != "UNMAPPED"),
                "unmapped_fields": list(mapped.get("UNMAPPED", {}).keys()),
                "warnings_errors": doc_errors + doc_warnings,
                "status": doc_status,
                "error": raw_extracted.get("_error")
            }

            processed_reports.append(clean_normalized)

        # Stage 5 & 10: Multi-Report Fusion & Duplicate Resolution
        fused_profile, fusion_warnings = fuser.fuse_multiple_reports(processed_reports)
        self.audit.log_step("Multi-Report Fusion", "COMPLETED", {"patient_id": fused_profile.patient_id, "warnings": len(fusion_warnings)})

        # Gather cumulative verify flags & conflict map
        cumulative_verify_flags = {}
        for rep in processed_reports:
            for mod in ["CLINICAL", "WEARABLE", "GUT_MICROBIOME"]:
                feat_dict = rep.get(mod, {})
                _, _, _, v_flags = validator.validate_feature_dict(feat_dict)
                cumulative_verify_flags.update(v_flags)

        cumulative_conflict_map = getattr(fused_profile, "conflict_map", {})

        # Stage 7: Data Quality Assessment
        quality_scores = quality_scorer.calculate_data_quality_scores(
            fused_profile.clinical_features,
            fused_profile.wearable_features,
            fused_profile.gut_features,
            verify_flags=cumulative_verify_flags,
            conflict_map=cumulative_conflict_map
        )
        self.audit.log_step("Data Quality Assessment", "COMPLETED", quality_scores)

        # Stages 8 & 9: Mandatory vs Optional Logic & Missing Assistant
        clinical_missing = missing_assistant.analyze_missing_features(
            "CLINICAL", fused_profile.clinical_features, config.CLINICAL_MANDATORY, config.CLINICAL_OPTIONAL
        )
        wearable_missing = missing_assistant.analyze_missing_features(
            "WEARABLE", fused_profile.wearable_features, config.WEARABLE_MANDATORY, config.WEARABLE_OPTIONAL
        )
        gut_missing = missing_assistant.analyze_missing_features(
            "GUT_MICROBIOME", fused_profile.gut_features, config.GUT_MANDATORY, config.GUT_OPTIONAL
        )
        self.audit.log_step("Missing Feature Assistant", "COMPLETED")

        # Stage 11: Feature Routing Engine
        routed_payloads = router.route_features_to_experts(fused_profile)
        self.audit.log_step("Feature Routing Engine", "COMPLETED")

        # Stage 12: Expert Model Availability Check
        availability_map = availability.check_all_experts_availability(
            routed_payloads.clinical_payload,
            routed_payloads.wearable_payload,
            routed_payloads.gut_payload
        )
        self.audit.log_step("Expert Model Availability Check", "COMPLETED", {k: v.value for k, v in availability_map.items()})

        # Stage 13: Adaptive Prediction Protocol
        strategy = adaptive_strategy.AdaptivePredictionStrategy(availability_map)
        self.audit.log_step("Adaptive Prediction Protocol", "COMPLETED", strategy.to_dict())

        # Stage 14: Prediction Confidence Evaluator
        conf_eval = confidence.evaluate_prediction_confidence(availability_map, quality_scores)
        self.audit.log_step("Prediction Confidence Evaluator", "COMPLETED", conf_eval)

        # Build provenance map from processed_reports
        feature_provenance = {}
        for rep in processed_reports:
            for mod_key in ["CLINICAL", "WEARABLE", "GUT_MICROBIOME"]:
                raw_mod = rep.get(mod_key, {})
                for k, v in raw_mod.items():
                    if k != "_metadata":
                        if isinstance(v, dict):
                            feature_provenance[k] = {
                                "source_file": v.get("source_file", rep.get("metadata", {}).get("filename", "uploaded_report")),
                                "source_page": v.get("source_page", 1),
                                "raw_value": str(v.get("raw_value", v.get("value", ""))),
                                "extraction_method": v.get("extraction_method", rep.get("metadata", {}).get("parser_used", "PARSER")),
                                "confidence": float(v.get("confidence", 0.90 if rep.get("metadata", {}).get("ocr_used") else 1.0)),
                                "original_text_snippet": v.get("original_text_snippet", f"{k}: {v.get('raw_value', '')}")
                            }
                        else:
                            feature_provenance[k] = {
                                "source_file": rep.get("metadata", {}).get("filename", "uploaded_report"),
                                "source_page": 1,
                                "raw_value": str(v),
                                "extraction_method": rep.get("metadata", {}).get("parser_used", "PARSER"),
                                "confidence": 0.90 if rep.get("metadata", {}).get("ocr_used") else 1.0,
                                "original_text_snippet": f"{k}: {v}"
                            }

        # Calculate Phase 2 reliability report metadata
        rel_engine = prediction_reliability_layer.PredictionReliabilityLayer()
        reliability_report = rel_engine.evaluate_reliability(
            patient_profile=fused_profile.to_dict(),
            quality_scores=quality_scores,
            prediction_output=None,
            effective_pathway=strategy.to_dict().get("effective_pathway", "C+W+G")
        )

        # Calculate Phase 2 prediction orchestration metadata
        orchestrator = prediction_orchestrator.PredictionOrchestrator()
        orchestration_metadata = orchestrator.build_orchestration_metadata(
            patient_profile=fused_profile.to_dict(),
            quality_scores=quality_scores,
            effective_pathway=strategy.to_dict().get("effective_pathway", "C+W+G"),
            predictions=None,
            shap_available=True,
            rag_available=True
        )

        # Build final structured output payload
        output = {
            "patient_profile": fused_profile.to_dict(),
            "data_quality_scores": quality_scores,
            "verify_flags": cumulative_verify_flags,
            "conflict_map": cumulative_conflict_map,
            "different_patient_warning": getattr(fused_profile, "different_patient_warning", None),
            "processed_reports_metadata": [r.get("metadata", {}) for r in processed_reports],
            "provenance": feature_provenance,
            "missing_feature_assistant": {
                "CLINICAL": clinical_missing,
                "WEARABLE": wearable_missing,
                "GUT_MICROBIOME": gut_missing
            },
            "expert_routing": routed_payloads.to_dict(),
            "expert_availability": {k: v.value for k, v in availability_map.items()},
            "adaptive_prediction_strategy": strategy.to_dict(),
            "prediction_confidence": conf_eval,
            "reliability_report": reliability_report,
            "orchestration_metadata": orchestration_metadata,
            "audit_log": self.audit.to_dict()
        }

        self.audit.log_step("Pipeline Execution", "SUCCESS", "IMDIE Processing Completed Successfully")
        return output
