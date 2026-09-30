# Product Requirements Document (PRD)

## Project Name: SDR-Based RF Noise Monitoring and Reduction Analysis

---

## 1. Document Control & Metadata
* **Document Title:** Product Requirements Document (PRD) - SDR-Based RF Noise Monitoring and Reduction Analysis
* **Academic Year / Phase:** 2026–2027
* **Institution:** KLS Vishwanathrao Deshpande Institute of Technology (VDIT), Haliyal
* **Department:** Electronics & Communication Engineering
* **Project Guide:** Dr. Plasin Dias / Prof. Deepak Sharma
* **Project Team:**
  - Basavaraj Agasimani (2VD23EC022)
  - Heena A Attar (2VD23EC033)
  - Naveengouda Bevinamarad (2VD23EC053)
  - Sangeeta Y Hondad (2VD23EC085)
* **Status:** Approved for Implementation

---

## 2. Executive Summary & Problem Definition

### 2.1 Problem Statement
Ubiquitous wireless communication infrastructure—such as cellular mobile base stations (GSM/LTE/5G), Wi-Fi access points, and radio/television broadcast networks—has contributed to significant RF signal saturation in residential, industrial, and educational environments. While concerns exist regarding prolonged ambient RF exposure and RF interference (RFI) with sensitive electronic equipment, monitoring tools remain out of reach:
* **Cost Constraints:** High-end commercial RF spectrum analyzers and calibrated field-strength meters cost thousands of dollars, making them impractical for community surveys, educational institutions, or distributed continuous deployment.
* **Complexity & Portability:** Conventional equipment is bulky, requiring specialized operation and manual record-keeping.
* **Lack of Shielding Verification Tools:** There are limited accessible workflows for users to quantify the attenuation efficiency of local shielding solutions.

### 2.2 Solution Overview
The **SDR-Based RF Noise Monitoring and Reduction Analysis System** provides an open-source, affordable, and flexible solution using Software Defined Radio (RTL-SDR). It digitizes analog RF signals across multiple frequency bands, analyzes them using Fast Fourier Transform (FFT), assigns a normalized **RF Exposure Index**, categorizes dominant signal bands (FM, GSM, Wi-Fi), and evaluates real-time shielding attenuation using accessible barrier materials.

---

## 3. Product Goals & Target Audience

### 3.1 Product Goals
1. **Low-Cost Spectrum Acquisition:** Utilize off-the-shelf RTL-SDR dongles to scan wide frequency bands without proprietary RF hardware.
2. **Real-Time Processing & UI:** Perform FFT calculations and display dynamic frequency spectrum and waterfall plots.
3. **Band Classification:** Reliably classify detected signals into established standard allocations (e.g., FM broadcast, GSM, ISM/Wi-Fi).
4. **Exposure Tiering:** Calculate a composite RF Exposure Index to present RF levels in simple terms: **Low**, **Medium**, or **High**.
5. **Shielding Attenuation Analysis:** Provide a measurement method to calculate attenuation ($dB$) across materials such as aluminum foil, metal mesh, and plastic.
6. **Data Logging:** Store location-tagged and timestamped spectral metrics for spatial RF surveys.

### 3.2 Target Audience
* **ECE Students & Researchers:** Practical testbed for digital signal processing (DSP), modulation detection, and wireless propagation.
* **Lab Administrators & Facilities Teams:** Quick evaluation of RF ambient noise floors and shielding integrity around sensitive laboratory instruments.
* **Environmental & Occupational Observers:** Assessment of baseline wireless radiation in classrooms, living quarters, and server rooms.

---

## 4. System Architecture & Flow

