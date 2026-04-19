"use client";

import { useRef, useState } from "react";
import styles from "./AudioInput.module.css";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";

interface AudioInputProps {
  onAudioReady: (blob: Blob, name: string) => void;
  disabled?: boolean;
}

export default function AudioInput({ onAudioReady, disabled }: AudioInputProps) {
  const recorder = useAudioRecorder();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      recorder.resetRecording();
      onAudioReady(file, file.name);
    }
  };

  const handleStopAndSubmit = () => {
    recorder.stopRecording();
    // The blob will be available after a short delay due to MediaRecorder async nature
    setTimeout(() => {
      if (recorder.audioBlob) {
        onAudioReady(recorder.audioBlob, "recording.webm");
      }
    }, 300);
  };

  const formatDuration = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  // If recording just finished and blob is available, auto-submit
  const handleUseRecording = () => {
    if (recorder.audioBlob) {
      onAudioReady(recorder.audioBlob, "recording.webm");
    }
  };

  return (
    <div className={styles.wrapper}>
      {/* Recorder card */}
      <div className={`${styles.card} card`}>
        <div className={styles.cardHeader}>
          <span className={styles.cardIcon}>🎤</span>
          <h3 className={styles.cardTitle}>Record Audio</h3>
        </div>
        <p className={styles.cardDesc}>
          Use your microphone to record a voice sample
        </p>

        {recorder.error && (
          <div className={styles.error}>{recorder.error}</div>
        )}

        <div className={styles.recorderControls}>
          {!recorder.isRecording && !recorder.audioBlob && (
            <button
              className="btn btn-primary"
              onClick={recorder.startRecording}
              disabled={disabled}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/></svg>
              Start Recording
            </button>
          )}

          {recorder.isRecording && (
            <div className={styles.recordingState}>
              <div className={styles.recordingIndicator}>
                <span className={styles.recordingDot} />
                <span className={styles.recordingTime}>
                  {formatDuration(recorder.duration)}
                </span>
              </div>
              <button
                className="btn btn-danger"
                onClick={handleStopAndSubmit}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>
                Stop
              </button>
            </div>
          )}

          {recorder.audioBlob && !recorder.isRecording && (
            <div className={styles.recordingDone}>
              <audio src={recorder.audioUrl!} controls className={styles.audioPlayer} />
              <div className={styles.recordingActions}>
                <button className="btn btn-primary btn-sm" onClick={handleUseRecording}>
                  Use Recording
                </button>
                <button className="btn btn-secondary btn-sm" onClick={recorder.resetRecording}>
                  Re-record
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Divider */}
      <div className={styles.divider}>
        <span className={styles.dividerText}>or</span>
      </div>

      {/* Upload card */}
      <div className={`${styles.card} card`}>
        <div className={styles.cardHeader}>
          <span className={styles.cardIcon}>📁</span>
          <h3 className={styles.cardTitle}>Upload File</h3>
        </div>
        <p className={styles.cardDesc}>
          Upload a .wav, .mp3, .flac, or .webm audio file
        </p>

        <div
          className={styles.dropzone}
          onClick={() => !disabled && fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
        >
          <svg className={styles.uploadIcon} width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          {uploadedFile ? (
            <span className={styles.fileName}>{uploadedFile.name}</span>
          ) : (
            <span className={styles.dropText}>Click to browse files</span>
          )}
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".wav,.mp3,.flac,.ogg,.m4a,.webm"
          onChange={handleFileChange}
          className={styles.fileInput}
          disabled={disabled}
        />
      </div>
    </div>
  );
}
