"use client";

import { useState, useCallback } from "react";
import AudioInput from "@/components/AudioInput";
import ResultPanel from "@/components/ResultPanel";
import RegisterModal from "@/components/RegisterModal";
import { analyzeAudio } from "@/lib/api";
import type { AnalyzeResponse } from "@/types/api";
import styles from "./page.module.css";

type PageState = "idle" | "ready" | "analyzing" | "done" | "error";

export default function AnalyzePage() {
  const [state, setState] = useState<PageState>("idle");
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioName, setAudioName] = useState("");
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showRegister, setShowRegister] = useState(false);

  const handleAudioReady = useCallback((blob: Blob, name: string) => {
    setAudioBlob(blob);
    setAudioName(name);
    setState("ready");
    setResult(null);
    setError(null);
  }, []);

  const handleAnalyze = async () => {
    if (!audioBlob) return;

    setState("analyzing");
    setError(null);

    try {
      const res = await analyzeAudio(audioBlob);
      setResult(res);
      setState("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed. Is the backend running?");
      setState("error");
    }
  };

  const handleReset = () => {
    setState("idle");
    setAudioBlob(null);
    setAudioName("");
    setResult(null);
    setError(null);
  };

  return (
    <div className={styles.page}>
      <div className={`${styles.content} container`}>
        {/* Page header */}
        <div className={styles.header}>
          <h1 className={styles.title}>Analyze Audio</h1>
          <p className={styles.subtitle}>
            Record or upload Hindi audio to identify the speaker
          </p>
        </div>

        {/* Audio input */}
        <AudioInput
          onAudioReady={handleAudioReady}
          disabled={state === "analyzing"}
        />

        {/* Action bar */}
        {state !== "idle" && (
          <div className={`${styles.actionBar} animate-in`}>
            <div className={styles.selectedFile}>
              <span className={styles.fileIcon}>🎵</span>
              <span className={styles.fileName}>{audioName}</span>
            </div>
            <div className={styles.actionButtons}>
              <button
                className="btn btn-secondary btn-sm"
                onClick={handleReset}
                disabled={state === "analyzing"}
              >
                Clear
              </button>
              <button
                className="btn btn-primary"
                onClick={handleAnalyze}
                disabled={state === "analyzing"}
              >
                {state === "analyzing" ? (
                  <>
                    <span className="spinner" />
                    Analyzing…
                  </>
                ) : (
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <polygon points="5 3 19 12 5 21 5 3"/>
                    </svg>
                    Analyze
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Loading state */}
        {state === "analyzing" && (
          <div className={`${styles.loadingCard} card animate-in`}>
            <div className={styles.loadingContent}>
              <div className={styles.loadingSpinner} />
              <div>
                <h3 className={styles.loadingTitle}>Analyzing audio…</h3>
                <p className={styles.loadingDesc}>
                  Extracting embeddings and comparing with registered speakers
                </p>
              </div>
            </div>
            <div className={styles.loadingSteps}>
              <span className={styles.loadingStep}>Splitting into chunks…</span>
              <span className={styles.loadingStep}>Extracting ECAPA embeddings…</span>
              <span className={styles.loadingStep}>Computing similarity…</span>
            </div>
          </div>
        )}

        {/* Error state */}
        {state === "error" && error && (
          <div className={`${styles.errorCard} animate-in`}>
            <span className={styles.errorIcon}>⚠️</span>
            <div>
              <h3 className={styles.errorTitle}>Analysis Failed</h3>
              <p className={styles.errorDesc}>{error}</p>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={handleAnalyze}>
              Retry
            </button>
          </div>
        )}

        {/* Results */}
        {state === "done" && result && (
          <ResultPanel
            result={result}
            onRegisterUnknown={() => setShowRegister(true)}
          />
        )}
      </div>

      {/* Register modal */}
      {showRegister && (
        <RegisterModal
          onClose={() => setShowRegister(false)}
          onSuccess={() => {
            setShowRegister(false);
          }}
        />
      )}
    </div>
  );
}