### 4.1 High-Level Architecture
```
  [ Ambient RF Environment ]
              │
              ▼
   +──────────────────────+
   |  Antenna Subsystem   |
   +──────────┬───────────+
              │ RF Analog Signals
              ▼
   +──────────────────────+
   |   RTL-SDR Receiver   | (Downconversion, Gain Control, 8-bit ADC)
   +──────────┬───────────+
              │ Digital I/Q Samples (USB Interface)
              ▼
   +────────────────────────────────────────────────────────+
   |                  Software / DSP Core                   |
   |                                                        |
   |  1. Fast Fourier Transform (FFT) Windowing & Scaling   |
   |  2. Spectral Feature Extraction (Power, Peaks, BW)     |
   |  3. Band Classifier (FM, GSM, Wi-Fi, Unknown)          |
   |  4. RF Exposure Index Computation                      |
   |  5. Shielding Attenuation Differential Engine          |
   +──────────┬───────────────────────────────┬─────────────+
              │                               │
              ▼                               ▼
   +──────────────────────+       +─────────────────────────+
   | Visualization Engine |       |   Data Logging Module   |
   | - Live Spectrum Plot |       | - CSV / SQLite Storage  |
   | - Waterfall Heatmap  |       | - Timestamp & Site Tags |
   | - (Opt) OLED Display |       +─────────────────────────+
   +──────────────────────+
```

### 4.2 System Workflow
1. **Acquisition:** The wideband antenna captures ambient electromagnetic waves; the RTL-SDR digitizes samples within the configured center frequency and sample rate.
2. **Frequency-Domain Transformation:** Python backend reads complex I/Q buffers and applies an FFT with windowing functions (e.g., Hann or Blackman) to produce power spectral density (PSD).
3. **Feature Extraction:** Peak detection algorithms extract absolute signal power ($dBm$ / $dBFS$), center frequencies, and bandwidth.
4. **Classification & Scoring:** The system maps detected peaks to frequency lookups (FM: 88–108 MHz, GSM 900: 890–960 MHz, etc.) and evaluates overall RF exposure.
5. **Attenuation Comparison:** When operating in "Shielding Mode," the system records two states ($P_{\text{unshielded}}$ and $P_{\text{shielded}}$) to calculate:
   $$\text{Attenuation (dB)} = P_{\text{unshielded}} - P_{\text{shielded}}$$
6. **Logging & Presentation:** The results are rendered to the desktop GUI / web dashboard and stored for multi-location comparison.

---

## 5. Functional Requirements (FR)

| Requirement ID | Module | Description | Priority |
| :--- | :--- | :--- | :--- |
| **FR-01** | Hardware Interface | Connect to RTL-SDR via USB and configure gain, sampling rate ($\le 2.4\text{ MS/s}$ typical), and tuner center frequency. | P0 |
| **FR-02** | FFT Processing Engine | Calculate discrete Fourier transforms on buffered blocks with selectable FFT sizes ($512$, $1024$, $2048$, $4096$). | P0 |
| **FR-03** | Feature Extraction | Extract peak power amplitude, estimate noise floor, and calculate 3dB / 10dB occupied channel bandwidth. | P0 |
| **FR-04** | RF Classification | Categorize active signals by cross-referencing peak frequencies with regulatory allocations (e.g., FM, GSM 900/1800, ISM 433/868 MHz). | P1 |
| **FR-05** | RF Exposure Index | Compute aggregate channel power and classify exposure status into **Low**, **Medium**, or **High** using preset threshold boundaries. | P1 |
| **FR-06** | Shielding Evaluation Mode | Dual-pass workflow that records baseline power, then prompts for shield installation, calculates attenuation in $dB$, and reports efficiency percentage. | P1 |
| **FR-07** | Spectrum & Waterfall GUI | Display real-time dynamic Power vs. Frequency plot and scrolling waterfall display with customizable color ramps. | P1 |
| **FR-08** | Persistent Data Logging | Save records to `.csv` or database, including fields: `Timestamp`, `Location_ID`, `Frequency_Range`, `Peak_Power`, `Avg_Power`, `Dominant_Band`, `Exposure_Index`. | P2 |
| **FR-09** | Parameter Adjustment | Allow dynamic in-flight changes to gain, center frequency, averaging count, and detection thresholds without restarting the program. | P2 |
| **FR-10** | OLED Compact Display (Optional) | Export summary metrics (Band, Exposure Index, Peak dB) over I2C/SPI to a small display (e.g., SSD1306) for headless setups. | P3 |

---

## 6. Non-Functional Requirements (NFR)

* **Performance & Frame Rate:** Real-time spectrum visualization must sustain $\ge 15\text{ FPS}$ on a modern multi-core PC without buffer dropouts or overflow.
* **Usability:** The interface should allow switching between basic monitoring mode and shielding comparison mode with one click.
* **Accuracy:** Spectral peak identification must have an accuracy within the frequency resolution dictated by the FFT bin size:
  $$\Delta f = \frac{f_s}{N_{\text{FFT}}}$$
