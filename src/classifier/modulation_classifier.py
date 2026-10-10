"""
Automatic Modulation Classification (AMC) & Higher-Order Cumulants Engine.
Ports, fixes, and elevates cumulant-based modulation recognition from RFA-Gemini into RF-monitor-tool.

Mathematical Foundations:
- Blind DC offset & carrier frequency offset (CFO) compensation (4th-power Viterbi & Viterbi loop).
- Higher-Order Moments (HOMs):
    mu_20 = E[s^2]
    mu_21 = E[|s|^2]
    mu_40 = E[s^4]
    mu_42 = E[|s|^4]   (Swami & Sadler standard definition)
- Higher-Order Cumulants (HOCs):
    C_40 = mu_40 - 3 * (mu_20)^2
    C_42 = mu_42 - |mu_20|^2 - 2 * (mu_21)^2
- Theoretical Values (Unit Power E[|s|^2] = 1.0):
    * Noise (Gaussian-like): |C_40| ~ 0.0, |C_42| ~ 0.0, |mu_20| ~ 0.0
    * BPSK         : |C_40| = 2.0, |C_42| = 2.0, |mu_20| = 1.0
    * QPSK / 4-QAM : |C_40| = 1.0, |C_42| = 1.0, |mu_20| ~ 0.0
    * 8-QAM/16-QAM : |C_40| ~ 0.68,|C_42| ~ 0.68,|mu_20| ~ 0.0
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np


@dataclass
class ModulationResult:
    """Stores the output of an automatic modulation classification pass."""
    format_label: str
    confidence_pct: float
    c40: float
    c42: float
    u20: float
    snr_est_db: float
    constellation_subsample: np.ndarray


class ModulationClassifier:
    """
    Automatic Modulation Classifier using 4th-order cumulants and blind CFO compensation.
    """

    def __init__(self, sample_rate: float = 2.048e6):
        self.sample_rate = sample_rate

    def normalize_iq(
        self,
        samples: np.ndarray,
        discard_transients: int = 512,
        compensate_cfo: bool = True
    ) -> np.ndarray:
        """
        Removes DC center spike, normalizes complex baseband samples to unit power,
        and optionally compensates residual carrier frequency offset (CFO).
        """
        if len(samples) < 512:
            return samples.copy()

        if discard_transients > 0 and len(samples) > discard_transients + 512:
            clean = samples[discard_transients:].copy()
        else:
            clean = samples.copy()

        # 1. Zero-mean centering (DC spike suppression)
        clean = clean - np.mean(clean)

        # 2. Unit-energy normalization: E[|s|^2] = 1.0
        pwr = np.mean(np.abs(clean) ** 2)
        rms = np.sqrt(pwr) + 1e-12
        clean = clean / rms

        # 3. Blind CFO compensation via 4th-power nonlinear loop (Viterbi & Viterbi)
        if compensate_cfo and len(clean) > 1024:
            s_4 = clean ** 4
            corr = np.mean(s_4[1:] * np.conj(s_4[:-1]))
            angle = np.angle(corr)
            # Only compensate if significant rotation detected (reduces noise jitter on static signals)
            if np.abs(angle) > 1e-4:
                cfo_est = angle / 4.0
                t = np.arange(len(clean), dtype=np.float64)
                clean = clean * np.exp(-1j * cfo_est * t)

        return clean

    def compute_cumulants(self, normalized_iq: np.ndarray) -> Tuple[float, float, float]:
        """
        Computes 4th-order cumulants C_40, C_42 and 2nd-order moment |u_20|
        using Swami & Sadler formulation.
        """
        s = normalized_iq
        # Moments
        u20 = np.mean(s ** 2)
        u21 = np.mean(np.abs(s) ** 2)
        u40 = np.mean(s ** 4)
        u42 = np.mean(np.abs(s) ** 4)

        # 4th-Order Cumulants
        c40 = u40 - 3.0 * (u20 ** 2)
        c42 = u42 - (np.abs(u20) ** 2) - 2.0 * (u21 ** 2)

        return float(np.abs(c40)), float(np.abs(c42)), float(np.abs(u20))

    def estimate_snr_db(self, normalized_iq: np.ndarray) -> float:
        """Estimates baseband SNR from signal envelope dispersion."""
        env = np.abs(normalized_iq)
        var_env = np.var(env)
        if var_env < 1e-6:
            return 30.0
        snr_linear = 1.0 / (2.0 * var_env + 1e-6)
        return float(10.0 * np.log10(np.clip(snr_linear, 0.1, 1000.0)))

    def classify(
        self,
        samples: np.ndarray,
        discard_transients: int = 512,
        max_constellation_pts: int = 1000,
        compensate_cfo: bool = True
    ) -> ModulationResult:
        """
        Classifies incoming raw I/Q samples into modulation format with confidence score.
        """
        if len(samples) < 512:
            return ModulationResult(
                format_label="Insufficient Samples",
                confidence_pct=0.0,
                c40=0.0,
                c42=0.0,
                u20=0.0,
                snr_est_db=0.0,
                constellation_subsample=np.array([], dtype=np.complex64),
            )

        norm_iq = self.normalize_iq(
            samples,
            discard_transients=discard_transients,
            compensate_cfo=compensate_cfo
        )
        abs_c40, abs_c42, abs_u20 = self.compute_cumulants(norm_iq)
        snr_est = self.estimate_snr_db(norm_iq)

        # Decision boundaries based on theoretical Swami & Sadler limits
        if abs_c40 < 0.25 and abs_c42 < 0.25:
            label = "Noise (Gaussian-like)"
            conf = min(99.0, max(60.0, (1.0 - max(abs_c40, abs_c42) / 0.25) * 100.0))
        elif abs_u20 > 0.60 and abs_c40 > 1.30:
            label = "BPSK (Binary Phase Shift Keying)"
            conf = min(99.0, max(65.0, (abs_c40 / 2.0) * 100.0))
        elif abs_c40 >= 0.70 and abs_c42 >= 0.65:
            label = "QPSK / 4-QAM (Quadrature Phase Shift)"
            conf = min(99.0, max(60.0, (1.0 - abs(abs_c40 - 1.0)) * 100.0))
        elif 0.25 <= abs_c40 < 0.70 and abs_c42 >= 0.35:
            label = "8-QAM / 16-QAM (Multi-Level Constellation)"
            conf = min(95.0, max(55.0, (abs_c40 / 0.68) * 100.0))
        else:
            label = "Complex Analog / Multipath (e.g. Broadcast FM)"
            conf = 75.0

        subsample = norm_iq[:max_constellation_pts]

        return ModulationResult(
            format_label=label,
            confidence_pct=round(conf, 1),
            c40=round(abs_c40, 4),
            c42=round(abs_c42, 4),
            u20=round(abs_u20, 4),
            snr_est_db=round(snr_est, 1),
            constellation_subsample=subsample,
        )

    @staticmethod
    def generate_synthetic_signal(
        modulation: str = "BPSK",
        num_samples: int = 8192,
        snr_db: float = 30.0,
        cfo_hz: float = 0.0,
        sample_rate: float = 2.048e6,
    ) -> np.ndarray:
        """
        Generates clean synthetic baseband signals with optional AWGN and CFO for testing.
        Supported modulations: 'BPSK', 'QPSK', '8QAM', 'CW', 'NOISE'.
        """
        mod = modulation.upper()
        if mod == "NOISE":
            noise_i = np.random.randn(num_samples)
            noise_q = np.random.randn(num_samples)
            return (noise_i + 1j * noise_q) / np.sqrt(2.0)

        if mod == "CW":
            symbols = np.ones(num_samples, dtype=np.complex64)
        elif mod == "BPSK":
            bits = np.random.choice([-1.0, 1.0], size=num_samples)
            symbols = bits.astype(np.complex64)
        elif mod == "QPSK":
            constellation = np.array([1 + 1j, 1 - 1j, -1 + 1j, -1 - 1j], dtype=np.complex64) / np.sqrt(2.0)
            symbols = np.random.choice(constellation, size=num_samples)
        elif mod in ("16QAM", "16-QAM", "8QAM", "8-QAM"):
            levels = np.array([-3, -1, 1, 3])
            pts = np.array([x + 1j * y for x in levels for y in levels], dtype=np.complex64)
            pts = pts / np.sqrt(np.mean(np.abs(pts)**2))
            symbols = np.random.choice(pts, size=num_samples)
        else:
            raise ValueError(f"Unsupported modulation type: {modulation}")

        # Add CFO
        if cfo_hz != 0.0:
            t = np.arange(num_samples) / sample_rate
            symbols = symbols * np.exp(1j * 2 * np.pi * cfo_hz * t)

        # Add AWGN
        if snr_db < 100.0:
            snr_linear = 10.0 ** (snr_db / 10.0)
            sig_pwr = np.mean(np.abs(symbols) ** 2)
            noise_pwr = sig_pwr / snr_linear
            noise = (np.random.randn(num_samples) + 1j * np.random.randn(num_samples)) * np.sqrt(noise_pwr / 2.0)
            return symbols + noise

        return symbols
