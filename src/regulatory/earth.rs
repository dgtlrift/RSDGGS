use crate::types::{BandEntry, ModulationType, PowerRef};

// FCC 902-928 MHz (Face 2 — N. America)
pub static FCC_902: BandEntry = BandEntry {
    band_id:       1,
    authority:     "FCC",
    citation:      "47 CFR 15.247",
    freq_lo_khz:   902_000,
    freq_hi_khz:   928_000,
    power_mw:      1_000,
    power_ref:     PowerRef::Conducted,
    duty_cycle:    None,
    dwell_s:       None,
    lbt:           false,
    hop_required:  true,
    min_hop_set:   Some(50),
    channels:      None,
    modulation:    None,
    whitespace_db: None,
    available:     true,
    exception:     false,
};

// ETSI 433 MHz (Face 1 — Europe)
pub static ETSI_433: BandEntry = BandEntry {
    band_id:       2,
    authority:     "ETSI",
    citation:      "EN 300 220-1",
    freq_lo_khz:   433_050,
    freq_hi_khz:   434_790,
    power_mw:      10,
    power_ref:     PowerRef::Erp,
    duty_cycle:    Some(0.10),
    dwell_s:       None,
    lbt:           false,
    hop_required:  false,
    min_hop_set:   None,
    channels:      None,
    modulation:    None,
    whitespace_db: None,
    available:     true,
    exception:     false,
};

// ETSI 868 MHz (Face 1 — Europe)
pub static ETSI_868: BandEntry = BandEntry {
    band_id:       3,
    authority:     "ETSI",
    citation:      "EN 300 220-2",
    freq_lo_khz:   863_000,
    freq_hi_khz:   870_000,
    power_mw:      25,
    power_ref:     PowerRef::Eirp,
    duty_cycle:    Some(0.01),
    dwell_s:       None,
    lbt:           false,
    hop_required:  false,
    min_hop_set:   None,
    channels:      None,
    modulation:    None,
    whitespace_db: None,
    available:     true,
    exception:     false,
};

// ACMA 915-928 MHz (Face 11 — Oceania)
pub static ACMA_915: BandEntry = BandEntry {
    band_id:       4,
    authority:     "ACMA",
    citation:      "Radiocommunications (Low Interference Potential Devices) Class Licence 2015",
    freq_lo_khz:   915_000,
    freq_hi_khz:   928_000,
    power_mw:      1_000,
    power_ref:     PowerRef::Eirp,
    duty_cycle:    None,
    dwell_s:       None,
    lbt:           false,
    hop_required:  false,
    min_hop_set:   None,
    channels:      None,
    modulation:    None,
    whitespace_db: None,
    available:     true,
    exception:     false,
};

/// (face, band_id) → &BandEntry
static EARTH_TABLE: &[(u8, u32, &BandEntry)] = &[
    (2, 1, &FCC_902),
    (1, 2, &ETSI_433),
    (1, 3, &ETSI_868),
    (10, 4, &ACMA_915), // Face 10 covers Australia/Oceania despite the "S/SE Asia" label in constants.rs
];

pub fn lookup_face(face: u8, band_id: u32) -> Option<&'static BandEntry> {
    EARTH_TABLE
        .iter()
        .find(|&&(f, b, _)| f == face && b == band_id)
        .map(|&(_, _, e)| e)
}

pub fn bands_for_face(face: u8) -> impl Iterator<Item = &'static BandEntry> {
    EARTH_TABLE
        .iter()
        .filter(move |&&(f, _, _)| f == face)
        .map(|&(_, _, e)| e)
}

// suppress unused import warning for ModulationType
const _: ModulationType = ModulationType::Any;
