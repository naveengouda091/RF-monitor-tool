"""
Verification Script: Geospatial Radio Environment Map (REM) Generation.
Verifies spatial database record extraction, coordinate resolution, HTML escaping, and Folium Leaflet HTML generation
using an isolated temporary database and temporary output map.
"""

import sys
import os
import time
import tempfile
import shutil

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.storage.survey_database import SurveyDatabase
from src.storage.rem_map_generator import RadioEnvironmentMapGenerator, DEFAULT_SITE_COORDINATES


def run_rem_verification():
    print("=" * 70)
    print("  VERIFICATION SUITE: GEOSPATIAL RADIO ENVIRONMENT MAP (REM)")
    print("=" * 70)

    temp_dir = tempfile.mkdtemp(prefix="rf_rem_test_")
    temp_db_path = os.path.join(temp_dir, "test_rf_surveys.db")
    temp_map_path = os.path.join(temp_dir, "test_radio_environment_map.html")

    try:
        db = SurveyDatabase(db_path=temp_db_path)

        # -------------------------------------------------------------
        # PART 1: Populating Multi-Site Spatial RF Survey Records
        # -------------------------------------------------------------
        print("\n--- [PART 1] Populating Multi-Site Spatial RF Survey Records (Isolated) ---")
        test_sites = [
            ("ECE Communication Lab", 98.3, -28.5, 78, "Elevated (Caution)", 4, None),
            ("VDIT Main Entrance", 935.2, -45.0, 42, "Moderate (Warning)", 6, None),
            ("Central Library", 100.0, -62.0, 18, "Safe Ambient (Low)", 2, None),
            ("Student Hostel Block", 865.4, -38.0, 56, "Moderate (Warning)", 3, None),
            ("Campus Sports Field", 108.5, -68.0, 12, "Safe Ambient (Low)", 1, None),
            # Explicit lat/lon in notes with HTML markup & template literal characters
            ("Custom <Tag> & '${injection}'", 433.92, -50.0, 35, "Safe Ambient (Low)", 1, "15.3350, 74.7575"),
            # Unknown unmapped site (must be omitted from map)
            ("Unknown Site Without Coords", 100.0, -50.0, 20, "Safe Ambient (Low)", 1, ""),
        ]

        for site_name, freq_mhz, peak_pwr, score, tier, carriers, notes_coord in test_sites:
            notes = notes_coord if notes_coord else f"Spatial REM Survey Point for {site_name}"
            db.insert_survey_log({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "location_id": site_name,
                "center_freq_mhz": freq_mhz,
                "sample_rate_msps": 2.048,
                "freq_start_mhz": freq_mhz - 1.0,
                "freq_end_mhz": freq_mhz + 1.0,
                "peak_power_dbfs": peak_pwr,
                "peak_freq_mhz": freq_mhz,
                "avg_power_dbfs": peak_pwr - 10.0,
                "noise_floor_dbfs": -85.0,
                "dominant_band": "Cellular / Broadcast",
                "exposure_score": score,
                "exposure_tier": tier,
                "active_carriers_count": carriers,
                "notes": notes
            })
        print(f"  [+] Inserted {len(test_sites)} records into temporary database: {temp_db_path}")

        # -------------------------------------------------------------
        # PART 2: Generating Folium / Leaflet Interactive Heatmap
        # -------------------------------------------------------------
        print("\n--- [PART 2] Generating Folium / Leaflet Interactive Heatmap ---")
        rem_gen = RadioEnvironmentMapGenerator(db_path=temp_db_path)
        res_path = rem_gen.generate_map(output_html_path=temp_map_path)

        print(f"  Generated Map Path : {res_path}")
        assert os.path.exists(res_path), "Radio Environment Map HTML file must be created."
        file_size_kb = os.path.getsize(res_path) / 1024.0
        print(f"  File Size          : {file_size_kb:.1f} KB")

        with open(res_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        assert "leaflet" in html_content.lower(), "Map HTML must contain Leaflet library assets."
        assert "heat" in html_content.lower(), "Map HTML must contain HeatMap layer."

        # Check standard preset sites
        for site_name, _, _, _, _, _, _ in test_sites[:5]:
            assert site_name in html_content, f"Map HTML must contain marker for mapped {site_name}."

        # Check HTML escaping & JS template-literal encoding
        assert "&lt;Tag&gt;" in html_content, "Markup in location_id must be escaped as HTML in popup and tooltip."
        assert "\\${injection}" in html_content, "Template literal interpolation '${' must be escaped."
        print("  [PASS] HTML escaping and JS template-literal encoding validated on special characters.")

        # Verify that unmapped site without coordinates is omitted
        assert "Unknown Site Without Coords" not in html_content, \
            "Unmapped site without coordinates must be omitted from spatial layers."
        print("  [PASS] Unmapped site properly omitted from map.")

        # -------------------------------------------------------------
        # PART 3: Verification of Required Coordinates Validation
        # -------------------------------------------------------------
        print("\n--- [PART 3] Verifying Rejection When Zero Valid Coordinates Exist ---")
        empty_gen = RadioEnvironmentMapGenerator(db_path=temp_db_path)
        unmapped_records = [{
            "location_id": "Ghost Site",
            "notes": "No GPS here",
            "exposure_score": 50,
            "exposure_tier": "MEDIUM"
        }]
        rejected = False
        try:
            empty_gen.generate_map(
                output_html_path=os.path.join(temp_dir, "should_fail.html"),
                records=unmapped_records
            )
        except ValueError as err:
            rejected = True
            print(f"  [PASS] Correctly rejected export when no valid coordinates exist: '{err}'")
        assert rejected, "Export must be rejected when no valid coordinates exist."

        print("\n" + "=" * 70)
        print("  GEOSPATIAL REM MAP VERIFICATION COMPLETE: ALL TESTS PASSED")
        print("=" * 70)
        return True

    finally:
        # Clean up temporary artifacts
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
            print("  [+] Temporary test artifacts cleaned up successfully.")


if __name__ == "__main__":
    success = run_rem_verification()
    sys.exit(0 if success else 1)
