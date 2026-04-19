import Link from "next/link";
import styles from "./page.module.css";

const features = [
  {
    icon: "🎯",
    title: "Speaker Identification",
    desc: "Identify registered speakers from Hindi audio using deep learning embeddings and cosine similarity.",
  },
  {
    icon: "❓",
    title: "Unknown Detection",
    desc: "Automatically detect unregistered voices. No forced classification — only confident matches.",
  },
  {
    icon: "📝",
    title: "Speaker Registration",
    desc: "Register new speakers with multiple voice samples. The system averages embeddings for robust matching.",
  },
  {
    icon: "🔊",
    title: "Chunk Analysis",
    desc: "Long audio files are split into chunks. Each chunk is analyzed independently and results are aggregated.",
  },
];

const techStack = [
  { name: "SpeechBrain", detail: "ECAPA-TDNN embeddings" },
  { name: "Cosine Similarity", detail: "Embedding comparison" },
  { name: "FastAPI", detail: "Python backend" },
  { name: "Next.js", detail: "React frontend" },
];

export default function LandingPage() {
  return (
    <div className={styles.page}>
      {/* Hero */}
      <section className={styles.hero}>
        <div className={`${styles.heroInner} container`}>
          <div className={styles.heroBadge}>
            <span className={styles.heroBadgeDot} />
            Lab Project — Speaker Recognition
          </div>

          <h1 className={styles.heroTitle}>
            Hindi Speaker
            <br />
            <span className={styles.heroAccent}>Recognition</span>
          </h1>

          <p className={styles.heroDesc}>
            AI-powered speaker identification for Hindi audio conversations.
            Register speakers, analyze recordings, and detect unknown voices
            using SpeechBrain ECAPA-TDNN deep embeddings.
          </p>

          <div className={styles.heroCta}>
            <Link href="/analyze" className="btn btn-primary btn-lg">
              Get Started
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
              </svg>
            </Link>
            <a href="#features" className="btn btn-secondary btn-lg">
              Learn More
            </a>
          </div>

          {/* Floating stats */}
          <div className={styles.stats}>
            {techStack.map((t) => (
              <div key={t.name} className={styles.stat}>
                <span className={styles.statName}>{t.name}</span>
                <span className={styles.statDetail}>{t.detail}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Hero background glow */}
        <div className={styles.heroGlow} />
      </section>

      {/* Features */}
      <section id="features" className={styles.features}>
        <div className="container">
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>How It Works</h2>
            <p className={styles.sectionDesc}>
              A complete pipeline from audio input to speaker identification
            </p>
          </div>

          <div className={styles.featureGrid}>
            {features.map((f) => (
              <div key={f.title} className={`${styles.featureCard} card`}>
                <span className={styles.featureIcon}>{f.icon}</span>
                <h3 className={styles.featureTitle}>{f.title}</h3>
                <p className={styles.featureDesc}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pipeline */}
      <section className={styles.pipeline}>
        <div className="container">
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>The Pipeline</h2>
            <p className={styles.sectionDesc}>
              Embedding-based approach — no SVM, no MFCC classifiers
            </p>
          </div>

          <div className={styles.pipelineSteps}>
            {[
              { step: "1", label: "Audio Input", desc: "Record or upload Hindi audio" },
              { step: "2", label: "Chunking", desc: "Split into 10-second segments" },
              { step: "3", label: "Embedding", desc: "Extract ECAPA-TDNN vectors" },
              { step: "4", label: "Matching", desc: "Cosine similarity comparison" },
              { step: "5", label: "Result", desc: "Identify speaker or mark Unknown" },
            ].map((s, i) => (
              <div key={s.step} className={styles.pipelineStep}>
                <div className={styles.stepNumber}>{s.step}</div>
                <h4 className={styles.stepLabel}>{s.label}</h4>
                <p className={styles.stepDesc}>{s.desc}</p>
                {i < 4 && <div className={styles.stepConnector} />}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className={styles.footer}>
        <div className="container">
          <p className={styles.footerText}>
            VoiceAuth — Hindi Speaker Recognition | Lab Project
          </p>
        </div>
      </footer>
    </div>
  );
}