* **Portability:** The entire physical setup (SDR dongle, whip antenna, connecting cables, and shield box) must weigh under 1 kg and fit in a standard laptop bag.
* **Cost Effectiveness:** Total system BOM cost (excluding the host computing device) must remain below $50 USD.

---

## 7. Hardware & Software Specifications

### 7.1 Hardware Components
* **SDR Receiver:** RTL2832U-based tuner (e.g., R820T2 / RTL-SDR Blog V3/V4).
* **Antenna:** Telescopic dipole antenna with SMA connector.
* **Host Platform:** Laptop / Desktop PC (minimum dual-core CPU, 4 GB RAM, USB 2.0+ port).
* **Test Shields:** Aluminum foil, copper mesh / wire gauze, plastic enclosure, metallic enclosures.
* **Cabling:** SMA-to-MCX/SMA jumper cables, shielded USB extension cables.

### 7.2 Software & Toolchain
* **Primary Programming Language:** Python 3.9+
* **SDR Drivers & APIs:** `librtlsdr`, `pyrtlsdr`, GNU Radio (optional advanced flowgraph backend)
* **DSP & Numeric Processing:** `NumPy`, `SciPy` (signal processing & peak detection)
* **Data Storage & Analytics:** `Pandas`
* **Plotting & Visualization:** `Matplotlib`, `Plotly`, or `PyQtGraph` (for high-rate UI rendering)
* **IDE / Environment:** VS Code, Jupyter Notebook

---

## 8. Shielding Analysis & Measurement Methodology

To ensure reproducible shielding effectiveness (SE) measurements:
1. **Calibration:** Set SDR tuner to a fixed manual gain to prevent Automatic Gain Control (AGC) from altering received signal levels between passes.
2. **Baseline Reference ($P_0$):** Position the receiver antenna inside the unshielded test enclosure; capture 100 frames across target center frequencies; record mean peak power $P_0\text{ (dBm/dBFS)}$.
3. **Shielded Measurement ($P_1$):** Seal the enclosure with the target shielding material (aluminum foil, metal mesh, conductive fabric, plastic sheet); capture 100 frames under identical RF conditions; record mean power $P_1\text{ (dBm/dBFS)}$.
4. **Metric Formulation:**
   $$\text{Shielding Effectiveness (SE)} = P_0 - P_1 \quad (\text{in dB})$$
   $$\text{Attenuation Ratio} = 10^{\frac{\text{SE}}{10}}$$
5. **Material Classification:** Automatically log the material label, thickness, continuity/grounding state, and resulting SE rating.

---

## 9. Verification & Acceptance Criteria

| Area | Test Condition | Expected Acceptance Standard |
| :--- | :--- | :--- |
| **SDR Connectivity** | Hot-plug and driver initialization | Device recognized within 3 seconds; continuous I/Q stream established without dropouts. |
| **Band Identification** | Exposure to FM transmission (88–108 MHz) and GSM (900 MHz) | Correct classification label assigned in $\ge 95\%$ of sample tests. |
| **Shielding Attenuation** | Enclosing antenna with multi-layer aluminum foil | Detectable drop of $\ge 20\text{ dB}$ on strong broadcast carriers compared to open baseline. |
| **Exposure Index** | Operation in low-noise room vs. proximity to active cellular call | Clear transition from **Low** to **High** category on the RF Exposure Index. |
| **Continuous Operation** | 2-hour continuous spectrum capture and logging | Memory usage remains stable; no unhandled buffer exceptions or memory leaks. |

---

## 10. Future Scope & Roadmap

* **Phase 1 (Current):** RTL-SDR integration, basic FFT UI, threshold-based Exposure Index, manual shielding comparison tool.
* **Phase 2:** Automated frequency sweeping across wide spans ($24\text{ MHz} - 1.7\text{ GHz}$) using stepped LO re-tuning algorithms.
* **Phase 3:** Integration of machine learning models for automatic modulation recognition (AMR) and anomaly detection.
* **Phase 4:** Cloud synchronization pipeline for distributed, crowd-sourced RF heatmapping and geospatial exposure monitoring.