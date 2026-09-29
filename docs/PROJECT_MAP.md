# TeleMed AI: Comprehensive Repository Architecture & Project Map

## 1. Top-Level Repository Structure

The TeleMed repository has been systematically structured to decouple production runtime applications, machine learning assets, microservices, testing infrastructure, deployment definitions, and historical research archives into clearly delineated domains.

```
TeleMed/
├── README.md                          # Primary project overview, quickstart & architecture summary
├── Doctor_Review_Report_v12.docx      # Concise clinical reference manual for modalities, features & formulas
├── .gitignore                         # Comprehensive git ignore rules for artifacts & runtime dirs
├── .env.example                       # Environment variables template for development & production
├── .env.production.example            # Production environment template
│
├── docs/                              # System documentation, specifications, architecture & review guides
│   ├── PROJECT_MAP.md                 # Complete repository directory and module index (this file)
│   ├── ACTIVE_COMPONENTS.md           # Authoritative index of active production components vs legacy assets
│   ├── REVIEW_GUIDE.md                # Evaluator & B.Tech defense guide, test commands, architectural flow
│   ├── SRS/                           # Software Requirements Specifications (final & phase history)
│   ├── architecture/                  # Architectural documents, diagrams, and UML models
│   ├── api/                           # API contracts, OpenAPI specifications, and endpoint catalogs
│   ├── deployment/                    # Production deployment procedures and infrastructure notes
│   ├── testing/                       # Test strategy, coverage metrics, and audit closure evidence
│   └── research/                      # Scientific research notes, clinical guidelines, and citations
│
├── app/                               # Full-stack production application source code
│   ├── backend/                       # FastAPI asynchronous REST & WebSocket backend service
│   │   ├── main.py                    # Application entry point, CORS, security middleware & router assembly
│   │   ├── config.py                  # Environment settings, secret validation, runtime paths
│   │   ├── database_legacy.py         # SQLite / PostgreSQL unified database abstraction layer
│   │   ├── security.py                # JWT authentication, Argon2id hashing, sliding window rate limiting
│   │   ├── auth.py                    # Role-Based Access Control (RBAC) dependencies
│   │   ├── celery_app.py              # Asynchronous Celery distributed worker configuration
│   │   ├── session_manager.py         # In-memory and persistent patient intake session state machine
│   │   ├── prometheus_metrics.py      # Prometheus telemetry metrics exporters
│   │   ├── api/                       # Modular FastAPI APIRouters
│   │   │   ├── auth_routes.py         # Registration, login, JWT token refresh, session validation
│   │   │   ├── intake_routes.py       # Multimodal file upload, parsing, quality scoring & confirmation
│   │   │   ├── predict_routes.py      # 5-disease risk prediction across 7 adaptive pathways
│   │   │   ├── xai_routes.py          # Unified TreeSHAP attribution & feature importance generation
│   │   │   ├── rag_routes.py          # Grounded Clinical RAG report generation & interactive Q&A
│   │   │   ├── records_routes.py      # Longitudinal patient health records & document management
│   │   │   ├── consultation_routes.py # Teleconsultation lifecycle, chat, WebRTC signaling & transcripts
│   │   │   ├── doctor_verification_routes.py # Medical license verification & credentialing
│   │   │   ├── admin_routes.py        # System administration, user governance, audit logging
│   │   │   ├── ops_monitoring_routes.py # Health diagnostics, database connection check, DB migration
│   │   │   └── websocket_routes.py    # Real-time WebSocket connection handling for chat & teleconsults
│   │   ├── models/                    # SQLAlchemy database models
│   │   ├── schemas/                   # Pydantic request and response validation schemas
│   │   ├── services/                  # Backend application services wrapping AI & platform logic
│   │   └── database/                  # PostgreSQL database connection pool & session factory
│   └── frontend/                      # React 18 + Vite SPA with Tailwind-free custom CSS design system
│       ├── src/                       # React components, pages, context, and services
│       ├── public/                    # Static assets, branding icons, and imagery
│       ├── package.json               # Frontend dependencies and build scripts
│       └── vite.config.js             # Vite build, chunking, and dev proxy configuration
│
├── ai/                                # Machine learning, multi-expert models & multimodal fusion
│   ├── datasets/                      # Approved dataset assets, generation pipelines & feature schemas
│   │   ├── final/                     # V4 publication-grade multimodal dataset (100k cohort)
│   │   │   ├── clinical_v4.csv        # 18-feature clinical laboratory cohort
│   │   │   ├── wearable_v4.csv        # 15-feature wearable & CGM biosensor cohort
│   │   │   ├── gut_v4.csv             # 20-taxa gut microbiome sequencing cohort
│   │   │   ├── labels_v4.csv          # Multi-label ground truth (T2D, Prediabetes, Obesity, MetSyn, NAFLD)
│   │   │   ├── patient_metadata_v4.csv# Demographics, age, gender, recording duration metadata
│   │   │   └── {train,val,test}_ids_v4.csv # Leakage-free stratified cohort split index
│   │   ├── generation/                # Reproducible synthetic dataset generators
│   │   │   ├── generate_multimodal_v4_dataset.py # Master V4 100k multimodal generator
│   │   │   ├── clinical/              # Clinical dataset generator engine
│   │   │   ├── wearable_cgm/          # Wearable & Continuous Glucose Monitor generator
│   │   │   └── gut_microbiome/        # 16S rRNA gut microbiome taxonomic generator
│   │   └── schemas/                   # Canonical JSON predictor feature schemas
│   ├── models/                        # Authoritative serialized model payloads
│   │   ├── clinical/                  # Clinical expert V4 payload (CatBoost, ROC-AUC 0.9996)
│   │   ├── wearable_cgm/              # Wearable CGM expert V4 payload (CatBoost, ROC-AUC 0.9961)
│   │   ├── gut_microbiome/            # Gut microbiome expert V4 payload (LightGBM, ROC-AUC 0.9972)
│   │   └── fusion/                    # 7-pathway multimodal fusion meta-learner payloads
│   ├── training/                      # Model training, hyperparameter optimization & ensembling scripts
│   │   ├── clinical/                  # Clinical expert training pipeline & artifact managers
│   │   ├── wearable_cgm/              # Wearable expert training pipeline
│   │   ├── gut_microbiome/            # Gut microbiome expert training pipeline
│   │   └── fusion/                    # Multimodal late fusion training & stacking pipelines
│   ├── inference/                     # Production inference engines and dynamic pathway routers
│   │   ├── v3_scientific_router.py    # Evidence-based 7-pathway dynamic router
│   │   ├── v3_inference_engine.py     # Multi-expert inference execution engine
│   │   ├── fusion_inference.py        # End-to-end multimodal fusion prediction engine
│   │   └── adaptive_router.py         # Missing-modality dynamic assembly router
│   ├── explainability/                # Explainable AI (XAI) engines & visualization tools
│   │   ├── unified_xai_engine.py      # Unified TreeSHAP explainer & attribution layer
│   │   ├── expert_explainer.py        # Feature-level SHAP explainers per disease
│   │   └── fusion_explainer.py        # Modality contribution weight calculator
│   ├── evaluation/                    # Cross-validation, threshold tuning & metric calculators
│   └── config/                        # AI hyperparameters, feature lists & dataset configurations
│
├── services/                          # Decoupled domain microservices and AI support engines
│   ├── multimodal_intake/             # Intelligent Multimodal Data Intake Engine (IMDIE)
│   │   ├── engine.py                  # Master IMDIE pipeline orchestrator (Stages 1–15)
│   │   ├── extractor.py               # Multi-format document parser (PDF, OCR, TXT, CSV, JSON)
│   │   ├── mapper.py                  # Clinical synonym mapping & canonical alignment
│   │   ├── normalizer.py              # Unit conversion & physiological bound validation
│   │   ├── validator.py               # Modality-specific range validation & rule checks
│   │   ├── quality_scorer.py          # Data completeness, integrity & noise quality scoring
│   │   ├── v3_schema_validator.py     # V3/V4 strict intake schema validator
│   │   └── config.py                  # IMDIE feature schemas, physiological bounds & regexes
│   ├── medical_rag/                   # Grounded Medical Retrieval-Augmented Generation Engine
│   │   ├── rag_service.py             # Medical RAG pipeline orchestrator (Report & Q&A modes)
│   │   ├── generator.py               # Grounded synthesis generator with strict evidence binding
│   │   ├── retriever.py               # Cosine similarity evidence retriever from vector store
│   │   ├── vector_store.py            # Local dense vector index & embedding storage
│   │   ├── ingestion.py               # Guideline chunker, metadata tagger & index builder
│   │   ├── post_validator.py          # Zero-hallucination citation validator & safety guardrails
│   │   ├── source_manifest.py         # Authoritative guideline bibliography manifest
│   │   └── data/raw_documents/        # Authoritative clinical guidelines (ADA, WHO, AASLD, AHA, ISAPP)
│   ├── report_processing/             # Report generation, formatting, and PDF export services
│   └── realtime/                      # WebRTC signaling and WebSocket event distribution
│
├── tests/                             # Unified 16-suite test regression harness (142 tests passing)
│   ├── unit/                          # Unit tests for individual extractors, parsers & scorers
│   ├── integration/                   # Cross-service integration tests (IMDIE -> AI -> RAG)
│   ├── security/                      # RBAC, doctor verification, rate limiting, and audit governance
│   ├── e2e/                           # End-to-end user workflows (Patient, Doctor, Admin, Teleconsult)
│   ├── ml/                            # Machine learning model precision, calibration & XAI tests
│   └── fixtures/                      # Test fixtures and raw sample clinical reports
│       ├── medical_reports/           # Multi-format clinical PDFs, CSVs, TXTs
│       └── ocr/                       # Scanned medical report images for OCR verification
│
├── deployment/                        # Production deployment configurations & containerization
│   ├── docker/                        # Dockerfiles and Docker Compose orchestration
│   │   ├── docker-compose.yml         # Development & testing multi-container stack
│   │   ├── docker-compose.prod.yml    # Production-hardened container stack
│   │   └── Dockerfile.backend         # Backend production Docker containerfile
│   ├── nginx/ssl/                     # Nginx reverse proxy configuration & TLS certificates
│   ├── postgres/                      # PostgreSQL init scripts and schema migrations
│   └── monitoring/                    # Prometheus and Grafana monitoring configurations
│
├── data/                              # Non-training sample data and reference fixtures
│   └── samples/                       # Sample patient payloads for demonstrations
│
├── reports/                           # Final evaluation summaries, audit closures & benchmarks
│   ├── final/                         # Final audit closure reports & production readiness sign-offs
│   └── evaluation/                    # Cross-modality benchmark tables & ROC-AUC curves
│
├── runtime/                           # Ephemeral runtime generated files (excluded from git)
│   ├── uploads/                       # Temporary file uploads during intake
│   ├── temp/                          # Scratch processing directory
│   ├── logs/                          # System, audit, and worker log outputs
│   ├── generated/                     # Generated clinical PDF reports and charts
│   └── backups/                       # Local SQLite and PostgreSQL database snapshots
│
└── archive/                           # Preserved historical research artifacts (Never deleted)
    ├── v1/                            # Phase 1 historical datasets (20k cohort) & generators
    ├── v2/                            # Phase 2 experimental code & scripts
    ├── v3/                            # Phase 3/4 validation scripts & historical models
    ├── legacy_models/                 # Historical V1/V2/V3 model checkpoints (clinical, wearable, gut, fusion)
    ├── legacy_datasets/               # Historical split tables and benchmark datasets
    ├── experimental_code/             # Exploratory research notebooks and scratch scripts
    ├── old_tests/                     # Deprecated sprint-specific verification scripts
    ├── old_reports/                   # Sprint audit reports and milestone summaries
    └── miscellaneous/                 # Legacy test recordings, distribution reports, and scratch files
```
