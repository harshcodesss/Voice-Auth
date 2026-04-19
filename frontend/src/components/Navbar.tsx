"use client";

import Link from "next/link";
import styles from "./Navbar.module.css";

export default function Navbar() {
  return (
    <nav className={`${styles.nav} glass`}>
      <div className={`${styles.inner} container`}>
        <Link href="/" className={styles.logo}>
          <span className={styles.logoIcon}>🎙️</span>
          <span className={styles.logoText}>VoiceAuth</span>
        </Link>

        <div className={styles.links}>
          <Link href="/analyze" className={styles.link}>
            Analyze
          </Link>
          <Link href="/analyze" className="btn btn-primary btn-sm">
            Get Started
          </Link>
        </div>
      </div>
    </nav>
  );
}
