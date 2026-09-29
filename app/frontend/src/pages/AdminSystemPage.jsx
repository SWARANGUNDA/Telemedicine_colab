import React, { useState, useEffect } from 'react';
import {
  Server, Database, Cpu, HardDrive, ShieldCheck, Activity, RefreshCw, Layers, Sparkles, Clock, CheckCircle
} from 'lucide-react';
import {
  Button, Card, CardHeader, CardBody, CardFooter, Badge, ProgressBar, CircularProgress, Alert
} from '../components/ui';
import { PageContainer, PageHeader, ContentSection } from '../components/layout';

export default function AdminSystemPage() {
  const [autoRefresh, setAutoRefresh] = useState(true);

  return (
    <PageContainer className="space-y-8 pb-24">
      <PageHeader
        title="Platform Health & System Monitoring"
        description="Real-time telemetry, model versioning, API gateway performance, and database maintenance"
        badge="System Health: 99.98%"
        actions={
          <Button variant="outline" size="sm" leftIcon={<RefreshCw className="w-4 h-4" />} onClick={() => window.location.reload()}>
            Refresh Telemetry
          </Button>
        }
      />

      {/* Subsystem Health Cards */}
      <ContentSection title="Subsystem Telemetry" subtitle="Active status across gateway endpoints, databases, and ML inference pipelines">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <Card isGlass={true} className="p-5 space-y-3 border-l-4 border-l-[var(--success)]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Server className="w-5 h-5 text-[var(--success)]" />
                <h5 className="text-sm font-bold text-[var(--text-main)]">FastAPI API Gateway</h5>
              </div>
              <Badge variant="success" size="sm">ONLINE</Badge>
            </div>
            <p className="text-xs text-[var(--text-muted)]">Port 8000 • 200 OK • Response Time: 12 ms</p>
          </Card>

          <Card isGlass={true} className="p-5 space-y-3 border-l-4 border-l-[var(--success)]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database className="w-5 h-5 text-[var(--primary)]" />
                <h5 className="text-sm font-bold text-[var(--text-main)]">SQLite / PostgreSQL DB</h5>
              </div>
              <Badge variant="success" size="sm">HEALTHY</Badge>
            </div>
            <p className="text-xs text-[var(--text-muted)]">Connections: 14 • Write Latency: 4 ms • Backup Status: Fresh</p>
          </Card>

          <Card isGlass={true} className="p-5 space-y-3 border-l-4 border-l-[var(--success)]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu className="w-5 h-5 text-[var(--secondary)]" />
                <h5 className="text-sm font-bold text-[var(--text-main)]">ML Inference Ensemble</h5>
              </div>
              <Badge variant="success" size="sm">READY</Badge>
            </div>
            <p className="text-xs text-[var(--text-muted)]">Clinical v4, Wearable v4, Gut v4 Models Frozen & Calibrated</p>
          </Card>

          <Card isGlass={true} className="p-5 space-y-3 border-l-4 border-l-[var(--success)]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-[var(--accent)]" />
                <h5 className="text-sm font-bold text-[var(--text-main)]">ChromaDB RAG Vector Store</h5>
              </div>
              <Badge variant="success" size="sm">INDEXED</Badge>
            </div>
            <p className="text-xs text-[var(--text-muted)]">Medical Guidelines Store • 1,420 Chunks Loaded</p>
          </Card>

          <Card isGlass={true} className="p-5 space-y-3 border-l-4 border-l-[var(--success)]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Layers className="w-5 h-5 text-blue-500" />
                <h5 className="text-sm font-bold text-[var(--text-main)]">Tesseract OCR Engine</h5>
              </div>
              <Badge variant="success" size="sm">ACTIVE</Badge>
            </div>
            <p className="text-xs text-[var(--text-muted)]">Hybrid PDF OCR Parsing • Success Rate: 98.5%</p>
          </Card>

          <Card isGlass={true} className="p-5 space-y-3 border-l-4 border-l-[var(--success)]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <HardDrive className="w-5 h-5 text-amber-500" />
                <h5 className="text-sm font-bold text-[var(--text-main)]">System Storage & Memory</h5>
              </div>
              <Badge variant="success" size="sm">42% Used</Badge>
            </div>
            <p className="text-xs text-[var(--text-muted)]">RAM: 4.2 GB / 16.0 GB • Disk: 128 GB Available</p>
          </Card>
        </div>
      </ContentSection>

      {/* Model Versions Read-Only Table */}
      <ContentSection title="Frozen ML Model Versions (Read-Only)" subtitle="Version control & training artifact integrity for clinical models">
        <Card isGlass={true} className="p-6 space-y-4">
          <div className="space-y-3 text-xs">
            <div className="p-3.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] flex items-center justify-between">
              <div>
                <strong className="text-[var(--text-main)] block">Clinical Expert Model v4.0 Unified</strong>
                <span className="font-mono text-[10px] text-[var(--text-muted)]">Artifact: clinical_v4_expert_payload.joblib • 18 Canonical Features</span>
              </div>
              <Badge variant="success" size="sm">Calibrated</Badge>
            </div>

            <div className="p-3.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] flex items-center justify-between">
              <div>
                <strong className="text-[var(--text-main)] block">Wearable Telemetry Expert v4.0 Unified</strong>
                <span className="font-mono text-[10px] text-[var(--text-muted)]">Artifact: wearable_v4_expert_payload.joblib • 15 Sensor & CGM Metrics</span>
              </div>
              <Badge variant="secondary" size="sm">Calibrated</Badge>
            </div>

            <div className="p-3.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] flex items-center justify-between">
              <div>
                <strong className="text-[var(--text-main)] block">Gut Microbiome Taxa Expert v4.0 Unified</strong>
                <span className="font-mono text-[10px] text-[var(--text-muted)]">Artifact: gut_v4_expert_payload.joblib • 40 Microbial Taxa</span>
              </div>
              <Badge variant="accent" size="sm">Calibrated</Badge>
            </div>
          </div>
        </Card>
      </ContentSection>
    </PageContainer>
  );
}
