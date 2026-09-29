import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import PublicCanvasLayout from '../components/landing/PublicCanvasLayout';
import Features3DVisual from '../components/landing/Features3DVisual';
import { Layers, Brain, Sparkles, ShieldCheck, Stethoscope, ArrowRight, Eye, Watch, Dna, FileText, CheckCircle2, Activity, Zap, Lock, Cpu, BarChart3, Database } from 'lucide-react';

export default function FeaturesPage({ user, onOpenAuth }) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');

  const handleGetStarted = () => {
    if (user) {
      const dashboardPath = user.role === 'ADMIN' ? '/admin/dashboard' : user.role === 'DOCTOR' ? '/doctor/dashboard' : '/dashboard';
      navigate(dashboardPath);
    } else if (onOpenAuth) {
      onOpenAuth('register');
    } else {
      navigate('/register');
    }
  };

  // Exact SRS Report Feature Schema Data (18 Clinical, 15 Wearable, 40 Gut)
  const modalityDetails = {
    overview: {
      title: 'Multimodal Stacking & Pathway Fusion',
      tagline: 'Dynamic Pathway Routing based on available patient data streams',
      desc: 'TeleMed AI intelligently routes available inputs through 7 distinct pathway combinations (Pathway A through G). Whether a patient provides clinical labs only, wearables only, or all 3 modalities, the fusion stacking engine outputs calibrated probabilistic risk scores across 82 total feature streams.',
      chips: ['Pathway A (C+W+G)', 'Pathway B (C+W)', 'Pathway C (C+G)', 'Pathway D (W+G)', 'Pathway E (Clinical)', 'Pathway F (Wearables)', 'Pathway G (Gut)'],
      metrics: [
        { label: 'Total Feature Streams', val: '82 Input Features' },
        { label: 'Fusion Pathways', val: '7 Stacking Options' },
        { label: 'Condition Targets', val: '5 Disease Profiles' }
      ]
    },
    clinical: {
      title: 'Clinical Biomarkers Engine (18 Features)',
      tagline: 'Laboratory chemistry, glycemic panels, hepatic & renal markers',
      desc: 'Processes 18 SRS-spec blood chemistry, metabolic panels, and vital sign metrics extracted automatically via OCR from lab PDF reports or manual intake. Trained on CatBoost ensemble models with Platt scaling calibration.',
      chips: ['HbA1c (%)', 'Fasting Blood Glucose', 'LDL / HDL Cholesterol', 'Triglycerides', 'ALT / AST Liver Enzymes', 'Systolic & Diastolic BP', 'Age & Biological Gender', 'Height & Weight (BMI)', 'Waist Circumference', 'Family History Risks'],
      metrics: [
        { label: 'SRS Predictors', val: '18 Biomarkers' },
        { label: 'Extraction Pipeline', val: 'Tesseract OCR + Regex Alias' },
        { label: 'Model Artifact', val: 'clinical_v4_expert_payload' }
      ]
    },
    wearable: {
      title: 'Continuous Wearable & CGM Telemetry (15 Metrics)',
      tagline: 'Smartwatch sensor streams (10) & continuous glucose monitoring (5)',
      desc: 'Ingests 15 SRS-spec continuous time-series metrics combining 10 smartwatch sensor metrics with 5 continuous glucose monitor (CGM) parameters. Evaluates autonomic nervous system balance, HRV RMSSD, and circadian sleep fragmentation.',
      chips: ['Average Daily Steps', 'Active & Sedentary Minutes', 'Resting Heart Rate (BPM)', 'HRV RMSSD (ms)', 'Sleep Duration & Efficiency', 'Autonomic Stress Score', 'Activity Caloric Expenditure', 'CGM Average Glucose & CV', 'CGM Time-In-Range (TIR/TAR/TBR)'],
      metrics: [
        { label: 'SRS Sensor Metrics', val: '15 Telemetry Features' },
        { label: 'Autonomic Indicator', val: 'HRV RMSSD & Stress Index' },
        { label: 'Model Artifact', val: 'wearable_v4_expert_payload' }
      ]
    },
    gut: {
      title: 'Gut Microbiome Taxa Engine (40 Bacterial Taxa)',
      tagline: 'Metagenomic 16S/shotgun taxa abundance & derived ecological indices',
      desc: 'Analyzes metagenomic sequencing profiles across 40 SRS-spec bacterial taxa and 9 derived ecological/functional indices. Identifies metabolic dysbiosis patterns linked to systemic low-grade inflammation and insulin resistance.',
      chips: ['Akkermansia Muciniphila', 'Faecalibacterium Prausnitzii', 'Roseburia Intestinalis', 'Bifidobacterium (Longum/Adolescentis)', 'Bacteroides (Thetaiotaomicron/Vulgatus)', 'Prevotella Copri', 'Blautia Wexlerae', 'Collinsella Aerofaciens', 'Shannon Alpha Diversity Index'],
      metrics: [
        { label: 'SRS Bacterial Taxa', val: '40 Microbial Features' },
        { label: 'Ecological Indices', val: '9 Derived Functional Indices' },
        { label: 'Model Artifact', val: 'gut_v4_expert_payload' }
      ]
    }
  };

  const featureCards = [
    {
      icon: Layers,
      title: 'Multi-Modal Data Integration',
      desc: 'Combine 18 clinical labs, 15 wearable metrics, and 40 gut taxa for a 360° health view.',
      bgColor: 'bg-teal-50',
      iconColor: 'text-teal-600',
      borderColor: 'border-t-teal-500 shadow-teal-500/10',
      tag: 'C + W + G Fusion'
    },
    {
      icon: Brain,
      title: 'AI-Powered Risk Prediction',
      desc: 'Advanced CatBoost & XGBoost models predict risk across 5 chronic disease targets.',
      bgColor: 'bg-blue-50',
      iconColor: 'text-blue-600',
      borderColor: 'border-t-blue-500 shadow-blue-500/10',
      tag: '5 Condition Targets'
    },
    {
      icon: Eye,
      title: 'Explainable AI (TreeSHAP)',
      desc: 'Understand predictions with clear feature attributions and key driving biomarker factors.',
      bgColor: 'bg-purple-50',
      iconColor: 'text-purple-600',
      borderColor: 'border-t-purple-500 shadow-purple-500/10',
      tag: 'Transparent XAI'
    },
    {
      icon: Sparkles,
      title: 'Personalized Insights',
      desc: 'Get personalized health insights and evidence-grounded lifestyle recommendations.',
      bgColor: 'bg-cyan-50',
      iconColor: 'text-cyan-600',
      borderColor: 'border-t-cyan-500 shadow-cyan-500/10',
      tag: 'Guideline-Grounded'
    },
    {
      icon: Stethoscope,
      title: 'Clinical Decision Support',
      desc: 'Evidence-based insights to support doctors and multidisciplinary care teams.',
      bgColor: 'bg-indigo-50',
      iconColor: 'text-indigo-600',
      borderColor: 'border-t-indigo-500 shadow-indigo-500/10',
      tag: 'Specialist Workspace'
    },
    {
      icon: ShieldCheck,
      title: 'Secure & Compliant',
      desc: 'Enterprise-grade security with encrypted data storage and strict RBAC role boundaries.',
      bgColor: 'bg-emerald-50',
      iconColor: 'text-emerald-600',
      borderColor: 'border-t-emerald-500 shadow-emerald-500/10',
      tag: 'Encrypted & Audited'
    }
  ];

  return (
    <PublicCanvasLayout user={user} onOpenAuth={onOpenAuth}>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-20">
        
        {/* 1. HERO SECTION matching SRS Specification */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-sm font-bold shadow-2xs">
              <Sparkles className="w-4 h-4 text-blue-600" />
              <span>Features</span>
            </div>
            
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-900 tracking-tight leading-[1.1]">
              Powerful Features for <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600">
                Smarter Healthcare.
              </span>
            </h1>
            
            <p className="text-base sm:text-lg text-slate-600 max-w-xl font-medium leading-relaxed">
              TeleMed AI brings together multiple health signals to deliver comprehensive insights and support better clinical decisions.
            </p>

            {/* SRS Specification Feature Chips */}
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <span className="px-4 py-2 rounded-full bg-blue-50 border border-blue-200 text-blue-800 text-xs sm:text-sm font-extrabold flex items-center gap-2 shadow-2xs">
                <FileText className="w-4 h-4 text-blue-600" />
                <span>18 Clinical Biomarkers</span>
              </span>
              <span className="px-4 py-2 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs sm:text-sm font-extrabold flex items-center gap-2 shadow-2xs">
                <Watch className="w-4 h-4 text-emerald-600" />
                <span>15 Wearable Metrics</span>
              </span>
              <span className="px-4 py-2 rounded-full bg-purple-50 border border-purple-200 text-purple-800 text-xs sm:text-sm font-extrabold flex items-center gap-2 shadow-2xs">
                <Dna className="w-4 h-4 text-purple-600" />
                <span>40 Gut Microbial Taxa</span>
              </span>
            </div>
          </div>

          {/* 3D Body Hologram Visual */}
          <div className="lg:col-span-5 flex justify-center">
            <Features3DVisual />
          </div>

        </div>

        {/* 2. INTERACTIVE MULTIMODAL EXPLORER SECTION */}
        <section className="space-y-8 pt-4">
          <div className="text-center space-y-3 max-w-3xl mx-auto">
            <h2 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
              Interactive Multimodal Intelligence Explorer
            </h2>
            <p className="text-base text-slate-600 font-medium">
              Click any modality tab below to inspect live feature schemas, model payloads, and data pathways.
            </p>
          </div>

          {/* Horizontally Aligned Outlined Modality Tabs */}
          <div className="w-full overflow-x-auto pb-2 flex justify-start md:justify-center">
            <div className="inline-flex items-center flex-nowrap gap-2.5 p-2 rounded-2xl bg-white/95 border border-slate-200/90 shadow-md">
              
              <button
                onClick={() => setActiveTab('overview')}
                className={`px-4 sm:px-5 py-2.5 rounded-xl font-extrabold text-xs sm:text-sm transition-all flex items-center gap-2 cursor-pointer shrink-0 whitespace-nowrap ${
                  activeTab === 'overview'
                    ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-md shadow-blue-500/25 ring-2 ring-blue-500/30'
                    : 'border border-slate-200/80 bg-slate-50/60 hover:bg-white hover:border-slate-300 text-slate-700 hover:text-blue-600 shadow-2xs'
                }`}
              >
                <Layers className="w-4 h-4 shrink-0" />
                <span>Overview & Fusion</span>
              </button>

              <button
                onClick={() => setActiveTab('clinical')}
                className={`px-4 sm:px-5 py-2.5 rounded-xl font-extrabold text-xs sm:text-sm transition-all flex items-center gap-2 cursor-pointer shrink-0 whitespace-nowrap ${
                  activeTab === 'clinical'
                    ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-md shadow-blue-500/25 ring-2 ring-blue-500/30'
                    : 'border border-slate-200/80 bg-slate-50/60 hover:bg-white hover:border-slate-300 text-slate-700 hover:text-blue-600 shadow-2xs'
                }`}
              >
                <FileText className="w-4 h-4 shrink-0" />
                <span>Clinical Labs (18 Features)</span>
              </button>

              <button
                onClick={() => setActiveTab('wearable')}
                className={`px-4 sm:px-5 py-2.5 rounded-xl font-extrabold text-xs sm:text-sm transition-all flex items-center gap-2 cursor-pointer shrink-0 whitespace-nowrap ${
                  activeTab === 'wearable'
                    ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-md shadow-blue-500/25 ring-2 ring-blue-500/30'
                    : 'border border-slate-200/80 bg-slate-50/60 hover:bg-white hover:border-slate-300 text-slate-700 hover:text-blue-600 shadow-2xs'
                }`}
              >
                <Watch className="w-4 h-4 shrink-0" />
                <span>Wearable & CGM (15 Metrics)</span>
              </button>

              <button
                onClick={() => setActiveTab('gut')}
                className={`px-4 sm:px-5 py-2.5 rounded-xl font-extrabold text-xs sm:text-sm transition-all flex items-center gap-2 cursor-pointer shrink-0 whitespace-nowrap ${
                  activeTab === 'gut'
                    ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-md shadow-blue-500/25 ring-2 ring-blue-500/30'
                    : 'border border-slate-200/80 bg-slate-50/60 hover:bg-white hover:border-slate-300 text-slate-700 hover:text-blue-600 shadow-2xs'
                }`}
              >
                <Dna className="w-4 h-4 shrink-0" />
                <span>Gut Microbiome (40 Taxa)</span>
              </button>

            </div>
          </div>

          {/* Active Tab Details Display Panel */}
          {(() => {
            const data = modalityDetails[activeTab];
            return (
              <div className="p-8 sm:p-12 rounded-3xl bg-white/95 backdrop-blur-xl border border-slate-200/90 shadow-2xl space-y-6">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-100 pb-6">
                  <div>
                    <h3 className="text-2xl sm:text-3xl font-black text-slate-900">{data.title}</h3>
                    <p className="text-sm sm:text-base font-bold text-blue-600 mt-1">{data.tagline}</p>
                  </div>
                  <span className="px-4 py-2 rounded-full bg-blue-50 text-blue-700 font-extrabold text-xs sm:text-sm border border-blue-200 shadow-2xs">
                    V4 UNIFIED ENGINE ACTIVE
                  </span>
                </div>

                <p className="text-base sm:text-lg text-slate-600 leading-relaxed font-medium">
                  {data.desc}
                </p>

                {/* Key Metrics Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 pt-2">
                  {data.metrics.map((m, idx) => (
                    <div key={idx} className="p-5 rounded-2xl bg-slate-50 border border-slate-200/90 space-y-1.5 shadow-2xs">
                      <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">{m.label}</span>
                      <span className="text-lg font-black text-slate-900">{m.val}</span>
                    </div>
                  ))}
                </div>

                {/* Feature Chips */}
                <div className="space-y-3 pt-2">
                  <h4 className="text-xs font-black text-slate-900 uppercase tracking-wider">Active Verified Predictors:</h4>
                  <div className="flex flex-wrap gap-2.5">
                    {data.chips.map((chip, idx) => (
                      <span key={idx} className="px-4 py-2 rounded-xl bg-blue-50/80 border border-blue-200/80 text-blue-900 text-xs sm:text-sm font-extrabold flex items-center gap-2 shadow-2xs">
                        <CheckCircle2 className="w-4 h-4 text-blue-600" />
                        <span>{chip}</span>
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            );
          })()}
        </section>

        {/* 3. 6 FEATURE CARDS GRID matching Reference Image 2 Top-Middle */}
        <section className="space-y-8">
          <div className="text-center space-y-2 max-w-2xl mx-auto">
            <h2 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">Core Platform Capabilities</h2>
            <p className="text-base text-slate-600 font-medium">Everything required for clinical decision support and personalized care.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {featureCards.map((feat, idx) => {
              const Icon = feat.icon;
              return (
                <div
                  key={idx}
                  className={`p-8 rounded-3xl bg-white/95 backdrop-blur-md border border-slate-200/90 shadow-lg hover:shadow-2xl transition-all duration-500 space-y-5 border-t-4 ${feat.borderColor} hover:-translate-y-2 group cursor-pointer`}
                >
                  <div className="flex items-center justify-between">
                    <div className={`p-4 rounded-2xl ${feat.bgColor} ${feat.iconColor} group-hover:scale-110 transition-transform`}>
                      <Icon className="w-7 h-7" />
                    </div>
                    <span className="px-3.5 py-1.5 rounded-full bg-slate-100 text-slate-800 text-xs font-extrabold">
                      {feat.tag}
                    </span>
                  </div>
                  <h3 className="text-xl font-black text-slate-900">{feat.title}</h3>
                  <p className="text-sm sm:text-base text-slate-600 leading-relaxed font-medium">
                    {feat.desc}
                  </p>
                </div>
              );
            })}
          </div>
        </section>

        {/* 4. EXPLAINABLE AI (XAI) SPOTLIGHT BANNER */}
        <section className="p-8 sm:p-12 rounded-3xl bg-slate-900 text-white shadow-2xl space-y-6">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 border-b border-slate-800 pb-6">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-purple-500/20 text-purple-300 text-xs font-bold border border-purple-500/40">
                <Eye className="w-4 h-4 text-purple-400" />
                <span>Explainable AI Engine</span>
              </div>
              <h3 className="text-2xl sm:text-3xl font-black">Transparent SHAP TreeExplainer Attributions</h3>
              <p className="text-base text-slate-300 font-medium max-w-xl">
                Every risk score comes with transparent feature importance attributions, so clinicians know exactly which biomarkers drove the inference.
              </p>
            </div>
            
            <button
              onClick={handleGetStarted}
              className="px-8 py-4 rounded-full bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 text-white font-extrabold text-sm sm:text-base shadow-lg hover:scale-105 transition-all shrink-0 flex items-center gap-2.5 cursor-pointer"
            >
              <span>Test XAI Engine</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 text-sm font-medium">
            <div className="p-5 rounded-2xl bg-slate-800/80 border border-slate-700/80 space-y-1.5">
              <span className="text-purple-400 font-extrabold block text-base">Biomarker Attributions</span>
              <p className="text-slate-300 leading-relaxed">Identifies top positive and negative risk contributors per patient.</p>
            </div>
            <div className="p-5 rounded-2xl bg-slate-800/80 border border-slate-700/80 space-y-1.5">
              <span className="text-blue-400 font-extrabold block text-base">No Black Boxes</span>
              <p className="text-slate-300 leading-relaxed">Physicians can audit underlying feature values against canonical thresholds.</p>
            </div>
            <div className="p-5 rounded-2xl bg-slate-800/80 border border-slate-700/80 space-y-1.5">
              <span className="text-emerald-400 font-extrabold block text-base">Platt-Scaled Probabilities</span>
              <p className="text-slate-300 leading-relaxed">Calibrated probabilities avoid overconfidence or extreme predictions.</p>
            </div>
          </div>
        </section>

        {/* 5. BOTTOM CTA BANNER matching Reference Image 2 Top-Middle */}
        <div className="p-8 sm:p-12 rounded-3xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-2xl flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="space-y-2 text-center sm:text-left">
            <h3 className="text-2xl sm:text-3xl font-black tracking-tight">Built for the future of healthcare.</h3>
            <p className="text-base text-blue-100 font-medium">Designed for doctors, researchers and innovators.</p>
          </div>
          <button
            onClick={handleGetStarted}
            className="px-8 py-4 rounded-full bg-white text-blue-700 hover:bg-blue-50 font-extrabold text-sm sm:text-base shadow-xl hover:scale-105 transition-all shrink-0 flex items-center gap-2.5 cursor-pointer"
          >
            <span>Get Started</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>

      </main>
    </PublicCanvasLayout>
  );
}
