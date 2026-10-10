"""
Geospatial Radio Environment Map (REM) & Drive-Test Heatmap Generator.
Ports interactive Leaflet / Folium heatmap mapping from RFA-Gemini into RF-monitor-tool.

Features:
- Queries survey records from SQLite (rf_surveys.db).
- Resolves spatial coordinates (explicit lat/lon or campus site presets for KLS VDIT Haliyal).
- Omits unmapped records; requires valid coordinates before export.
- Generates publication-ready interactive Leaflet/Folium HTML maps.
- Weighted HeatMap layer based on RF Exposure Index / Peak Carrier Power.
- Rich interactive marker pins with HTML-escaped popup values and JS-encoded tooltips.
"""

import os
import json
import math
import html
import sqlite3
import logging
from typing import List, Dict, Any, Optional, Tuple
import folium
from folium.plugins import HeatMap

logger = logging.getLogger(__name__)

# Standard campus & survey location coordinates for KLS VDIT Haliyal
DEFAULT_SITE_COORDINATES: Dict[str, Tuple[float, float]] = {
    "ECE Communication Lab": (15.3348, 74.7570),
    "VDIT Main Entrance":     (15.3352, 74.7562),
    "Central Library":        (15.3342, 74.7578),
    "Mechanical Workshop":    (15.3338, 74.7566),
    "Admin Block Quadrangle": (15.3345, 74.7568),
    "Student Hostel Block":   (15.3360, 74.7585),
    "Campus Sports Field":    (15.3332, 74.7580),
    "Default Lab":            (15.3348, 74.7570),
}


def _is_valid_coord(lat: float, lon: float) -> bool:
    """Validates finite coordinates within standard Earth lat/lon ranges."""
    try:
        return (
            math.isfinite(lat) and math.isfinite(lon)
            and -90.0 <= lat <= 90.0
            and -180.0 <= lon <= 180.0
        )
    except (TypeError, ValueError):
        return False


def _encode_js_template_literal(text: str) -> str:
    """Encodes strings for JavaScript template-literal contexts."""
    return text.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')


def _format_safe_text(val: Any) -> str:
    """Escapes text as HTML and encodes template-literal characters for Folium JS contexts."""
    escaped_html = html.escape(str(val))
    return _encode_js_template_literal(escaped_html)


