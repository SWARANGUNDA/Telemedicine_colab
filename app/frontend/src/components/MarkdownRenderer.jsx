import React from 'react';
import { BookOpen } from 'lucide-react';

export default function MarkdownRenderer({ text, content, evidenceList, onCitationClick }) {
  const markdownText = text || content;
  if (!markdownText) return null;

  // Helper to parse inline bolding (**text**) and citation tags ([REF_X])
  const parseInlineElements = (inlineText) => {
    if (!inlineText) return null;

    // First split by REF tags e.g. [REF_1]
    const refParts = inlineText.split(/(\[REF_\d+\])/g);

    return refParts.map((part, rIdx) => {
      const refMatch = part.match(/\[(REF_\d+)\]/);
      if (refMatch) {
        const refId = refMatch[1];
        return (
          <button
            key={`ref-${rIdx}`}
            className="citation-tag"
            onClick={() => onCitationClick && onCitationClick(refId, evidenceList)}
            title="Click to view verified source metadata"
            type="button"
          >
            <BookOpen size={10} /> [{refId}]
          </button>
        );
      }

      // Parse bolding **text** within text parts
      const boldParts = part.split(/(\*\*[^*]+\*\*)/g);
      return boldParts.map((bPart, bIdx) => {
        if (bPart.startsWith('**') && bPart.endsWith('**')) {
          const boldContent = bPart.slice(2, -2);
          return <strong key={`b-${bIdx}`} style={{ color: 'var(--text-main)' }}>{boldContent}</strong>;
        }
        return bPart;
      });
    });
  };

  const lines = markdownText.split('\n');
  const elements = [];

  lines.forEach((line, idx) => {
    const trimmed = line.trim();
    if (!trimmed) return;

    // Skip orphan citation lines or empty bullets
    if (trimmed === '-' || trimmed === '•' || /^[-•]\s*\[REF_\d+\]$/.test(trimmed)) {
      return;
    }

    // Headings
    if (trimmed.startsWith('# ')) {
      elements.push(
        <h1 key={idx} style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-main)', marginTop: '20px', marginBottom: '12px' }}>
          {parseInlineElements(trimmed.replace('# ', ''))}
        </h1>
      );
      return;
    }
    if (trimmed.startsWith('## ')) {
      elements.push(
        <h2 key={idx} style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--accent-cyan)', marginTop: '18px', marginBottom: '10px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '6px' }}>
          {parseInlineElements(trimmed.replace('## ', ''))}
        </h2>
      );
      return;
    }
    if (trimmed.startsWith('### ')) {
      elements.push(
        <h3 key={idx} style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '14px', marginBottom: '8px' }}>
          {parseInlineElements(trimmed.replace('### ', ''))}
        </h3>
      );
      return;
    }

    // Bullet Lists
    if (trimmed.startsWith('- ') || trimmed.startsWith('• ')) {
      const listContent = trimmed.replace(/^[-•]\s*/, '');
      elements.push(
        <li key={idx} style={{ marginLeft: '20px', marginBottom: '8px', color: 'var(--text-main)', lineHeight: 1.6 }}>
          {parseInlineElements(listContent)}
        </li>
      );
      return;
    }

    // Standard Paragraphs
    elements.push(
      <p key={idx} style={{ marginBottom: '10px', color: 'var(--text-main)', lineHeight: 1.6 }}>
        {parseInlineElements(trimmed)}
      </p>
    );
  });

  return <div>{elements}</div>;
}
