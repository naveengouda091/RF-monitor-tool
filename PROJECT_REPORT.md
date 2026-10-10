# COMPREHENSIVE PROJECT REPORT

# SDR-Based RF Noise Monitoring and Reduction Analysis

---

### **Department of Electronics & Communication Engineering**
### **KLS Vishwanathrao Deshpande Institute of Technology (VDIT)**
*(Affiliated to Visvesvaraya Technological University, Belagavi | Approved by AICTE, New Delhi)*  
**Haliyal – 581 329, Uttara Kannada District, Karnataka, India**

---

### **Academic Year: 2026–2027**

**Project Title:** Software-Defined Radio (SDR) Based Ambient Radio Frequency Noise Monitoring, Signal Classification, and Reduction Analysis  
**Course:** Bachelor of Engineering (B.E.) Capstone Project  
**Internal Guides:**  
- **Dr. Plasin Dias**, Associate Professor, Dept. of ECE  
- **Prof. Deepak Sharma**, Assistant Professor, Dept. of ECE  

**Project Team Members:**
- **Basavaraj Agasimani** — University Seat Number (USN): `2VD23EC022`
- **Heena A Attar** — University Seat Number (USN): `2VD23EC033`
- **Naveengouda Bevinamarad** — University Seat Number (USN): `2VD23EC053`
- **Sangeeta Y Hondad** — University Seat Number (USN): `2VD23EC085`

---

## Certificate of Authenticity

This is to certify that the project entitled **"SDR-Based RF Noise Monitoring and Reduction Analysis"** is a bona fide record of work carried out by **Basavaraj Agasimani (2VD23EC022)**, **Heena A Attar (2VD23EC033)**, **Naveengouda Bevinamarad (2VD23EC053)**, and **Sangeeta Y Hondad (2VD23EC085)** in partial fulfillment of the requirements for the award of Bachelor of Engineering in Electronics & Communication Engineering during the academic year 2026–2027 at KLS Vishwanathrao Deshpande Institute of Technology, Haliyal.

---

## Executive Summary & Abstract

The proliferation of high-density wireless communication infrastructure—encompassing cellular mobile base transceiver stations (GSM/LTE/5G), ubiquitous Wi-Fi access points, low-power IoT transceivers, and high-power radio/television broadcast transmitters—has resulted in pervasive electromagnetic saturation across residential, educational, and laboratory environments. While increasing ambient radio frequency (RF) levels raise valid operational concerns regarding electromagnetic interference (EMI) with sensitive instrumentation and occupational human exposure, systematic monitoring remains largely unattainable due to the prohibitive capital cost ($3,000 to $15,000 USD) and mechanical bulk of commercial RF spectrum analyzers. Furthermore, accessible engineering tools capable of quantitatively verifying the attenuation performance of local electromagnetic shielding barriers in real time are virtually nonexistent.

To address these limitations, this project designs, implements, and benchmarks a low-cost, open-source, high-throughput **SDR-Based RF Noise Monitoring and Reduction Analysis System**. Utilizing an off-the-shelf RTL-SDR dongle (RTL2832U + R820T2) and an optimized Python digital signal processing (DSP) architecture, the system provides:
1. **Real-time spectrum analysis** sustaining $\ge 20\text{ FPS}$ with 2D scrolling waterfall spectrograms rendered via GPU-backed PyQtGraph.
2. **Automated regulatory band classification** conforming to the **Indian National Frequency Allocation Plan (NFAP 2022)** and ITU Region 3 standards.
3. **Automatic Modulation Classification (AMC)** based on 4th-order cumulants ($C_{40}, C_{42}$) and blind carrier frequency offset (CFO) compensation, discriminating BPSK, QPSK, 16-QAM, and Gaussian noise.
4. **Adaptive 1D Kalman filtering** and vectorized spectral Kalman smoothing, reducing RSSI measurement jitter variance by **11.7×** ($8.70\text{ dB}^2 \rightarrow 0.74\text{ dB}^2$) while adapting instantaneously to physical shielding steps ($|y| > 3\sigma$).
5. **A composite RF Exposure Index (0–100 scale)** categorizing environmental electromagnetic density into *Safe Ambient (Low)*, *Moderate (Warning)*, and *Elevated (Caution)* tiers referenced against ICNIRP guidelines.
6. **A dual-pass quantitative Shielding Effectiveness (SE)** differential engine that captures unshielded baseline power ($P_0$), live shielded power ($P_1$), computes attenuation ($dB$), calculates percentage power blocked, and classifies physical barriers.
7. **Thread-safe SQLite logging** (`rf_surveys.db`), CSV exports, interactive Leaflet/Folium **Radio Environment Maps (REM)**, and automated academic HTML/Print reporting.

Experimental results across the KLS VDIT Haliyal campus demonstrated clear spatial distinctions between quiet environments (Central Library: $-62.0\text{ dBFS}$, Exposure 18/100) and saturated zones (ECE Comm Lab: $-28.5\text{ dBFS}$, Exposure 78/100). Physical barrier benchmarks at 98.30 MHz demonstrated shielding effectiveness of **+9.80 dB** (89.53% blocked) for wire mesh, **+23.40 dB** (99.54% blocked) for dual-layer aluminum foil, and **+34.60 dB** (99.97% blocked) for a sealed steel enclosure. The total hardware bill-of-materials cost is under **$40 USD**, achieving over a 99% cost reduction compared to proprietary spectrum analyzers.

---

## Table of Contents

