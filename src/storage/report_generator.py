"""
Survey & Shielding Report Generator.
Produces professional, academic HTML and Markdown survey reports for KLS VDIT Haliyal.
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any, List

from src.storage.survey_database import SurveyDatabase


class ReportGenerator:
    """
    Builds comprehensive HTML and Markdown summary reports from survey and shielding database records.
    """

    def __init__(self, db: Optional[SurveyDatabase] = None):
        self.db = db or SurveyDatabase()

    def generate_html_report(self, filepath: str, title: str = "RF Survey & Shielding Analysis Report") -> str:
        """
        Compiles an HTML report file and writes it to `filepath`.
        Returns the absolute filepath of the generated report.
        """
        # Fetch stats & records
        overall_stats = self.db.get_survey_statistics()
        locations_summary = self.db.get_locations_summary()
        shielding_logs = self.db.get_recent_shielding_logs(limit=25)
        recent_surveys = self.db.get_recent_survey_logs(limit=30)

        gen_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build HTML content
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --bg: #0b0f19;
            --surface: #131b2e;
            --surface-border: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --primary: #0284c7;
            --primary-accent: #38bdf8;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }}
        @media print {{
            :root {{
                --bg: #ffffff;
                --surface: #f8fafc;
                --surface-border: #cbd5e1;
                --text-primary: #0f172a;
                --text-secondary: #475569;
                --primary: #0369a1;
            }}
            body {{
                background: white !important;
                color: black !important;
            }}
            .card {{
                box-shadow: none !important;
                border: 1px solid #cbd5e1 !important;
            }}
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text-primary);
            margin: 0;
            padding: 24px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}
        .header {{
            border-bottom: 2px solid var(--surface-border);
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        .inst-title {{
            font-size: 13px;
            font-weight: 700;
            color: var(--primary-accent);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 4px;
        }}
        .doc-title {{
            font-size: 24px;
            font-weight: 800;
            margin: 0 0 6px 0;
            color: var(--text-primary);
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 12px;
        }}
        .meta-item strong {{
            color: var(--text-primary);
        }}
        /* Executive Metrics Grid */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }}
        .metric-card {{
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }}
        .metric-title {{
            font-size: 11px;
            font-weight: 700;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }}
        .metric-val {{
            font-size: 26px;
            font-weight: 800;
            color: var(--primary-accent);
        }}
        .metric-sub {{
            font-size: 11px;
            color: var(--text-secondary);
            margin-top: 4px;
        }}
        /* Tables */
        h2 {{
            font-size: 17px;
            font-weight: 700;
            color: var(--text-primary);
            border-left: 4px solid var(--primary-accent);
            padding-left: 10px;
            margin: 32px 0 14px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 8px;
            overflow: hidden;
            font-size: 12px;
            margin-bottom: 24px;
        }}
        th {{
            background: #0f172a;
            color: var(--text-secondary);
            font-weight: 700;
            text-align: left;
            padding: 10px 12px;
            border-bottom: 1px solid var(--surface-border);
            text-transform: uppercase;
            font-size: 10px;
            letter-spacing: 0.5px;
        }}
        td {{
            padding: 8px 12px;
            border-bottom: 1px solid var(--surface-border);
            color: var(--text-primary);
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        tr:hover td {{
            background: rgba(255, 255, 255, 0.02);
        }}
        /* Badges */
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .badge-green {{
            background: rgba(16, 185, 129, 0.15);
            color: #10b981;
            border: 1px solid #10b981;
        }}
        .badge-amber {{
            background: rgba(245, 158, 11, 0.15);
            color: #f59e0b;
            border: 1px solid #f59e0b;
        }}
        .badge-red {{
            background: rgba(239, 68, 68, 0.15);
            color: #ef4444;
            border: 1px solid #ef4444;
        }}
        .badge-cyan {{
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid #38bdf8;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 16px;
            border-top: 1px solid var(--surface-border);
            font-size: 11px;
            color: var(--text-secondary);
            text-align: center;
        }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="inst-title">KLS Vishwanathrao Deshpande Institute of Technology, Haliyal &bull; Dept. of ECE</div>
        <h1 class="doc-title">{title}</h1>
        <div class="meta-grid">
            <div class="meta-item"><strong>Academic Year:</strong> 2026–2027</div>
            <div class="meta-item"><strong>Generated:</strong> {gen_time}</div>
            <div class="meta-item"><strong>Guides:</strong> Dr. Plasin Dias / Prof. Deepak Sharma</div>
            <div class="meta-item"><strong>Team:</strong> Basavaraj, Heena, Naveengouda, Sangeeta</div>
        </div>
    </div>

    <!-- Executive Metrics -->
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-title">Survey Records</div>
            <div class="metric-val">{overall_stats['total_entries']}</div>
            <div class="metric-sub">Captured snapshots</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Locations Tested</div>
            <div class="metric-val">{len(locations_summary)}</div>
            <div class="metric-sub">Survey sites</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Max Observed Peak</div>
            <div class="metric-val">{overall_stats['max_peak_dbfs']:.1f} <span style="font-size: 14px;">dBFS</span></div>
            <div class="metric-sub">Peak carrier intensity</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Dominant Band</div>
            <div class="metric-val" style="font-size: 18px; line-height: 1.4;">{overall_stats['dominant_band']}</div>
            <div class="metric-sub">Most active allocation</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Shielding Tests</div>
            <div class="metric-val">{len(shielding_logs)}</div>
            <div class="metric-sub">Material benchmarks</div>
        </div>
    </div>

    <!-- Spatial Location Exposure Table -->
    <h2>1. Multi-Location RF Ambient Survey Comparison</h2>
"""
        if locations_summary:
            html += """
    <table>
        <thead>
            <tr>
                <th>Location / Site Tag</th>
                <th>Sample Count</th>
                <th>Peak Level (dBFS)</th>
                <th>Mean Avg Power (dBFS)</th>
                <th>Dominant Band</th>
                <th>Exposure Tier</th>
                <th>Survey Interval</th>
            </tr>
        </thead>
        <tbody>
"""
            for loc in locations_summary:
                tier = loc["highest_tier"]
                badge_class = "badge-green" if tier == "Low" else ("badge-amber" if tier == "Medium" else "badge-red")
                html += f"""
            <tr>
                <td><strong>{loc['location_id']}</strong></td>
                <td>{loc['sample_count']}</td>
                <td>{loc['max_peak_dbfs']:.1f} dBFS</td>
                <td>{loc['avg_power_dbfs']:.1f} dBFS</td>
                <td><span class="badge badge-cyan">{loc['dominant_band']}</span></td>
                <td><span class="badge {badge_class}">{tier}</span></td>
                <td>{loc['first_seen']} &rarr; {loc['last_seen']}</td>
            </tr>
"""
            html += """
        </tbody>
    </table>
"""
        else:
            html += "<p style='color: var(--text-secondary);'>No survey records logged yet.</p>"

        # Shielding Benchmarks Table
        html += """
    <h2>2. Shielding Material Effectiveness Benchmarks (SE Analysis)</h2>
"""
        if shielding_logs:
            html += """
    <table>
        <thead>
            <tr>
                <th>Timestamp</th>
                <th>Material Description</th>
                <th>Center Freq</th>
                <th>Baseline P0</th>
                <th>Shielded P1</th>
                <th>SE Attenuation</th>
                <th>Power Blocked</th>
                <th>Ratio</th>
                <th>Rating</th>
            </tr>
        </thead>
        <tbody>
"""
            for sh in shielding_logs:
                rating = sh["rating"]
                r_badge = "badge-green" if "EXCELLENT" in rating or "GOOD" in rating else ("badge-amber" if "FAIR" in rating or "MODERATE" in rating else "badge-red")
                html += f"""
            <tr>
                <td>{sh['timestamp']}</td>
                <td><strong>{sh['material_name']}</strong></td>
                <td>{sh['center_freq_mhz']:.2f} MHz</td>
                <td>{sh['baseline_peak_dbfs']:.1f} dBFS</td>
                <td>{sh['live_peak_dbfs']:.1f} dBFS</td>
                <td><strong>+{sh['se_peak_db']:.1f} dB</strong></td>
                <td style="color: #10b981; font-weight: 700;">{sh['percentage_reduction']:.1f}%</td>
                <td>{sh['attenuation_ratio']:.1f}x</td>
                <td><span class="badge {r_badge}">{rating}</span></td>
            </tr>
"""
            html += """
        </tbody>
    </table>
"""
        else:
            html += "<p style='color: var(--text-secondary);'>No shielding benchmark tests logged yet.</p>"

        # Recent Log Samples
        html += """
    <h2>3. Recent Survey Measurements Timeline</h2>
"""
        if recent_surveys:
            html += """
    <table>
        <thead>
            <tr>
                <th>Timestamp</th>
                <th>Location</th>
                <th>Center (MHz)</th>
                <th>Peak Carrier</th>
                <th>Noise Floor</th>
                <th>Active Carriers</th>
                <th>Dominant Band</th>
                <th>Exposure</th>
            </tr>
        </thead>
        <tbody>
"""
            for s in recent_surveys:
                tier = s["exposure_tier"]
                badge_class = "badge-green" if tier == "Low" else ("badge-amber" if tier == "Medium" else "badge-red")
                html += f"""
            <tr>
                <td>{s['timestamp']}</td>
                <td>{s['location_id']}</td>
                <td>{s['center_freq_mhz']:.2f}</td>
                <td>{s['peak_freq_mhz']:.3f} MHz ({s['peak_power_dbfs']:.1f} dBFS)</td>
                <td>{s['noise_floor_dbfs']:.1f} dBFS</td>
                <td>{s['active_carriers_count']}</td>
                <td>{s['dominant_band']}</td>
                <td><span class="badge {badge_class}">{tier} ({s['exposure_score']}/100)</span></td>
            </tr>
"""
            html += """
        </tbody>
    </table>
"""
        else:
            html += "<p style='color: var(--text-secondary);'>No recent survey measurements recorded.</p>"

        # Footer & Reference
        html += """
    <div class="footer">
        <p>SDR-Based RF Noise Monitoring & Reduction Analyzer &bull; KLS VDIT Haliyal Dept. of Electronics & Communication Engineering</p>
        <p>Measurements referenced against Indian National Frequency Allocation Plan (NFAP 2022) & ICNIRP Public Radiation Guidelines</p>
    </div>
</div>
</body>
</html>
"""
        out_dir = os.path.dirname(filepath)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        return os.path.abspath(filepath)
