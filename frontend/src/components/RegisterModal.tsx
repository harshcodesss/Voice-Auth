"use client";

import { useState, useRef } from "react";
import { registerSpeaker } from "@/lib/api";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import styles from "./RegisterModal.module.css";

interface RegisterModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export default function RegisterModal({ onClose, onSuccess }: RegisterModalProps) {
  const [speakerName, setSpeakerName] = useState("");
  const [samples, setSamples] = useState<{ blob: Blob; name: string }[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const recorder = useAudioRecorder();

  const addRecordedSample = () => {
    if (recorder.audioBlob) {
      setSamples((prev) => [
        ...prev,
        { blob: recorder.audioBlob!, name: `recording_${prev.length + 1}.webm` },
      ]);
      recorder.resetRecording();
    }
  };

  const addFileSamples = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const newSamples = files.map((f) => ({ blob: f, name: f.name }));
    setSamples((prev) => [...prev, ...newSamples]);
    e.target.value = "";
  };

  const removeSample = (idx: number) => {
    setSamples((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleSubmit = async () => {
    if (!speakerName.trim()) {
      setError("Please enter a speaker name");
      return;
    }
    if (samples.length === 0) {
      setError("Please add at least one audio sample");
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      await registerSpeaker(
        speakerName.trim(),
        samples.map((s) => s.blob)
      );
      setSuccess(true);
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatDuration = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        {success ? (
          <div className={styles.successState}>
            <span className={styles.successIcon}>✅</span>
            <h3>Speaker Registered!</h3>
            <p className={styles.successText}>
              <strong>{speakerName}</strong> has been added with {samples.length} sample(s)
            </p>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className={styles.header}>
              <h2 className={styles.title}>Register New Speaker</h2>
              <button className={styles.closeBtn} onClick={onClose}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>

            {/* Name input */}
            <div className={styles.field}>
              <label className={styles.label}>Speaker Name</label>
              <input
                className="input"
                type="text"
                placeholder="e.g. Harsh, Speaker_01"
                value={speakerName}
                onChange={(e) => setSpeakerName(e.target.value)}
                disabled={isSubmitting}
              />
            </div>

            {/* Audio samples */}
            <div className={styles.field}>
              <label className={styles.label}>
                Voice Samples ({samples.length} added)
              </label>

              {/* Sample list */}
              {samples.length > 0 && (
                <div className={styles.sampleList}>
                  {samples.map((s, i) => (
                    <div key={i} className={styles.sampleItem}>
                      <span className={styles.sampleName}>🎵 {s.name}</span>
                      <button
                        className={styles.removeBtn}
                        onClick={() => removeSample(i)}
                        disabled={isSubmitting}
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Record section */}
              <div className={styles.addMethods}>
                <div className={styles.recordSection}>
                  {!recorder.isRecording && !recorder.audioBlob && (
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={recorder.startRecording}
                      disabled={isSubmitting}
                    >
                      🎤 Record Sample
                    </button>
                  )}

                  {recorder.isRecording && (
                    <div className={styles.miniRecorder}>
                      <span className={styles.recordingDot} />
                      <span>{formatDuration(recorder.duration)}</span>
                      <button className="btn btn-danger btn-sm" onClick={recorder.stopRecording}>
                        Stop
                      </button>
                    </div>
                  )}

                  {recorder.audioBlob && !recorder.isRecording && (
                    <div className={styles.miniRecorder}>
                      <audio src={recorder.audioUrl!} controls className={styles.miniPlayer} />
                      <button className="btn btn-success btn-sm" onClick={addRecordedSample}>
                        Add
                      </button>
                      <button className="btn btn-secondary btn-sm" onClick={recorder.resetRecording}>
                        Discard
                      </button>
                    </div>
                  )}
                </div>

                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isSubmitting}
                >
                  📁 Upload Files
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".wav,.mp3,.flac,.ogg,.m4a,.webm"
                  multiple
                  onChange={addFileSamples}
                  style={{ display: "none" }}
                />
              </div>
            </div>

            {/* Error */}
            {error && <div className={styles.error}>{error}</div>}

            {/* Actions */}
            <div className={styles.actions}>
              <button className="btn btn-secondary" onClick={onClose} disabled={isSubmitting}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={handleSubmit} disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <span className="spinner" />
                    Registering…
                  </>
                ) : (
                  "Register Speaker"
                )}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
