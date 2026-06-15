import { useState, useEffect, useRef, useCallback } from 'react';
import { streamCoverLetter } from '../api/applyApi';
import './CoverLetterModal.css';

export default function CoverLetterModal({ job, profile, onClose }) {
  const [text, setText] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const areaRef = useRef(null);

  const provider = profile?.llm_provider || 'ollama';
  const model = profile?.llm_model || 'qwen2.5:14b';

  const generate = useCallback(() => {
    setText('');
    setDone(false);
    setError('');
    setStreaming(true);
    streamCoverLetter(
      job,
      provider,
      model,
      (chunk) => {
        setText(prev => {
          const next = prev + chunk;
          if (next.startsWith('ERROR:')) {
            setError(next);
            setStreaming(false);
            setDone(false);
            return '';
          }
          return next;
        });
        if (areaRef.current) areaRef.current.scrollTop = areaRef.current.scrollHeight;
      },
      () => { setStreaming(false); setDone(true); },
      (err) => { setError(err); setStreaming(false); }
    );
  }, [job, provider, model]);

  useEffect(() => { generate(); }, [generate]);

  const copy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const providerLabel = { ollama: '🦙 Ollama', openai: '🤖 OpenAI', gemini: '💎 Gemini' }[provider] || provider;

  return (
    <div className="cl-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="cl-modal">
        <div className="cl-header">
          <div className="cl-title-group">
            <span className="cl-sparkle">✨</span>
            <div>
              <h3>AI Cover Letter</h3>
              <p className="cl-subtitle">
                {job.title} @ {job.company} &nbsp;·&nbsp; via {providerLabel} ({model})
              </p>
            </div>
          </div>
          <button className="cl-close" onClick={onClose}>×</button>
        </div>

        {error ? (
          <div className="cl-error">
            <span>⚠️</span>
            <p>{error}</p>
            <button onClick={generate}>Try again</button>
          </div>
        ) : (
          <>
            <div className="cl-body">
              <textarea
                ref={areaRef}
                className={`cl-textarea ${streaming ? 'streaming' : ''}`}
                value={text}
                onChange={e => setText(e.target.value)}
                rows={16}
                placeholder={streaming ? '' : 'Click Regenerate to generate a cover letter...'}
                readOnly={streaming}
              />
              {streaming && (
                <div className="cl-cursor-blink" />
              )}
            </div>

            <div className="cl-footer">
              <button className="cl-btn cl-btn-regen" onClick={generate} disabled={streaming}>
                {streaming ? '⏳ Generating…' : '🔄 Regenerate'}
              </button>
              <button className="cl-btn cl-btn-copy" onClick={copy} disabled={!done || !text}>
                {copied ? '✅ Copied!' : '📋 Copy'}
              </button>
              <button className="cl-btn cl-btn-close" onClick={onClose}>Close</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