class RadioEnvironmentMapGenerator:
    """
    Generates interactive Leaflet / Folium Radio Environment Maps (REM)
    from SQLite survey records.
    """

    def __init__(self, db_path: str = "data/rf_surveys.db"):
        self.db_path = db_path

    def _resolve_coordinates(self, location_id: str, notes: str) -> Optional[Tuple[float, float]]:
        """
        Resolves GPS coordinates from notes or site presets.
        Returns None for unmapped or invalid records so they are omitted from spatial layers.
        """
        # 1. Check if coordinates are formatted as JSON or "lat,lon" in notes
        if notes:
            try:
                if "{" in notes and "}" in notes:
                    parsed = json.loads(notes)
                    if "lat" in parsed and "lon" in parsed:
                        lat, lon = float(parsed["lat"]), float(parsed["lon"])
                        if _is_valid_coord(lat, lon):
                            return lat, lon
                        return None
                if "," in notes:
                    parts = notes.split(",")
                    if len(parts) >= 2:
                        lat, lon = float(parts[0].strip()), float(parts[1].strip())
                        if _is_valid_coord(lat, lon):
                            return lat, lon
                        return None
            except Exception:
                pass

        # 2. Check site coordinate presets
        if location_id in DEFAULT_SITE_COORDINATES:
            lat, lon = DEFAULT_SITE_COORDINATES[location_id]
            if _is_valid_coord(lat, lon):
                return lat, lon

        # 3. Stop generating coordinates for unknown sites: return unmapped result
        return None

    def fetch_survey_records(self, limit: int = 500) -> List[Dict[str, Any]]:
        """Queries recent survey records from SQLite database."""
        if not os.path.exists(self.db_path):
            return []

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, timestamp, location_id, center_freq_mhz, peak_power_dbfs,
                       peak_freq_mhz, avg_power_dbfs, noise_floor_dbfs, dominant_band,
                       exposure_score, exposure_tier, active_carriers_count, notes
                FROM survey_logs
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def generate_map(
        self,
        output_html_path: str = "data/radio_environment_map.html",
        records: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Builds the interactive Folium HTML map with HeatMap overlay and detail pins.
        Omits records without coordinates, and reports that valid coordinates are required before export.
        Returns the absolute path to the generated HTML file.
        """
        if records is None:
            records = self.fetch_survey_records()

        # Filter for records with valid resolved coordinates
        mapped_records: List[Tuple[Dict[str, Any], Tuple[float, float]]] = []
        for r in records:
            coords = self._resolve_coordinates(r.get("location_id", ""), r.get("notes", ""))
            if coords is not None:
                mapped_records.append((r, coords))

        if not mapped_records:
            msg = "No valid coordinates found in survey records. Valid coordinates are required before export."
            logger.warning(msg)
            raise ValueError(msg)

        # Center map dynamically around active survey locations
        lats = [c[0] for _, c in mapped_records]
        lons = [c[1] for _, c in mapped_records]
        map_center = [float(sum(lats) / len(lats)), float(sum(lons) / len(lons))]

        rem_map = folium.Map(
            location=map_center,
            zoom_start=17,
            tiles="OpenStreetMap",
            control_scale=True,
        )

        heat_points = []
        for r, (lat, lon) in mapped_records:
            score = float(r.get("exposure_score", 10))
            weight = max(0.2, min(1.0, score / 100.0))
            heat_points.append([lat, lon, weight])

            # Marker color by safety tier
            tier = str(r.get("exposure_tier", "LOW")).upper()
            if "HIGH" in tier or "ELEVATED" in tier:
                marker_color = "red"
            elif "MEDIUM" in tier or "MODERATE" in tier:
                marker_color = "orange"
            else:
                marker_color = "green"

            # Escape popup fields for HTML and encode for Folium JS template-literal context
            loc_escaped = _format_safe_text(r.get("location_id", "Site"))
            ts_escaped = _format_safe_text(r.get("timestamp", "N/A"))
            band_escaped = _format_safe_text(r.get("dominant_band", "N/A"))
            tier_escaped = _format_safe_text(tier)

            popup_html = f"""
            <div style="font-family: Arial, sans-serif; font-size: 12px; width: 230px; line-height: 1.5;">
                <h4 style="margin: 0 0 6px 0; color: #1565c0; font-size: 14px;">📡 {loc_escaped}</h4>
                <div style="background: #f5f5f5; padding: 6px; border-radius: 4px; margin-bottom: 6px;">
                    <b>Timestamp:</b> {ts_escaped}<br/>
                    <b>Dominant Band:</b> {band_escaped}<br/>
                    <b>Peak Carrier:</b> {float(r.get('peak_freq_mhz', 0.0)):.2f} MHz ({float(r.get('peak_power_dbfs', 0.0)):.1f} dBFS)<br/>
                    <b>Total Channel:</b> {float(r.get('avg_power_dbfs', 0.0)):.1f} dBFS<br/>
                    <b>Active Carriers:</b> {int(r.get('active_carriers_count', 0))}
                </div>
                <div style="font-weight: bold; color: {'#c62828' if marker_color == 'red' else '#2e7d32'};">
                    Exposure Score: {score:.0f} / 100 ({tier_escaped})
                </div>
            </div>
            """

            # Escape tooltip_raw as HTML before passing to _encode_js_template_literal
            tooltip_raw = f"{r.get('location_id', 'Site')}: {score:.0f} ({tier})"
            tooltip_encoded = _encode_js_template_literal(html.escape(tooltip_raw))

            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=tooltip_encoded,
                icon=folium.Icon(color=marker_color, icon="signal", prefix="fa")
            ).add_to(rem_map)

        if heat_points:
            HeatMap(
                heat_points,
                radius=25,
                blur=18,
                max_zoom=18,
                gradient={0.2: "blue", 0.4: "cyan", 0.6: "lime", 0.8: "yellow", 1.0: "red"}
            ).add_to(rem_map)

        os.makedirs(os.path.dirname(os.path.abspath(output_html_path)), exist_ok=True)
        rem_map.save(output_html_path)
        return os.path.abspath(output_html_path)
