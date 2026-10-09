"""
Survey Database Module for SDR-Based RF Noise Monitoring and Reduction Analysis.
Provides SQLite storage, indexing, spatial location queries, and CSV export (FR-08).
"""

import os
import sqlite3
import threading
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime


DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "rf_surveys.db",
)


class SurveyDatabase:
    """
    Thread-safe SQLite database manager for RF surveys and shielding effectiveness tests.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=10.0)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for high concurrency & reliability
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self):
        """Initializes tables and indices if they do not exist."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                # 1. Survey Logs Table (FR-08: Timestamp, Location_ID, Frequency_Range, Peak_Power, Avg_Power, Dominant_Band, Exposure_Index)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS survey_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        location_id TEXT NOT NULL,
                        center_freq_mhz REAL NOT NULL,
                        sample_rate_msps REAL NOT NULL,
                        freq_start_mhz REAL NOT NULL,
                        freq_end_mhz REAL NOT NULL,
                        peak_power_dbfs REAL NOT NULL,
                        peak_freq_mhz REAL NOT NULL,
                        avg_power_dbfs REAL NOT NULL,
                        noise_floor_dbfs REAL NOT NULL,
                        dominant_band TEXT NOT NULL,
                        exposure_score INTEGER NOT NULL,
                        exposure_tier TEXT NOT NULL,
                        active_carriers_count INTEGER NOT NULL,
                        notes TEXT DEFAULT ''
                    );
                """)

                # 2. Shielding Logs Table (PRD Section 8: Material, Thickness, Baseline P0, Shielded P1, SE dB, Reduction %, Rating)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS shielding_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        material_name TEXT NOT NULL,
                        baseline_peak_dbfs REAL NOT NULL,
                        live_peak_dbfs REAL NOT NULL,
                        se_peak_db REAL NOT NULL,
                        percentage_reduction REAL NOT NULL,
                        attenuation_ratio REAL NOT NULL,
                        rating TEXT NOT NULL,
                        center_freq_mhz REAL NOT NULL,
                        notes TEXT DEFAULT ''
                    );
                """)

                # Indices for fast lookups & timeline queries
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_survey_time ON survey_logs(timestamp);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_survey_loc ON survey_logs(location_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_shielding_mat ON shielding_logs(material_name);")
                conn.commit()
            finally:
                conn.close()

    def insert_survey_log(self, record: Dict[str, Any]) -> int:
        """
        Inserts a single spectral survey record.
        Returns the newly created row ID.
        """
        query = """
            INSERT INTO survey_logs (
                timestamp, location_id, center_freq_mhz, sample_rate_msps,
                freq_start_mhz, freq_end_mhz, peak_power_dbfs, peak_freq_mhz,
                avg_power_dbfs, noise_floor_dbfs, dominant_band, exposure_score,
                exposure_tier, active_carriers_count, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            record.get("timestamp", datetime.now().isoformat(timespec="seconds")),
            record.get("location_id", "Default Lab"),
            float(record.get("center_freq_mhz", 100.0)),
            float(record.get("sample_rate_msps", 2.4)),
            float(record.get("freq_start_mhz", 98.8)),
            float(record.get("freq_end_mhz", 101.2)),
            float(record.get("peak_power_dbfs", -50.0)),
            float(record.get("peak_freq_mhz", 100.0)),
            float(record.get("avg_power_dbfs", -70.0)),
            float(record.get("noise_floor_dbfs", -75.0)),
            str(record.get("dominant_band", "Unknown")),
            int(record.get("exposure_score", 0)),
            str(record.get("exposure_tier", "Low")),
            int(record.get("active_carriers_count", 0)),
            str(record.get("notes", "")),
        )

        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.lastrowid
            finally:
                conn.close()

    def insert_shielding_log(self, record: Dict[str, Any]) -> int:
        """
        Inserts a shielding effectiveness benchmark record.
        Returns the newly created row ID.
        """
        query = """
            INSERT INTO shielding_logs (
                timestamp, material_name, baseline_peak_dbfs, live_peak_dbfs,
                se_peak_db, percentage_reduction, attenuation_ratio, rating,
                center_freq_mhz, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            record.get("timestamp", datetime.now().isoformat(timespec="seconds")),
            str(record.get("material_name", "Aluminum Foil")),
            float(record.get("baseline_peak_dbfs", -30.0)),
            float(record.get("live_peak_dbfs", -55.0)),
            float(record.get("se_peak_db", 25.0)),
            float(record.get("percentage_reduction", 99.5)),
            float(record.get("attenuation_ratio", 316.2)),
            str(record.get("rating", "EXCELLENT SHIELDING")),
            float(record.get("center_freq_mhz", 100.0)),
            str(record.get("notes", "")),
        )

        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.lastrowid
            finally:
                conn.close()

    def get_recent_survey_logs(self, limit: int = 50, location_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves recent survey records ordered by newest first."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                if location_id:
                    cursor.execute(
                        "SELECT * FROM survey_logs WHERE location_id = ? ORDER BY id DESC LIMIT ?",
                        (location_id, limit),
                    )
                else:
                    cursor.execute("SELECT * FROM survey_logs ORDER BY id DESC LIMIT ?", (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            finally:
                conn.close()

    def get_recent_shielding_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent shielding effectiveness test records."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM shielding_logs ORDER BY id DESC LIMIT ?", (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            finally:
                conn.close()

    def get_survey_statistics(self, location_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculates summary statistics across survey entries."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                filter_clause = "WHERE location_id = ?" if location_id else ""
                params = (location_id,) if location_id else ()

                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total_entries,
                        MAX(peak_power_dbfs) as max_peak_dbfs,
                        AVG(avg_power_dbfs) as mean_avg_power_dbfs,
                        MIN(noise_floor_dbfs) as min_noise_floor_dbfs,
                        AVG(exposure_score) as avg_exposure_score
                    FROM survey_logs {filter_clause}
                """, params)
                stats_row = cursor.fetchone()

                # Dominant band frequency
                cursor.execute(f"""
                    SELECT dominant_band, COUNT(*) as cnt
                    FROM survey_logs {filter_clause}
                    GROUP BY dominant_band
                    ORDER BY cnt DESC LIMIT 1
                """, params)
                band_row = cursor.fetchone()
                dominant_band = band_row["dominant_band"] if band_row else "None"

                # Exposure tier counts
                cursor.execute(f"""
                    SELECT exposure_tier, COUNT(*) as cnt
                    FROM survey_logs {filter_clause}
                    GROUP BY exposure_tier
                """, params)
                tier_rows = cursor.fetchall()
                tier_counts = {r["exposure_tier"]: r["cnt"] for r in tier_rows}

                return {
                    "total_entries": stats_row["total_entries"] if stats_row else 0,
                    "max_peak_dbfs": stats_row["max_peak_dbfs"] if stats_row and stats_row["max_peak_dbfs"] is not None else -100.0,
                    "mean_avg_power_dbfs": stats_row["mean_avg_power_dbfs"] if stats_row and stats_row["mean_avg_power_dbfs"] is not None else -100.0,
                    "min_noise_floor_dbfs": stats_row["min_noise_floor_dbfs"] if stats_row and stats_row["min_noise_floor_dbfs"] is not None else -100.0,
                    "avg_exposure_score": stats_row["avg_exposure_score"] if stats_row and stats_row["avg_exposure_score"] is not None else 0.0,
                    "dominant_band": dominant_band,
                    "tier_distribution": tier_counts,
                }
            finally:
                conn.close()

    def get_locations_summary(self) -> List[Dict[str, Any]]:
        """Returns per-location aggregated metrics for spatial comparison."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        location_id,
                        COUNT(*) as sample_count,
                        MAX(peak_power_dbfs) as max_peak_dbfs,
                        AVG(avg_power_dbfs) as avg_power_dbfs,
                        AVG(exposure_score) as avg_score,
                        MIN(timestamp) as first_seen,
                        MAX(timestamp) as last_seen
                    FROM survey_logs
                    GROUP BY location_id
                    ORDER BY max_peak_dbfs DESC
                """)
                rows = cursor.fetchall()

                results = []
                for row in rows:
                    loc = row["location_id"]
                    # Get dominant band for this location
                    cursor.execute("""
                        SELECT dominant_band, COUNT(*) as cnt
                        FROM survey_logs
                        WHERE location_id = ?
                        GROUP BY dominant_band
                        ORDER BY cnt DESC LIMIT 1
                    """, (loc,))
                    top_band = cursor.fetchone()
                    band_str = top_band["dominant_band"] if top_band else "Unknown"

                    # Get highest exposure tier
                    cursor.execute("""
                        SELECT exposure_tier, COUNT(*) as cnt
                        FROM survey_logs
                        WHERE location_id = ?
                        GROUP BY exposure_tier
                        ORDER BY 
                            CASE exposure_tier 
                                WHEN 'High' THEN 1 
                                WHEN 'Medium' THEN 2 
                                ELSE 3 
                            END ASC LIMIT 1
                    """, (loc,))
                    top_tier = cursor.fetchone()
                    tier_str = top_tier["exposure_tier"] if top_tier else "Low"

                    results.append({
                        "location_id": loc,
                        "sample_count": row["sample_count"],
                        "max_peak_dbfs": row["max_peak_dbfs"],
                        "avg_power_dbfs": row["avg_power_dbfs"],
                        "avg_score": row["avg_score"],
                        "dominant_band": band_str,
                        "highest_tier": tier_str,
                        "first_seen": row["first_seen"],
                        "last_seen": row["last_seen"],
                    })
                return results
            finally:
                conn.close()

    def export_survey_to_csv(self, filepath: str, location_id: Optional[str] = None) -> int:
        """
        Exports survey entries to a standard CSV file (FR-08).
        Returns the number of exported rows.
        """
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                if location_id:
                    cursor.execute("SELECT * FROM survey_logs WHERE location_id = ? ORDER BY id ASC", (location_id,))
                else:
                    cursor.execute("SELECT * FROM survey_logs ORDER BY id ASC")
                rows = cursor.fetchall()
                if not rows:
                    # Write header anyway
                    fieldnames = [
                        "id", "timestamp", "location_id", "center_freq_mhz", "sample_rate_msps",
                        "freq_start_mhz", "freq_end_mhz", "peak_power_dbfs", "peak_freq_mhz",
                        "avg_power_dbfs", "noise_floor_dbfs", "dominant_band", "exposure_score",
                        "exposure_tier", "active_carriers_count", "notes"
                    ]
                    with open(filepath, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(fieldnames)
                    return 0

                fieldnames = [k for k in rows[0].keys()]
                with open(filepath, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(fieldnames)
                    for row in rows:
                        writer.writerow([row[k] for k in fieldnames])
                return len(rows)
            finally:
                conn.close()

    def export_shielding_to_csv(self, filepath: str) -> int:
        """Exports shielding effectiveness records to CSV. Returns row count."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM shielding_logs ORDER BY id ASC")
                rows = cursor.fetchall()
                if not rows:
                    fieldnames = [
                        "id", "timestamp", "material_name", "baseline_peak_dbfs", "live_peak_dbfs",
                        "se_peak_db", "percentage_reduction", "attenuation_ratio", "rating",
                        "center_freq_mhz", "notes"
                    ]
                    with open(filepath, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(fieldnames)
                    return 0

                fieldnames = [k for k in rows[0].keys()]
                with open(filepath, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(fieldnames)
                    for row in rows:
                        writer.writerow([row[k] for k in fieldnames])
                return len(rows)
            finally:
                conn.close()

    def clear_survey_logs(self, location_id: Optional[str] = None):
        """Clears all or location-specific survey records."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                if location_id:
                    cursor.execute("DELETE FROM survey_logs WHERE location_id = ?", (location_id,))
                else:
                    cursor.execute("DELETE FROM survey_logs")
                conn.commit()
            finally:
                conn.close()

    def clear_shielding_logs(self):
        """Clears all shielding evaluation records."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM shielding_logs")
                conn.commit()
            finally:
                conn.close()