1. [Chapter 1: Introduction & Problem Formulation](#chapter-1-introduction--problem-formulation)
2. [Chapter 2: Theoretical Foundations & Mathematical Formulations](#chapter-2-theoretical-foundations--mathematical-formulations)
3. [Chapter 3: System Architecture & Design Specifications](#chapter-3-system-architecture--design-specifications)
4. [Chapter 4: Detailed Implementation of Core Modules](#chapter-4-detailed-implementation-of-core-modules)
5. [Chapter 5: Verification Protocols, Experimental Results & Benchmarks](#chapter-5-verification-protocols-experimental-results--benchmarks)
6. [Chapter 6: Practical Applications & Comparative Analysis](#chapter-6-practical-applications--comparative-analysis)
7. [Chapter 7: Conclusions & Future Scope](#chapter-7-conclusions--future-scope)
8. [Chapter 8: References & Appendices](#chapter-8-references--appendices)

---

## Chapter 1: Introduction & Problem Formulation

### 1.1 Background & Context
The radio frequency spectrum represents a finite, indispensable natural resource underpinning global communication, navigation, defense, and automation. Over the past two decades, wireless infrastructure density has experienced exponential growth. Cellular networks have progressed from narrowband 2G/GSM to wideband 4G/LTE and sub-6 GHz 5G MIMO deployments. Concurrently, 2.4 GHz and 5 GHz Wi-Fi access points, Bluetooth peripherals, and sub-GHz IoT networks (such as 865–867 MHz LoRa in India) operate continuously across indoor and outdoor spaces.

This relentless growth has created elevated ambient electromagnetic noise floors. Radio frequency noise encompasses unwanted or unintended radiated electromagnetic energy arising from carrier intermodulation, switching transients, power distribution lines, spurious digital harmonics, and saturated co-channel wireless transmissions. 

### 1.2 Problem Definition
Despite the ubiquity of RF saturation, ambient spectrum monitoring and shielding verification remain inaccessible due to three fundamental obstacles:

1. **Extreme Capital Cost Barriers:** Commercial benchtop or handheld calibrated spectrum analyzers manufactured by vendors such as Keysight Technologies, Rohde & Schwarz, Anritsu, or Tektronix cost between **$3,000 and $15,000 USD**. Calibrated isotropic field-strength radiation meters (e.g., Narda NBM-550) cost upwards of **$6,000 USD**. Such price points prohibit wide deployment in undergraduate engineering laboratories, academic classrooms, and distributed campus environmental surveys.
2. **Lack of Accessible Shielding Attenuation Workflows:** When laboratories, clinics, or testing facilities install local shielding materials (such as aluminum barriers, copper meshes, conductive fabrics, or Faraday boxes) to protect sensitive instruments, they lack an accessible, automated mechanism to empirically verify the material's attenuation efficiency ($dB$) in-situ.
3. **Data Logging and Spatial Representation Gaps:** Traditional spectrum analyzers operate as standalone instruments with closed display interfaces. Transferring spatial survey data, generating drive-test heatmaps, and creating standardized compliance reports requires proprietary software suites and cumbersome manual recording.

### 1.3 Project Objectives
The primary objective of this project is to architect, build, and experimentally validate a fully integrated, low-cost, open-source RF noise monitoring and reduction analysis system. Specifically:
- **Low-Cost Hardware Integration:** Interface an RTL-SDR Blog V3 receiver ($~35 USD) to continuously capture baseband complex I/Q samples from 24 MHz to 1.7 GHz with sampling rates up to 2.8 MS/s.
- **High-Throughput DSP Engine:** Implement a windowed Fast Fourier Transform (FFT) pipeline executing at $\ge 20\text{ FPS}$ with parametric noise floor estimation and multi-carrier peak prominence detection.
- **National Regulatory Mapping:** Construct an automatic carrier classifier aligned with the **Indian National Frequency Allocation Plan (NFAP 2022)** and ITU Region 3 spectrum allocations.
- **Automatic Modulation Recognition:** Implement higher-order statistical cumulants ($C_{40}, C_{42}$) and blind carrier frequency offset compensation to automatically classify received modulations.
- **Recursive State-Space Estimation:** Integrate a 1D adaptive Kalman filter and a vectorized spectral smoother to suppress measurement jitter while retaining rapid convergence to physical shielding steps.
- **Audience RF Exposure Scoring:** Formulate an intuitive composite RF Exposure Index (0–100) mapped to safety tiers according to ICNIRP public exposure recommendations.
- **Quantitative Shielding Analysis:** Build a dual-pass differential measurement engine ($SE = P_0 - P_1$) providing live attenuation curves, percentage power blocked, and material performance grading.
- **Spatial Survey Logging & Mapping:** Implement thread-safe SQLite storage, CSV exports, Leaflet/Folium Radio Environment Maps (REM), and automated academic HTML/Print reporting branded for KLS VDIT Haliyal.

### 1.4 Scope and Limitations
- **Frequency Coverage:** Tuner bandwidth spans 24 MHz to 1766 MHz (direct sampling can reach 0.5–24 MHz). High-frequency 2.4 GHz and 5 GHz ISM bands are outside the tuning range of standard RTL2832U hardware without an external upconverter/downconverter.
- **Dynamic Range & Bit Depth:** The RTL2832U features an 8-bit analog-to-digital converter (ADC), providing an effective dynamic range of approximately 45–50 dB. This requires proper manual gain management to avoid front-end saturation.
- **Power Calibration:** Signals are measured in dBFS (decibels relative to full scale) and approximated in dBm using standard 50-ohm load calibration offsets.

---

## Chapter 2: Theoretical Foundations & Mathematical Formulations

### 2.1 Software Defined Radio (SDR) Principles & RTL2832U Architecture
Software Defined Radio replaces traditional hardwired analog mixers, intermediate frequency (IF) filters, and analog demodulators with software algorithms running on a general-purpose processor.

The RTL2832U dongle functions as a dual-channel direct-conversion (zero-IF / low-IF) receiver. The analog RF signal intercepted by the antenna passes through an electrostatic discharge (ESD) protection network into the Rafael Micro R820T2 silicon tuner. The tuner applies low-noise amplification (LNA), image rejection mixing with a local oscillator ($f_{\text{LO}}$), and programmable intermediate frequency filtering. The baseband in-phase ($I$) and quadrature ($Q$) signals are then digitized by twin 8-bit ADCs at sampling rates up to $f_s = 2.8\text{ MS/s}$.

The digitized complex baseband stream represents:
$$s[n] = I[n] + j Q[n]$$
where $I[n]$ and $Q[n]$ represent the instantaneous Cartesian coordinates of the received electromagnetic vector.

### 2.2 Digital Signal Processing & Power Spectral Density (PSD)
To transform continuous time-domain baseband buffers into the frequency domain, the DSP core applies windowed Discrete Fourier Transforms (DFT) computed via the Fast Fourier Transform (FFT).

#### 2.2.1 Windowing & Spectral Leakage Suppression
Rectangular truncation of finite sample buffers causes spectral leakage due to high-amplitude sinc sidelobes ($-13\text{ dB}$). To suppress sidelobe spillover into adjacent bins, the processor applies window functions $w[n]$:

- **Hann Window:**
  $$w[n] = 0.5 \left(1 - \cos\left(\frac{2\pi n}{N - 1}\right)\right), \quad 0 \le n \le N-1$$
- **Hamming Window:**
  $$w[n] = 0.54 - 0.46 \cos\left(\frac{2\pi n}{N - 1}\right)$$
- **Blackman Window:**
  $$w[n] = 0.42 - 0.5 \cos\left(\frac{2\pi n}{N-1}\right) + 0.08 \cos\left(\frac{4\pi n}{N-1}\right)$$

#### 2.2.2 Normalized Power Spectral Density
Given a windowed complex block $x[n] = s[n] \cdot w[n]$, the $N$-point FFT is computed as:
$$X[k] = \sum_{n=0}^{N-1} x[n] e^{-j 2\pi k n / N}, \quad k = 0, 1, \dots, N-1$$

The spectrum is zero-frequency shifted (`fftshift`) so that DC ($0\text{ Hz}$) appears at the center bin $N/2$. The power spectral density in decibels relative to full scale (dBFS) is evaluated as:
$$\text{PSD}_{\text{dBFS}}[k] = 20 \log_{10} \left( \frac{|X[k]|}{N \cdot S_{\text{window}}} + \epsilon \right)$$
where $S_{\text{window}} = \frac{1}{N} \sum_{n=0}^{N-1} w[n]$ is the coherent window gain, and $\epsilon = 10^{-12}$ prevents numerical underflow.

The physical frequency assigned to bin $k$ is:
$$f[k] = f_{\text{center}} - \frac{f_s}{2} + k \cdot \frac{f_s}{N}, \quad \Delta f = \frac{f_s}{N}$$

#### 2.2.3 Noise Floor Estimation
The receiver noise floor is estimated dynamically using an order-statistic trimmed estimator:
$$P_{\text{noise}} = \text{Percentile}_{20}\left( \text{PSD}_{\text{dBFS}} \right)$$
Evaluating the 20th percentile rather than the arithmetic mean ensures that high-power broadcast carriers do not artificially bias the noise floor estimate upward.

### 2.3 Indian National Frequency Allocation Plan (NFAP 2022)
Signal identification requires matching detected spectral peaks against established regulatory allocations. In accordance with the Ministry of Communications, Government of India (Wireless Planning & Coordination Wing), the primary allocated bands within the tuner's range are:

| Band Classification | Frequency Span | Regulatory Description |
| :--- | :--- | :--- |
| **Commercial FM Broadcast** | $88.000 - 108.000\text{ MHz}$ | Sound broadcasting, wideband FM ($200\text{ kHz}$ channel spacing) |
| **VHF Aviation Airband** | $108.000 - 137.000\text{ MHz}$ | Air traffic control, AM voice communication, VOR navigation |
| **2m Amateur Radio VHF** | $144.000 - 148.000\text{ MHz}$ | Amateur satellite and terrestrial repeaters |
| **ISM / Telemetry 433** | $433.050 - 434.790\text{ MHz}$ | Short-range devices (SRD), remote keyless entry, industrial telemetry |
| **ISM / LoRa India** | $865.000 - 867.000\text{ MHz}$ | India delicensed sub-GHz IoT band (LoRaWAN, smart metering) |
| **GSM 900 Downlink** | $935.000 - 960.000\text{ MHz}$ | Cellular base transceiver station (BTS) to mobile downlink |
| **Aviation ADS-B Mode-S** | $1090.000\text{ MHz}$ | Airborne surveillance, transponder beacon broadcast ($1090\text{ MHz}$) |

### 2.4 Higher-Order Statistics & Automatic Modulation Classification (AMC)
Automatic Modulation Classification allows autonomous identification of carrier modulation schemes without prior pilot synchronization. The system implements 4th-order cumulant features following the Swami & Sadler formulation.

#### 2.4.1 Moments and Cumulants Formulation
Let $s[n]$ be a zero-mean, unit-energy baseband complex signal such that $E[|s|^2] = 1.0$. The higher-order moments (HOMs) are defined as:
$$\mu_{20} = E[s^2], \quad \mu_{21} = E[|s|^2] = 1.0$$
$$\mu_{40} = E[s^4], \quad \mu_{42} = E[|s|^4]$$

The 4th-order cumulants (HOCs) are computed as:
$$C_{40} = \mu_{40} - 3 (\mu_{20})^2$$
$$C_{42} = \mu_{42} - |\mu_{20}|^2 - 2 (\mu_{21})^2$$

Theoretical magnitudes for normalized constellations under ideal conditions:
- **Gaussian Noise:** $|C_{40}| \approx 0.0$, $|C_{42}| \approx 0.0$, $|\mu_{20}| \approx 0.0$
- **BPSK:** $|C_{40}| = 2.0$, $|C_{42}| = 2.0$, $|\mu_{20}| = 1.0$
- **QPSK / 4-QAM:** $|C_{40}| = 1.0$, $|C_{42}| = 1.0$, $|\mu_{20}| \approx 0.0$
- **16-QAM:** $|C_{40}| \approx 0.68$, $|C_{42}| \approx 0.68$, $|\mu_{20}| \approx 0.0$

#### 2.4.2 Blind Carrier Frequency Offset (CFO) Compensation
Residual carrier frequency offset causes constellation rotation that degrades cumulant calculation. To eliminate CFO without pilot symbols, the engine applies a 4th-power nonlinear feedback loop (Viterbi & Viterbi algorithm):
$$R_{4}[1] = E\left[ (s[n])^4 \cdot (s^*[n-1])^4 \right]$$
$$\Delta \hat{\omega} = \frac{1}{4} \text{arg}\left( R_{4}[1] \right)$$
$$s_{\text{corrected}}[n] = s[n] \cdot e^{-j \Delta \hat{\omega} n}$$

### 2.5 State-Space Estimation & Adaptive Kalman Filtering
In low-SNR environments, spectral measurements and RSSI indicators fluctuate rapidly due to thermal noise and quantization errors. A linear moving average introduces unacceptable group delay when measuring sudden physical shielding changes. The system implements an adaptive 1D Kalman filter and a vectorized spectral smoother.

#### 2.5.1 Discrete Kalman Model
The discrete state-space formulation is:
- **State equation:** $x[k] = x[k-1] + w[k], \quad w[k] \sim \mathcal{N}(0, Q)$
- **Measurement equation:** $z[k] = x[k] + v[k], \quad v[k] \sim \mathcal{N}(0, R)$

The recursive execution steps are:
1. **Time Update (Prediction):**
   $$\hat{x}^-[k] = \hat{x}[k-1]$$
   $$P^-[k] = P[k-1] + Q$$

2. **Innovation & Adaptive Gating:**
   $$y[k] = z[k] - \hat{x}^-[k]$$
   $$\text{If } |y[k]| > 3.0 \sqrt{R} \implies P^-[k] = \max(P^-[k], |y[k]|)$$
   *When a physical shield is suddenly applied, the innovation $|y[k]|$ spikes dramatically. Inflating $P^-[k]$ forces the filter to immediately trust the new measurement, eliminating sluggish convergence.*

3. **Measurement Update (Correction):**
   $$K[k] = \frac{P^-[k]}{P^-[k] + R}$$
   $$\hat{x}[k] = \hat{x}^-[k] + K[k] y[k]$$
   $$P[k] = (1 - K[k]) P^-[k]$$

### 2.6 Electromagnetic Shielding Effectiveness Theory
Electromagnetic shielding effectiveness (SE) quantifies the attenuation of electromagnetic waves passing through a physical barrier.

#### 2.6.1 Classical Wave Attenuation
According to Schelkunoff’s theory, total shielding effectiveness represents the sum of reflection loss ($R$), absorption loss ($A$), and multiple internal reflection correction ($B$):
$$\text{SE}_{\text{total}} = R + A + B \quad (\text{in dB})$$

- **Absorption Loss:**
  $$A = 8.686 \cdot \frac{t}{\delta} \quad (\text{dB})$$
  where $t$ is the material thickness, and $\delta = \frac{1}{\sqrt{\pi f \mu \sigma}}$ is the skin depth ($\mu$ is magnetic permeability, $\sigma$ is electrical conductivity).
- **Reflection Loss:**
  $$R \approx 168 - 10 \log_{10}\left( \frac{\mu_r}{\sigma_r} \cdot f \right) \quad (\text{dB})$$

#### 2.6.2 Experimental Differential Formulation
In the software engine, SE is measured across identical receiver gain settings between an unshielded reference state ($P_0$) and a shielded enclosure state ($P_1$):
$$\text{SE (dB)} = P_0 - P_1$$
$$\text{Power Attenuation Ratio} = 10^{\frac{\text{SE}}{10}}$$
$$\text{Percentage Power Blocked} = \left( 1 - 10^{-\frac{\text{SE}}{10}} \right) \times 100\%$$

### 2.7 Composite RF Exposure Index Formulation
To convey complex spectral measurements to non-technical observers, the engine calculates a composite normalized score ($0 \le \text{Index} \le 100$).

1. **Total Channel Power Integration:**
   $$P_{\text{total}} = \sum_{k=0}^{N-1} 10^{\frac{\text{PSD}_{\text{dBFS}}[k]}{10}}$$
   $$P_{\text{total, dBFS}} = 10 \log_{10}(P_{\text{total}})$$

2. **Sigmoidal Normalization:**
   $$\text{Score} = \text{clip}\left( \frac{P_{\text{total, dBFS}} - P_{\text{floor, ref}}}{P_{\text{ceil, ref}} - P_{\text{floor, ref}}} \times 100, \quad 0, \quad 100 \right)$$
   where $P_{\text{floor, ref}} = -90.0\text{ dBFS}$ (quiet baseline) and $P_{\text{ceil, ref}} = -15.0\text{ dBFS}$ (severe saturation).

3. **Safety Tier Boundaries:**
   - **Safe Ambient (Low):** $\text{Score} < 35$ ($P_{\text{peak}} < -50\text{ dBFS}$)
   - **Moderate (Warning):** $35 \le \text{Score} \le 70$ (Standard urban wireless environment)
   - **Elevated (Caution):** $\text{Score} > 70$ (Direct proximity to high-power emitter)

---

## Chapter 3: System Architecture & Design Specifications

### 3.1 High-Level Architecture
The system consists of four primary functional tiers: Physical RF Hardware, Background Acquisition Worker, DSP Core & Analytics, and Graphical User Interface & Storage.

```
+─────────────────────────────────────────────────────────────+
|                     PHYSICAL ENVIRONMENT                    |
|    Ambient Signals (FM, GSM, Wi-Fi) / Test Barrier Shields  |
+──────────────────────────────┬──────────────────────────────+
                               │
                               ▼
+─────────────────────────────────────────────────────────────+
|                      HARDWARE SUBSYSTEM                     |
|  - Telescopic Dipole Antenna Subsystem                      |
|  - RTL-SDR Blog V3 (R820T2 Tuner + RTL2832U 8-bit ADC)      |
|  - USB 2.0 Bulk Endpoint Stream (pyrtlsdr / librtlsdr)      |
+──────────────────────────────┬──────────────────────────────+
                               │ Complex I/Q Samples
                               ▼
+─────────────────────────────────────────────────────────────+
|               ASYNCHRONOUS WORKER THREAD (QThread)          |
|  - Continuous non-blocking hardware buffer capture          |
|  - Frame-rate throttling (Target: 30 FPS, Actual: 20-25 FPS)|
|  - Inter-thread signal dispatch to GUI event loop           |
+──────────────────────────────┬──────────────────────────────+
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
+──────────────────────────────+  +──────────────────────────────+
|           DSP CORE           |  |       CLASSIFIER & AMC       |
| - Windowed FFT Engine        |  | - Indian NFAP Band Matcher   |
| - Logarithmic PSD Scaling    |  | - 4th-Order Cumulants (CFO)  |
| - Prominence Peak Detector   |  | - BPSK / QPSK / 16QAM Engine |
| - 1D & Vector Kalman Filter  |  | - Occupied Channel Bandwidth |
+──────────────┬───────────────+  +──────────────┬───────────────+
               │                                 │
               └────────────────┬────────────────┘
                                │
                                ▼
+─────────────────────────────────────────────────────────────+
|                  ANALYTICS & SHIELDING ENGINE               |
| - Composite RF Exposure Index Calculator (0 - 100)          |
| - Dual-Pass Differential Shielding Engine (P0 / P1, SE dB)  |
+──────────────────────────────┬──────────────────────────────+
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
+──────────────────────────────+  +──────────────────────────────+
|    PyQt6 GRAPHICAL DASHBOARD |  |     PERSISTENCE & MAPPING    |
| - Real-Time PyQtGraph PSD    |  | - SQLite Database (WAL mode) |
| - 2D Scrolling Spectrogram   |  | - CSV Telemetry Exporter     |
| - Audience Exposure Ribbon   |  | - Leaflet/Folium REM Heatmap |
| - Active Carrier Data Table  |  | - Academic HTML/Print Report |
+──────────────────────────────+  +──────────────────────────────+
```

### 3.2 Hardware Specifications

| Component | Subsystem | Technical Specifications |
| :--- | :--- | :--- |
| **Receiver** | RTL-SDR Blog V3 | Tuner: Rafael Micro R820T2; ADC: Realtek RTL2832U; Resolution: 8 bits; TCXO: 0.5 PPM temperature compensated; Bias-T: 4.5V software switchable; Enclosure: Aluminum shielded; Interface: USB 2.0 |
| **Frequency Range**| Tuner Bandwidth | 24 MHz to 1766 MHz (direct sampling: 500 kHz to 24 MHz) |
| **Sampling Rate** | Baseband ADC | Configurable: 900 kS/s to 2800 kS/s (Nominal: 2048 kS/s without packet dropouts) |
| **Antenna** | RF Front-End | Wideband telescopic dipole antenna kit, adjustable length (20 cm to 1.5 m), 50-ohm RG174 coaxial cable with SMA male termination |
| **Host System** | Compute Node | Laptop / Desktop PC; Intel Core i5 / AMD Ryzen 5 or equivalent; 4 GB RAM minimum; Windows 10/11 64-bit OS |
| **Test Shields** | Material Enclosures | Dual-layer commercial aluminum foil ($0.03\text{ mm}$ total thickness); perforated copper/brass wire gauze ($0.8\text{ mm}$ aperture); sealed carbon steel enclosure; non-conductive plastic box |

### 3.3 Software Architecture & Threading Model
In high-rate DSP visualization applications, blocking the user interface thread with heavy mathematical processing results in frozen windows and buffer overflows. To guarantee deterministic performance, the application enforces strict multi-threaded separation:

1. **Hardware Acquisition Worker (`SDRWorker`):** Runs on a dedicated `QThread`. It interfaces with `pyrtlsdr` via native C DLL calls, reads blocks of 131,072 complex samples, computes windowed FFTs and power spectral densities, and emits Qt signals at regulated intervals.
2. **Main GUI Thread (`MainWindow`):** Operates the PyQt6 event loop, updating GPU-accelerated PyQtGraph plots, refreshing data tables, and responding to user interaction without experiencing frame drops.
3. **Database Concurrency:** The SQLite database utilizes Write-Ahead Logging (`WAL` mode) with a 5000 ms busy timeout, allowing concurrent write logging from background survey threads without locking GUI queries.

---

## Chapter 4: Detailed Implementation of Core Modules

### 4.1 Hardware Interface & Acquisition (`src/hardware/`)
- **`sdr_device.py` (`SDRDevice`):** Wraps `pyrtlsdr.RtlSdr`. Provides bulletproof error handling, auto-detection of bundled DLLs (`rtlsdr.dll`, `pthreadVC2.dll`, `msvcr100.dll`), valid gain step discovery (0.0 to 49.6 dB), and tuner re-tuning logic.
- **`worker.py` (`SDRWorker`):** Inherits from `QThread`. Executes an asynchronous acquisition loop throttled by a high-resolution timer. Decouples raw hardware reads from DSP dispatch to prevent USB buffer overflow.

### 4.2 DSP Processing Engine & Peak Detection (`src/dsp/`)
- **`fft_processor.py` (`FFTProcessor`):** Implements dynamic window generation (Hann, Hamming, Blackman), vector FFT computation, coherent window power normalization, zero-frequency centering, and exponential moving average (EMA) smoothing:
  $$P_{\text{avg}}[k] = \alpha \cdot P_{\text{current}}[k] + (1 - \alpha) \cdot P_{\text{avg}}[k-1], \quad \alpha = \frac{2}{N_{\text{avg}} + 1}$$
- **`peak_detector.py` (`PeakDetector`):** Utilizes `scipy.signal.find_peaks` with custom prominence filtering ($\ge 6.0\text{ dB}$) and minimum bin separation. For each detected peak, it computes signal-to-noise ratio (SNR) and calculates the 3 dB and 10 dB occupied bandwidths through interpolation across adjacent bins.
- **`kalman_filter.py` (`KalmanFilter1D`, `VectorKalmanSmoother`):** Implements recursive 1D state estimation for scalar indicators and a vectorized bin-by-bin spectrum smoother for 2048-point PSD arrays. Features innovation gating ($|y| > 3\sigma$) to track abrupt shielding changes without delay.

### 4.3 Regulatory & Modulation Classifier (`src/classifier/`)
- **`band_definitions.py`:** Contains formal frequency boundaries and descriptions for commercial FM, VHF Airband, 2m Amateur, ISM 433, ISM/LoRa 865, GSM 900, and ADS-B 1090 MHz in accordance with India NFAP 2022.
- **`classifier.py` (`BandClassifier`):** Matches detected carrier peaks against regulatory boundaries, labeling carriers and evaluating the dominant active service in the current band.
- **`modulation_classifier.py` (`ModulationClassifier`):** Computes Swami & Sadler 4th-order cumulants ($C_{40}, C_{42}$) and 2nd-order moments ($U_{20}$) with blind 4th-power CFO compensation. Classifies baseband buffers into BPSK, QPSK/4-QAM, 16-QAM, and Gaussian noise.

### 4.4 Exposure Scoring Engine (`src/exposure/`)
- **`exposure_index.py` (`ExposureIndexEngine`):** Integrates wideband channel power, computes composite 0–100 exposure scores, and assigns environmental safety tiers (*Safe Ambient*, *Moderate*, *Elevated*) based on ICNIRP public reference limits.

### 4.5 Shielding Attenuation Engine (`src/shielding/`)
- **`differential_engine.py` (`ShieldingDifferentialEngine`):** Orchestrates the dual-pass shielding measurement workflow. In baseline capture mode, it averages $N=50$ incoming frames to record a reference curve $P_0[k]$. In differential mode, it computes the live delta curve $\Delta P[k] = P_0[k] - P_1[k]$, evaluates peak attenuation ($dB$), calculates percentage power blocked, and assigns material ratings.

### 4.6 Survey Database, Mapping & Reports (`src/storage/`)
- **`survey_database.py` (`SurveyDatabase`):** Manages SQLite schema (`survey_logs`, `shielding_logs`), connection pools, summary statistics queries, and CSV data export.
- **`survey_logger.py` (`SurveyLogger`):** Provides interval-throttled automatic survey logging (1.0s to 10.0s intervals) and instant manual snapshot logging.
- **`rem_map_generator.py` (`RadioEnvironmentMapGenerator`):** Generates interactive Leaflet/Folium Radio Environment Maps (`data/radio_environment_map.html`) featuring weighted heatmaps and detailed popups with GPS coordinates.
- **`report_generator.py` (`ReportGenerator`):** Compiles academic, print-ready HTML reports (`data/rf_survey_report.html`) complete with executive KPI cards, spatial location tables, and shielding benchmark logs.

### 4.7 Graphical User Interface (`src/gui/`)
- Built using **PyQt6** and **PyQtGraph** with a custom dark theme design system (`styles.py`).
- **`SpectrumWidget`:** Live interactive PSD plot with peak markers, noise floor line, baseline curve overlay, and differential delta curve.
- **`WaterfallWidget`:** Scrolling 2D spectrogram with custom colormaps (`viridis`, `inferno`) synchronized to the spectrum frequency axis.
- **`AudienceExposureCard`:** High-contrast audience ribbon featuring live exposure gauge, dominant band tag, and a one-click presentation mode toggle.
- **`ControlsPanel`, `CarrierTableWidget`, `ShieldingPanel`, `SurveyPanel`:** Tabbed sidebar providing full control over tuner hardware, DSP parameters, shielding tests, and survey logging.

---

## Chapter 5: Verification Protocols, Experimental Results & Benchmarks

### 5.1 Verification Test Suite Architecture
To ensure high engineering rigor, five automated verification test suites and four specialized benchmark scripts were developed:

| Verification Script | Scope of Verification | Key Pass Criteria |
| :--- | :--- | :--- |
| `verify_phase1.py` | RTL-SDR connectivity, I/Q buffer streaming, FFT throughput | Buffer read $\ge 2.048\text{ MS/s}$, FFT compute latency $< 5\text{ ms}$ |
| `verify_phase2.py` | PyQt6 GUI integration, rendering loop | Sustained GUI frame rate $\ge 15\text{ FPS}$ without memory leaks |
| `verify_phase3.py` | Peak detector, NFAP band classifier, Exposure Index | Correct identification of FM (98.3 MHz) & GSM (935 MHz); Exposure 0–100 |
| `verify_phase4.py` | Shielding differential engine, P0 baseline, SE math | Baseline capture across 50 frames; accurate SE ($dB$) & delta curves |
| `verify_phase5.py` | SQLite CRUD, throttling, CSV export, HTML report | Database write integrity, CSV export generation, HTML report creation |
| `verify_kalman_filter.py`| 1D Kalman jitter reduction, step response, Vector smoother| Jitter variance reduction $> 3\times$; step error $< 1\text{ dB}$; time $< 1\text{ ms}$ |
| `verify_modulation_classifier.py`| Cumulant AMC accuracy on synthetic and live signals | $>90\%$ confidence on BPSK, QPSK, 16QAM; execution $< 5\text{ ms}$ |
| `verify_shielding_benchmark.py`| Multi-material shielding benchmark, figure export | Benchmark data logging to SQLite; 300 DPI publication figure export |
| `verify_rem_mapping.py` | Spatial database queries, coordinate resolution, Folium map| HTML escaping validation, unmapped site omission, Leaflet map creation |

### 5.2 Real-Time GUI Performance & Frame Rate
Under standard test conditions on a modern laptop (AMD Ryzen / Intel Core i5, 8 GB RAM):
- **Target Frame Rate:** 30 FPS
- **Measured Frame Rate:** **20.0 to 24.5 FPS**
- **FFT Size:** 2048 bins
- **FFT Processing Latency:** $1.82\text{ ms}$ per frame
- **CPU Utilization:** $< 12\%$ on quad-core host

### 5.3 Kalman Filter Variance Reduction & Step-Tracking Benchmark
Executing `verify_kalman_filter.py` on an experimental carrier with 3.0 dB measurement noise jitter:
- **True Signal Level:** $-45.0\text{ dBm}$
- **Raw Measurement Variance:** $8.70\text{ dB}^2$ ($\sigma = 2.95\text{ dB}$)
- **Kalman Filtered Variance:** $0.74\text{ dB}^2$ ($\sigma = 0.86\text{ dB}$)
- **Jitter Reduction Factor:** **11.7× variance reduction**
- **Sudden Physical Step Response (20 dB Shielding Jump):** Settled within 2 frames to $-54.83\text{ dBm}$ (target: $-55.00\text{ dBm}$, error: $0.17\text{ dB}$).
- **Vector Smoother Execution Time:** **0.139 ms** per 2048-bin frame.

### 5.4 Automatic Modulation Classification Benchmark
Evaluating `verify_modulation_classifier.py` across 16,384-sample blocks at $30\text{ dB}$ SNR:

| Modulation Scheme | Theoretical $|C_{40}|$ | Measured $|C_{40}|$ | Theoretical $|C_{42}|$ | Measured $|C_{42}|$ | Decision Label | Classification Confidence |
| :--- | :---: | :---: | :---: | :---: | :--- | :---: |
| **BPSK** | $2.000$ | $1.996$ | $2.000$ | $1.996$ | BPSK (Binary Phase Shift Keying) | **99.0%** |
| **QPSK / 4-QAM** | $1.000$ | $0.998$ | $1.000$ | $0.998$ | QPSK / 4-QAM (Quadrature Phase) | **99.0%** |
| **16-QAM** | $0.680$ | $0.677$ | $0.680$ | $0.677$ | 8-QAM / 16-QAM (Multi-Level) | **95.0%** |
| **Gaussian Noise** | $0.000$ | $0.045$ | $0.000$ | $0.003$ | Noise (Gaussian-like) | **82.0%** |

- **Execution Latency:** **0.50 ms** per classification pass, proving real-time viability.

### 5.5 Quantitative Multi-Material Shielding Effectiveness Benchmark
Experimental shielding tests conducted at 98.30 MHz (commercial FM carrier, unshielded baseline $P_0 = -24.80\text{ dBFS}$):

| Material / Barrier Description | Peak Power ($P_1$) | Shielding Effectiveness (SE) | Channel Power Drop | Noise Floor Drop | Power Blocked (%) | Classification Tier |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Baseline (Unshielded)** | $-24.80\text{ dBFS}$ | $0.00\text{ dB}$ (Ref) | $0.00\text{ dB}$ | $0.00\text{ dB}$ | $0.00\%$ | Minimal / Ineffective |
| **Wire Mesh (Perforated)** | $-34.60\text{ dBFS}$ | $+9.80\text{ dB}$ | $+8.60\text{ dB}$ | $+0.50\text{ dB}$ | $89.53\%$ | Moderate Attenuation |
| **Aluminium Foil (Dual Layer)** | $-48.20\text{ dBFS}$ | $+23.40\text{ dB}$ | $+21.70\text{ dB}$ | $+3.60\text{ dB}$ | $99.54\%$ | Excellent Shielding (>99%) |
| **Steel Enclosure (Faraday)** | $-59.40\text{ dBFS}$ | $+34.60\text{ dB}$ | $+31.90\text{ dB}$ | $+4.90\text{ dB}$ | $99.97\%$ | Excellent Shielding (>99%) |

The benchmark generated a high-resolution, publication-grade dual-panel figure exported to [`data/viva_shielding_analysis.png`](file:///c:/Users/bevin/OneDrive/Desktop/RF-monitor-tool/data/viva_shielding_analysis.png) illustrating carrier peak suppression and quantitative attenuation bars.

### 5.6 Spatial Campus Survey & Radio Environment Map (REM)
Spatial RF surveys conducted across designated locations at KLS VDIT Haliyal revealed significant ambient variability:

| Location / Survey Site Tag | GPS Coordinates | Observed Peak Level | Dominant Service | Exposure Score | Exposure Tier |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **ECE Communication Lab** | $15.3348^\circ\text{ N}, 74.7570^\circ\text{ E}$ | $-28.5\text{ dBFS}$ | Cellular / Broadcast | 78 / 100 | Elevated (Caution) |
| **VDIT Main Entrance** | $15.3352^\circ\text{ N}, 74.7562^\circ\text{ E}$ | $-45.0\text{ dBFS}$ | Cellular Downlink | 42 / 100 | Moderate (Warning) |
| **Central Library** | $15.3342^\circ\text{ N}, 74.7578^\circ\text{ E}$ | $-62.0\text{ dBFS}$ | Ambient Noise Floor | 18 / 100 | Safe Ambient (Low) |
| **Student Hostel Block** | $15.3360^\circ\text{ N}, 74.7585^\circ\text{ E}$ | $-38.0\text{ dBFS}$ | LoRa / Cellular | 56 / 100 | Moderate (Warning) |
| **Campus Sports Field** | $15.3332^\circ\text{ N}, 74.7580^\circ\text{ E}$ | $-68.0\text{ dBFS}$ | FM Broadcast (Distant)| 12 / 100 | Safe Ambient (Low) |

The records were synthesized into an interactive geospatial heatmap (`data/radio_environment_map.html`), allowing users to click marker pins and inspect location-specific RF metrics.

---

## Chapter 6: Practical Applications & Comparative Analysis

### 6.1 Cost-Benefit Analysis: Commercial Spectrum Analyzers vs. RTL-SDR System

| Parameter / Feature | Keysight FieldFox N9914B | Rohde & Schwarz FPH | RTL-SDR RF Monitor (This Project) |
| :--- | :--- | :--- | :--- |
| **Hardware BOM Cost** | **$12,500 – $15,000 USD** | **$7,500 – $10,000 USD** | **< $40 USD** |
| **Form Factor & Weight** | $3.2\text{ kg}$ handheld | $2.5\text{ kg}$ portable | **$< 0.3\text{ kg}$ ultra-portable** |
| **Frequency Span** | $30\text{ kHz} - 6.5\text{ GHz}$ | $5\text{ kHz} - 3\text{ GHz}$ | $24\text{ MHz} - 1.7\text{ GHz}$ |
| **ADC Resolution** | 14-bit | 14-bit | 8-bit |
| **Real-Time Display Rate** | ~15–20 sweeps/sec | ~15 sweeps/sec | **20–25 FPS (GPU-accelerated)** |
| **Regulatory Band Mapping** | Manual marker setup | Manual marker setup | **Automated (India NFAP 2022)** |
| **Modulation Classifier (AMC)**| Expensive software option | Expensive software option | **Built-in (4th-order cumulants)** |
| **Shielding Attenuation Tool** | Manual trace subtraction | Manual trace subtraction | **Dedicated dual-pass differential engine** |
| **Audience Exposure Ribbon** | None | None | **Built-in (0–100 score & presentation mode)** |
| **Geospatial REM Heatmap** | Proprietary PC software | Proprietary PC software | **Interactive Folium/Leaflet HTML export** |
| **Open-Source Adaptability** | Closed proprietary firmware | Closed proprietary firmware | **100% Open-source Python codebase** |

### 6.2 Practical Domains of Application
1. **Academic Laboratories & Engineering Pedagogy:** Provides undergraduate ECE students with a transparent, low-cost platform to observe AM/FM modulation, discrete Fourier transforms, filter windowing, and wireless channel multipath in real time.
2. **Facility EMI/RFI Auditing:** Enables laboratory technicians and hospital biomedical engineers to rapidly scan ambient noise floors and detect electromagnetic interference near sensitive analytical instruments.
3. **Shielding Performance Validation:** Offers a standardized, reproducible method to evaluate the attenuation of custom RF shielding enclosures, Faraday cages, and conductive textiles before equipment deployment.
4. **Occupational Health & Environmental Surveys:** Empowers community researchers and occupational safety officers to perform continuous RF monitoring and log geographic exposure heatmaps.

---

## Chapter 7: Conclusions & Future Scope

### 7.1 Summary of Contributions
This project successfully designed, implemented, and benchmarked an open-source, low-cost, high-performance RF noise monitoring and reduction analysis system. Key contributions include:
- A high-framerate ($\ge 20\text{ FPS}$) real-time spectrum and waterfall visualization dashboard utilizing PyQt6 and PyQtGraph.
- Integration of the **Indian National Frequency Allocation Plan (NFAP 2022)** into an autonomous multi-carrier regulatory classification engine.
- An Automatic Modulation Classification (AMC) pipeline applying Swami & Sadler 4th-order cumulants and blind CFO compensation, achieving $>95\%$ confidence on standard digital modulations.
- An adaptive 1D Kalman filter and vectorized spectral smoother achieving **11.7× measurement jitter reduction** while tracking sudden physical attenuation steps.
- A normalized composite **RF Exposure Index** mapped to ICNIRP biological exposure boundaries.
- A dual-pass **Shielding Effectiveness (SE)** differential measurement engine demonstrating up to **+34.60 dB** attenuation (>99.9% blocked) on physical barrier materials.
- A complete data persistence, Leaflet/Folium Radio Environment Mapping, and academic report generation architecture.
- Full system validation at a hardware bill-of-materials cost of **< $40 USD**, achieving over a 99% cost reduction compared to proprietary spectrum analyzers.

### 7.2 Future Research Directions
- **Stepped Local Oscillator Wideband Sweeping:** Implement an automated frequency-hopping algorithm to synthesize contiguous multi-gigahertz spectral spans (e.g., sweeping from 24 MHz to 1.7 GHz) by stitching consecutive 2.4 MHz buffers.
- **Deep Learning Modulation Recognition:** Supplement cumulant-based AMC with a lightweight 1D Convolutional Neural Network (CNN) trained on raw I/Q samples to classify higher-order modulations (e.g., 64-QAM, OFDM) under negative SNR conditions.
- **Distributed IoT Sensor Mesh:** Deploy low-cost Raspberry Pi Zero W nodes equipped with RTL-SDR dongles across the campus to stream real-time spectral telemetry to a centralized cloud database for continuous environmental heatmapping.
- **Active Noise Cancellation (ANC) for RF:** Explore active RF phase-inversion cancellation circuits to actively attenuate narrow-band interferers entering sensitive receiving antennas.

---

## Chapter 8: References & Appendices

### 8.1 References
1. Wireless Planning & Coordination (WPC) Wing, Ministry of Communications, Government of India. *National Frequency Allocation Plan (NFAP-2022)*, New Delhi, India, 2022.
2. International Commission on Non-Ionizing Radiation Protection (ICNIRP). "Guidelines for Limiting Exposure to Electromagnetic Fields (100 kHz to 300 GHz)," *Health Physics*, vol. 118, no. 5, pp. 483–524, May 2020.
3. Swami, A., & Sadler, B. M. "Hierarchical digital modulation classification using cumulants," *IEEE Transactions on Communications*, vol. 48, no. 3, pp. 416–429, Mar. 2000.
4. Schelkunoff, S. A. *Electromagnetic Waves*, D. Van Nostrand Co., New York, 1943.
5. Welch, P. "The use of fast Fourier transform for the estimation of power spectra: A method based on time averaging over short, modified periodograms," *IEEE Transactions on Audio and Electroacoustics*, vol. 15, no. 2, pp. 70–73, Jun. 1967.
6. Kalman, R. E. "A New Approach to Linear Filtering and Prediction Problems," *Journal of Basic Engineering*, vol. 82, no. 1, pp. 35–45, Mar. 1960.
7. Viterbi, A. J., & Viterbi, A. M. "Nonlinear estimation of PSK-modulated carrier phase with application to burst digital transmission," *IEEE Transactions on Information Theory*, vol. 29, no. 4, pp. 543–551, Jul. 1983.
8. RTL-SDR Blog. *RTL-SDR Blog V3 User Guide and Technical Specifications*, 2023.

### 8.2 Technical Appendix: Verification Commands & Deliverables
The entire project verification pipeline can be reproduced using the following terminal commands:

```powershell
# 1. Activate project virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Execute core phased verification suites
.\.venv\Scripts\python.exe verify_phase1.py
.\.venv\Scripts\python.exe verify_phase2.py
.\.venv\Scripts\python.exe verify_phase3.py
.\.venv\Scripts\python.exe verify_phase4.py
.\.venv\Scripts\python.exe verify_phase5.py

# 3. Execute specialized algorithm benchmarks
.\.venv\Scripts\python.exe verify_kalman_filter.py
.\.venv\Scripts\python.exe verify_modulation_classifier.py
.\.venv\Scripts\python.exe verify_shielding_benchmark.py
.\.venv\Scripts\python.exe verify_rem_mapping.py

# 4. Launch main interactive GUI application
.\.venv\Scripts\python.exe main.py
```
