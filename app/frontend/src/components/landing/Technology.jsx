import React from 'react';
import { Card, Badge } from '../ui';
import { Code2, Cpu, Database, Server, Layers } from 'lucide-react';

export default function Technology() {
  const techStack = [
    {
      name: 'React 18',
      desc: 'Modern component-driven UI architecture',
      tooltip: 'React 18 with concurrent rendering and automatic batching',
      category: 'Frontend',
      icon: Code2,
    },
    {
      name: 'FastAPI',
      desc: 'Asynchronous Python microservice framework',
      tooltip: 'FastAPI async REST endpoints with automatic OpenAPI schemas',
      category: 'Backend',
      icon: Server,
    },
    {
      name: 'Python 3.11',
      desc: 'Core machine learning & data processing engine',
      tooltip: 'High-performance Python 3.11 runtime for ML pipelines',
      category: 'Language',
      icon: Code2,
    },
    {
      name: 'XGBoost & LightGBM',
      desc: 'Gradient boosted tree ensembles for disease risk',
      tooltip: 'Optimized gradient boosted decision trees for clinical tabular data',
      category: 'ML Models',
      icon: Cpu,
    },
    {
      name: 'TreeSHAP',
      desc: 'Game-theoretic local feature attribution explainer',
      tooltip: 'Exact Shapley additive attributions for gradient boosted tree models',
      category: 'XAI Engine',
      icon: Cpu,
    },
    {
      name: 'PostgreSQL / SQLite',
      desc: 'Relational database for patient & consultation state',
      tooltip: 'ACID-compliant relational database storage for patient audit logs',
      category: 'Database',
      icon: Database,
    },
    {
      name: 'ChromaDB RAG',
      desc: 'Vector embedding database for medical guidelines',
      tooltip: 'Vector similarity search over clinical practice guideline embeddings',
      category: 'Knowledge Base',
      icon: Database,
    },
  ];

  return (
    <section className="py-24 bg-[var(--bg-primary)] border-b border-[var(--border-subtle)] space-y-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center max-w-3xl mx-auto space-y-3">
          <Badge variant="accent" size="sm">ENTERPRISE TECH STACK</Badge>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[var(--text-main)] tracking-tight">
            Powered by Modern Technologies
          </h2>
          <p className="text-base text-[var(--text-muted)] font-normal">
            Built using industry-standard open-source machine learning frameworks and web infrastructure.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {techStack.map((tech, idx) => {
            const Icon = tech.icon;
            return (
              <div key={idx} title={tech.tooltip} className="group">
                <Card isGlass={true} className="p-6 space-y-3 hover:border-[var(--primary)] hover:-translate-y-1 transition-all duration-200 shadow-md">
                  <div className="flex items-center justify-between">
                    <div className="p-2.5 rounded-xl bg-[var(--primary-light)] text-[var(--primary)] group-hover:scale-110 transition-transform">
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase tracking-wider font-semibold">{tech.category}</span>
                  </div>
                  <h3 className="text-base font-bold text-[var(--text-main)] group-hover:text-[var(--primary)] transition-colors">{tech.name}</h3>
                  <p className="text-xs text-[var(--text-muted)] leading-relaxed">{tech.desc}</p>
                </Card>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
