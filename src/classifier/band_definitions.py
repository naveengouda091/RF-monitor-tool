"""
Frequency allocation definitions for India (NFAP) and ITU Region 3.
Covers spectrum from 24 MHz to 1.766 GHz accessible via RTL-SDR Blog V3.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class BandInfo:
    name: str
    service: str
    freq_min_mhz: float
    freq_max_mhz: float
    description: str


# Standard Indian National Frequency Allocation Plan (NFAP) & ITU-R3 bands
INDIAN_FREQUENCY_BANDS: List[BandInfo] = [
    BandInfo(
        name="CB Radio",
        service="Civilian Mobile",
        freq_min_mhz=26.965,
        freq_max_mhz=27.405,
        description="Citizens Band 27 MHz short-range voice communications",
    ),
    BandInfo(
        name="10m Amateur Radio",
        service="Ham Radio",
        freq_min_mhz=28.0,
        freq_max_mhz=29.7,
        description="Amateur radio HF/VHF boundary band",
    ),
    BandInfo(
        name="FM Broadcast",
        service="Commercial Radio",
        freq_min_mhz=88.0,
        freq_max_mhz=108.0,
        description="Wideband FM commercial broadcasting (All India Radio / Private FM)",
    ),
    BandInfo(
        name="Aviation Nav (VOR)",
        service="Aeronautical",
        freq_min_mhz=108.0,
        freq_max_mhz=117.975,
        description="VHF Omnidirectional Range (VOR) and instrument landing systems",
    ),
    BandInfo(
        name="Aviation Airband",
        service="Air Traffic Control",
        freq_min_mhz=118.0,
        freq_max_mhz=137.0,
        description="Civil aviation voice communications (AM modulation)",
    ),
    BandInfo(
        name="2m VHF Amateur",
        service="Ham Radio",
        freq_min_mhz=144.0,
        freq_max_mhz=146.0,
        description="VHF 2-meter amateur repeaters and simplex voice",
    ),
    BandInfo(
        name="VHF Land Mobile",
        service="Public Safety",
        freq_min_mhz=146.0,
        freq_max_mhz=174.0,
        description="Police, railway, and municipal emergency services VHF dispatch",
    ),
    BandInfo(
        name="VHF TV / DAB",
        service="Broadcasting",
        freq_min_mhz=174.0,
        freq_max_mhz=230.0,
        description="VHF Band III television broadcast & digital audio radio",
    ),
    BandInfo(
        name="70cm UHF Amateur",
        service="Ham Radio",
        freq_min_mhz=430.0,
        freq_max_mhz=440.0,
        description="70cm amateur repeaters, digital voice, and satellite links",
    ),
    BandInfo(
        name="ISM 433 MHz",
        service="Telemetry / IoT",
        freq_min_mhz=433.05,
        freq_max_mhz=434.79,
        description="Short-range remotes, keyless entry, weather sensors, low-power telemetry",
    ),
    BandInfo(
        name="UHF Television",
        service="Broadcasting",
        freq_min_mhz=470.0,
        freq_max_mhz=698.0,
        description="Doordarshan and terrestrial digital TV channels",
    ),
    BandInfo(
        name="LTE 700 (Band 28 UL)",
        service="Cellular Uplink",
        freq_min_mhz=703.0,
        freq_max_mhz=748.0,
        description="4G/5G low-band mobile uplink transmissions",
    ),
    BandInfo(
        name="LTE 700 (Band 28 DL)",
        service="Cellular Downlink",
        freq_min_mhz=758.0,
        freq_max_mhz=803.0,
        description="4G/5G low-band base station carrier downlinks",
    ),
    BandInfo(
        name="LTE 850 (Band 5 UL)",
        service="Cellular Uplink",
        freq_min_mhz=824.0,
        freq_max_mhz=849.0,
        description="Mobile phone handset uplink to 850 MHz cell towers",
    ),
    BandInfo(
        name="ISM / LoRa India",
        service="IoT / RFID",
        freq_min_mhz=865.0,
        freq_max_mhz=867.0,
        description="License-free India IoT band: LoRaWAN, smart meters, and RFID tags",
    ),
    BandInfo(
        name="LTE 850 (Band 5 DL)",
        service="Cellular Downlink",
        freq_min_mhz=869.0,
        freq_max_mhz=894.0,
        description="Jio / Airtel 850 MHz LTE base station downlinks",
    ),
    BandInfo(
        name="GSM 900 (Uplink)",
        service="Cellular Handset",
        freq_min_mhz=890.0,
        freq_max_mhz=915.0,
        description="Mobile handset transmission in 900 MHz band (Band 8)",
    ),
    BandInfo(
        name="GSM 900 (Downlink)",
        service="Cellular Base Station",
        freq_min_mhz=935.0,
        freq_max_mhz=960.0,
        description="Cell tower transmission in 900 MHz band (Band 8)",
    ),
    BandInfo(
        name="ADS-B Flight Radar",
        service="Aviation Transponder",
        freq_min_mhz=1085.0,
        freq_max_mhz=1095.0,
        description="Commercial aircraft Mode-S / ADS-B beacon broadcasts (1090 MHz)",
    ),
    BandInfo(
        name="GPS L1 Navigation",
        service="Satellite GNSS",
        freq_min_mhz=1570.0,
        freq_max_mhz=1580.0,
        description="Global Positioning System civilian carrier (1575.42 MHz)",
    ),
    BandInfo(
        name="DCS / GSM 1800 (UL)",
        service="Cellular Handset",
        freq_min_mhz=1710.0,
        freq_max_mhz=1785.0,
        description="Handset transmission for 1800 MHz 2G/4G cellular (Band 3)",
    ),
]
