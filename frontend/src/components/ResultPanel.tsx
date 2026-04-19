"use client";

import type { AnalyzeResponse } from "@/types/api";
import styles from "./ResultPanel.module.css";

interface ResultPanelProps {
  result: AnalyzeResponse;
  onRegisterUnknown: () => void;
}

export default function ResultPanel({ result, onRegisterUnknown }: ResultPanelProps) {
  const similarityPct = Math.round(result.similarity * 100);

  return (
    <div className={`${styles.panel} animate-in`}>
      {/* Header */}
      <div className={styles.header}>
        <h3 className={styles.title}>Analysis Result</h3>
        <span className={result.is_known ? "badge badge-known" : "badge badge-unknown"}>
          {result.is_known ? "✓ Known" : "? Unknown"}
        </span>
      </div>

      {/* Main result */}
      <div className={styles.mainResult}>
        <div className={styles.speakerName}>
          {result.is_known ? (
            <span className={styles.speakerIcon}>🎤</span>
          ) : (
            <span className={styles.speakerIcon}>❓</span>
          )}
          <span>{result.final_speaker}</span>
        </div>

        {/* Similarity meter */}
        <div className={styles.meterWrapper}>
          <div className={styles.meterLabel}>
            <span>Similarity</span>
            <span className={styles.meterValue}>{similarityPct}%</span>
          </div>
          <div className={styles.meterTrack}>
            <div
              className={styles.meterFill}
              style={{
                width: `${similarityPct}%`,
                background: result.is_known
                  ? "linear-gradient(90deg, var(--success), #55efc4)"
                  : "linear-gradient(90deg, var(--warning), #ffeaa7)",
              }}
            />
          </div>
          <div className={styles.meterThreshold}>
            <span>Threshold: {Math.round(result.threshold_used * 100)}%</span>
          </div>
        </div>
      </div>

      {/* Meta info */}
      <div className={styles.meta}>
        <div className={styles.metaItem}>
          <span className={styles.metaLabel}>File</span>
          <span className={styles.metaValue}>{result.filename}</span>
        </div>
        <div className={styles.metaItem}>
          <span className={styles.metaLabel}>Duration</span>
          <span className={styles.metaValue}>{result.duration_sec}s</span>
        </div>
        <div className={styles.metaItem}>
          <span className={styles.metaLabel}>Chunks</span>
          <span className={styles.metaValue}>{result.num_chunks}</span>
        </div>
      </div>

      {/* Chunk predictions */}
      {result.chunks && result.chunks.length > 1 && (
        <div className={styles.chunks}>
          <h4 className={styles.chunksTitle}>Chunk Predictions</h4>
          <div className={styles.chunkList}>
            {result.chunks.map((chunk) => (
              <div key={chunk.chunk_index} className={styles.chunk}>
                <div className={styles.chunkTime}>
                  {chunk.start_sec.toFixed(1)}s – {chunk.end_sec.toFixed(1)}s
                </div>
                <div className={styles.chunkSpeaker}>
                  {chunk.speaker}
                </div>
                <div className={styles.chunkScore}>
                  <div className={styles.chunkMeter}>
                    <div
                      className={styles.chunkMeterFill}
                      style={{
                        width: `${Math.round(chunk.similarity * 100)}%`,
                        background: chunk.is_known ? "var(--success)" : "var(--warning)",
                      }}
                    />
                  </div>
                  <span className={styles.chunkPct}>
                    {Math.round(chunk.similarity * 100)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Register unknown */}
      {!result.is_known && (
        <div className={styles.unknownAction}>
          <p className={styles.unknownText}>
            This speaker is not in the database. Would you like to register them?
          </p>
          <button className="btn btn-primary" onClick={onRegisterUnknown}>
            Register Speaker
          </button>
        </div>
      )}
    </div>
  );
}
