//! The Earth regulatory database (draft sections 8 and 9): band entries by face, and the
//! exception overlay for the locations face-level entries get wrong.
//!
//! Each entry cites the clause it comes from. Entries verified against the primary text
//! for this revision: ETSI EN 300 220-2 V3.2.1 Table B.1, EN 300 220-3-1 V2.1.1,
//! EN 300 220-3-2 V1.1.1, EN 300 328 V2.2.2, and 47 CFR 15.247 and 15.249. The others
//! (ACMA, and the exception overlay's 920-925 MHz entries) are as the draft gives them,
//! not yet checked against their primary texts. An emission complies if it meets at
//! least one entry that contains it.

use crate::types::{BandEntry, ExceptionEntry, ModulationType, PowerRef};

/// The fields most entries leave unset.
const BASE: BandEntry = BandEntry {
    band_id:                  0,
    authority:                "",
    citation:                 "",
    freq_lo_khz:              0,
    freq_hi_khz:              0,
    power_mw:                 0.0,
    power_ref:                PowerRef::Erp,
    duty_cycle:               None,
    dwell_s:                  None,
    lbt:                      false,
    hop_required:             false,
    min_hop_set:              None,
    channels:                 None,
    modulation:               None,
    whitespace_db:            None,
    available:                true,
    exception:                false,
    min_bw_khz:               None,
    psd_mw_per_mhz:           None,
    duty_cycle_above_mw:      None,
    dwell_window_s:           None,
    single_channel_power_mw:  None,
    single_channel_power_ref: None,
    single_channel_window_s:  None,
};

// ── Face 1, Europe: ETSI ─────────────────────────────────────────────────────────
//
// EN 300 220-2 V3.2.1 Table B.1 (bands H, K to Q; EC Decision 2017/1483/EU band numbers
// in brackets). "Duty cycle or polite spectrum access": the duty cycle is the limit
// checked; polite spectrum access is the alternative.

/// Band H, 433.050-434.790 MHz: 10 mW e.r.p., 10 % (44b, 45b).
pub static ETSI_433: BandEntry = BandEntry {
    band_id: 2,
    authority: "ETSI",
    citation: "EN 300 220-2 V3.2.1 Table B.1 band H",
    freq_lo_khz: 433_050,
    freq_hi_khz: 434_790,
    power_mw: 10.0,
    duty_cycle: Some(0.10),
    ..BASE
};

/// Band K, 863-865 MHz: 25 mW e.r.p., 0.1 % (46a).
pub static ETSI_863_K: BandEntry = BandEntry {
    band_id: 3,
    authority: "ETSI",
    citation: "EN 300 220-2 V3.2.1 Table B.1 band K",
    freq_lo_khz: 863_000,
    freq_hi_khz: 865_000,
    power_mw: 25.0,
    duty_cycle: Some(0.001),
    ..BASE
};

/// Band L, 865-868 MHz: 25 mW e.r.p., 1 % (47).
pub static ETSI_865_L: BandEntry = BandEntry {
    band_id: 5,
    citation: "EN 300 220-2 V3.2.1 Table B.1 band L",
    freq_lo_khz: 865_000,
    freq_hi_khz: 868_000,
    duty_cycle: Some(0.01),
    ..ETSI_863_K
};

/// Band M, 868.0-868.6 MHz: 25 mW e.r.p., 1 % (48).
pub static ETSI_868_M: BandEntry = BandEntry {
    band_id: 6,
    citation: "EN 300 220-2 V3.2.1 Table B.1 band M",
    freq_lo_khz: 868_000,
    freq_hi_khz: 868_600,
    ..ETSI_865_L
};

/// Wireless alarms, band A, 868.6-868.7 MHz: 10 mW e.r.p., 1 % (49).
pub static ETSI_868_ALARM_A: BandEntry = BandEntry {
    band_id: 7,
    citation: "EN 300 220-3-2 V1.1.1 band A",
    freq_lo_khz: 868_600,
    freq_hi_khz: 868_700,
    power_mw: 10.0,
    duty_cycle: Some(0.01),
    ..ETSI_863_K
};

/// Band N, 868.7-869.2 MHz: 25 mW e.r.p., 0.1 % (50).
pub static ETSI_868_N: BandEntry = BandEntry {
    band_id: 8,
    citation: "EN 300 220-2 V3.2.1 Table B.1 band N",
    freq_lo_khz: 868_700,
    freq_hi_khz: 869_200,
    ..ETSI_863_K
};

/// Social alarms, 869.200-869.250 MHz: 10 mW e.r.p., 0.1 % in an hour.
pub static ETSI_869_SOCIAL_ALARM: BandEntry = BandEntry {
    band_id: 9,
    citation: "EN 300 220-3-1 V2.1.1",
    freq_lo_khz: 869_200,
    freq_hi_khz: 869_250,
    power_mw: 10.0,
    ..ETSI_863_K
};

/// Wireless alarms, band B, 869.25-869.30 MHz: 10 mW e.r.p., 0.1 % (52).
pub static ETSI_869_ALARM_B: BandEntry = BandEntry {
    band_id: 10,
    citation: "EN 300 220-3-2 V1.1.1 band B",
    freq_lo_khz: 869_250,
    freq_hi_khz: 869_300,
    ..ETSI_869_SOCIAL_ALARM
};

/// Wireless alarms, band C, 869.30-869.40 MHz: 10 mW e.r.p., 1 % (53).
pub static ETSI_869_ALARM_C: BandEntry = BandEntry {
    band_id: 11,
    citation: "EN 300 220-3-2 V1.1.1 band C",
    freq_lo_khz: 869_300,
    freq_hi_khz: 869_400,
    duty_cycle: Some(0.01),
    ..ETSI_869_SOCIAL_ALARM
};

/// Band P, 869.40-869.65 MHz: 500 mW e.r.p., 10 % (54).
pub static ETSI_869_P: BandEntry = BandEntry {
    band_id: 12,
    citation: "EN 300 220-2 V3.2.1 Table B.1 band P",
    freq_lo_khz: 869_400,
    freq_hi_khz: 869_650,
    power_mw: 500.0,
    duty_cycle: Some(0.10),
    ..ETSI_863_K
};

/// Wireless alarms, band D, 869.65-869.70 MHz: 25 mW e.r.p., 10 % (55).
pub static ETSI_869_ALARM_D: BandEntry = BandEntry {
    band_id: 13,
    citation: "EN 300 220-3-2 V1.1.1 band D",
    freq_lo_khz: 869_650,
    freq_hi_khz: 869_700,
    power_mw: 25.0,
    duty_cycle: Some(0.10),
    ..ETSI_863_K
};

/// 869.7-870.0 MHz at 5 mW e.r.p., no duty cycle (56a; the second "P" row of Table B.1).
pub static ETSI_869_7_LOW: BandEntry = BandEntry {
    band_id: 14,
    citation: "EN 300 220-2 V3.2.1 Table B.1 (869.7-870 MHz, 5 mW)",
    freq_lo_khz: 869_700,
    freq_hi_khz: 870_000,
    power_mw: 5.0,
    duty_cycle: None,
    ..ETSI_863_K
};

/// Band Q, 869.7-870.0 MHz at 25 mW e.r.p., 1 % (56b).
pub static ETSI_869_7_Q: BandEntry = BandEntry {
    band_id: 15,
    citation: "EN 300 220-2 V3.2.1 Table B.1 band Q",
    power_mw: 25.0,
    duty_cycle: Some(0.01),
    ..ETSI_869_7_LOW
};

/// 2400-2483.5 MHz: 20 dBm e.i.r.p. (4.3.1.2, 4.3.2.2); non-FHSS 10 dBm/MHz (4.3.2.3);
/// non-adaptive equipment above 10 dBm a 10 % medium utilisation (4.3.1.6, 4.3.2.5).
pub static ETSI_2400: BandEntry = BandEntry {
    band_id: 20,
    authority: "ETSI",
    citation: "EN 300 328 V2.2.2 4.3.1.2, 4.3.2.2, 4.3.2.3, 4.3.2.5",
    freq_lo_khz: 2_400_000,
    freq_hi_khz: 2_483_500,
    power_mw: 100.0,
    power_ref: PowerRef::Eirp,
    psd_mw_per_mhz: Some(10.0),
    duty_cycle: Some(0.10),
    duty_cycle_above_mw: Some(10.0),
    ..BASE
};

// ── Face 2, North America: FCC ───────────────────────────────────────────────────

/// 902-928 MHz frequency hopping (15.247(a)(1)(i), (b)(2), (b)(4)): 1 W conducted with at
/// least 50 channels, at most 0.4 s on any channel in 20 s. A transmitter that has used
/// no other channel within 20 s is held to 15.249(a)'s 50 mV/m at 3 m (15.249(c)),
/// 0.75 mW e.i.r.p.
pub static FCC_902: BandEntry = BandEntry {
    band_id: 1,
    authority: "FCC",
    citation: "47 CFR 15.247(a)(1)(i), (b)(2), (b)(4); 15.249(a), (c)",
    freq_lo_khz: 902_000,
    freq_hi_khz: 928_000,
    power_mw: 1_000.0,
    power_ref: PowerRef::Conducted,
    hop_required: true,
    min_hop_set: Some(50),
    dwell_s: Some(0.4),
    dwell_window_s: Some(20.0),
    single_channel_power_mw: Some(0.75),
    single_channel_power_ref: Some(PowerRef::Eirp),
    single_channel_window_s: Some(20.0),
    ..BASE
};

/// 902-928 MHz digital modulation (15.247(a)(2), (b)(3)): 1 W conducted, a 6 dB
/// bandwidth of at least 500 kHz.
pub static FCC_902_DTS: BandEntry = BandEntry {
    band_id: 16,
    citation: "47 CFR 15.247(a)(2), (b)(3), (b)(4)",
    hop_required: false,
    min_hop_set: None,
    dwell_s: None,
    dwell_window_s: None,
    single_channel_power_mw: None,
    single_channel_power_ref: None,
    single_channel_window_s: None,
    min_bw_khz: Some(500),
    ..FCC_902
};

/// 2400-2483.5 MHz digital modulation (15.247(a)(2), (b)(3)): 1 W conducted, a 6 dB
/// bandwidth of at least 500 kHz.
pub static FCC_2400_DTS: BandEntry = BandEntry {
    band_id: 21,
    freq_lo_khz: 2_400_000,
    freq_hi_khz: 2_483_500,
    ..FCC_902_DTS
};

/// 2400-2483.5 MHz under 15.249(a): 50 mV/m at 3 m, 0.75 mW e.i.r.p.
pub static FCC_2400_249: BandEntry = BandEntry {
    band_id: 22,
    authority: "FCC",
    citation: "47 CFR 15.249(a), (c)",
    freq_lo_khz: 2_400_000,
    freq_hi_khz: 2_483_500,
    power_mw: 0.75,
    power_ref: PowerRef::Eirp,
    ..BASE
};

// ── Face 7, eastern Australia: ACMA (not yet checked against the class licence) ───────

/// ACMA 915-928 MHz, 1 W e.i.r.p.
pub static ACMA_915: BandEntry = BandEntry {
    band_id: 4,
    authority: "ACMA",
    citation: "Radiocommunications (Low Interference Potential Devices) Class Licence 2015",
    freq_lo_khz: 915_000,
    freq_hi_khz: 928_000,
    power_mw: 1_000.0,
    power_ref: PowerRef::Eirp,
    ..BASE
};

/// ACMA 2400-2483.5 MHz digital modulation, 4 W e.i.r.p., a 6 dB bandwidth of at least
/// 500 kHz.
pub static ACMA_2400: BandEntry = BandEntry {
    band_id: 23,
    freq_lo_khz: 2_400_000,
    freq_hi_khz: 2_483_500,
    power_mw: 4_000.0,
    min_bw_khz: Some(500),
    ..ACMA_915
};

// ── The exception overlay's own entries (draft Table 7; not yet checked) ────────────

/// OFCA (Hong Kong) 920-925 MHz, 100 mW e.i.r.p.
pub static OFCA_920: BandEntry = BandEntry {
    band_id: 30,
    authority: "OFCA",
    citation: "draft-hanley-rsdggs-02 Table 7",
    freq_lo_khz: 920_000,
    freq_hi_khz: 925_000,
    power_mw: 100.0,
    power_ref: PowerRef::Eirp,
    exception: true,
    ..BASE
};

/// IMDA (Singapore) 920-925 MHz, 500 mW e.i.r.p.
pub static IMDA_920: BandEntry = BandEntry {
    band_id: 31,
    authority: "IMDA",
    power_mw: 500.0,
    ..OFCA_920
};

/// The ETSI entries, as they apply on face 1 and in its overlay locations.
pub static ETSI_BANDS: &[&BandEntry] = &[
    &ETSI_433,
    &ETSI_863_K,
    &ETSI_865_L,
    &ETSI_868_M,
    &ETSI_868_ALARM_A,
    &ETSI_868_N,
    &ETSI_869_SOCIAL_ALARM,
    &ETSI_869_ALARM_B,
    &ETSI_869_ALARM_C,
    &ETSI_869_P,
    &ETSI_869_ALARM_D,
    &ETSI_869_7_LOW,
    &ETSI_869_7_Q,
    &ETSI_2400,
];

/// The FCC entries.
pub static FCC_BANDS: &[&BandEntry] = &[&FCC_902, &FCC_902_DTS, &FCC_2400_DTS, &FCC_2400_249];

/// The ACMA entries.
pub static ACMA_BANDS: &[&BandEntry] = &[&ACMA_915, &ACMA_2400];

/// Face-level entries: the face's dominant regime. Faces not listed have none.
static FACE_TABLE: &[(u8, &[&BandEntry])] = &[(1, ETSI_BANDS), (2, FCC_BANDS), (7, ACMA_BANDS)];

/// The exception overlay (draft Table 7). The boxes approximate each territory; a cell at
/// the exception's RSL belongs to it if the cell's centre is in its box. Where the
/// authority's figures aren't in the database, `bands` is empty: no band is known to be
/// available there.
pub static EXCEPTIONS: &[ExceptionEntry] = &[
    ExceptionEntry {
        location:  "Hong Kong",
        authority: "OFCA",
        face:      Some(3),
        triangles: None,
        bbox:      [22.15, 22.57, 113.82, 114.45],
        rsl:       5,
        bands:     &[&OFCA_920],
    },
    ExceptionEntry {
        location:  "Macau",
        authority: "DSRT",
        face:      Some(3),
        triangles: None,
        bbox:      [22.10, 22.22, 113.52, 113.60],
        rsl:       5,
        bands:     ETSI_BANDS,
    },
    ExceptionEntry {
        location:  "Singapore",
        authority: "IMDA",
        face:      Some(3),
        triangles: None,
        bbox:      [1.15, 1.48, 103.60, 104.10],
        rsl:       5,
        bands:     &[&IMDA_920],
    },
    ExceptionEntry {
        location:  "British Virgin Islands",
        authority: "ICTA",
        face:      Some(2),
        triangles: None,
        bbox:      [18.30, 18.80, -64.90, -64.25],
        rsl:       5,
        bands:     &[],
    },
    ExceptionEntry {
        location:  "French Guiana",
        authority: "ARCEP",
        face:      None,
        triangles: None,
        bbox:      [2.10, 5.80, -54.60, -51.60],
        rsl:       4,
        bands:     ETSI_BANDS,
    },
    ExceptionEntry {
        location:  "Ceuta",
        authority: "ETSI",
        face:      None,
        triangles: None,
        bbox:      [35.86, 35.92, -5.39, -5.27],
        rsl:       6,
        bands:     ETSI_BANDS,
    },
    ExceptionEntry {
        location:  "Melilla",
        authority: "ETSI",
        face:      None,
        triangles: None,
        bbox:      [35.26, 35.32, -2.97, -2.92],
        rsl:       6,
        bands:     ETSI_BANDS,
    },
    ExceptionEntry {
        location:  "Guam",
        authority: "FCC",
        face:      None,
        triangles: None,
        bbox:      [13.20, 13.70, 144.60, 145.00],
        rsl:       4,
        bands:     FCC_BANDS,
    },
    ExceptionEntry {
        location:  "Northern Mariana Islands",
        authority: "FCC",
        face:      None,
        triangles: None,
        bbox:      [14.10, 20.60, 144.90, 146.10],
        rsl:       4,
        bands:     FCC_BANDS,
    },
    ExceptionEntry {
        location:  "Alaska / Yukon",
        authority: "FCC, ISED",
        face:      Some(11),
        triangles: Some(&[2, 3, 4]),
        bbox:      [-90.0, 90.0, -180.0, 180.0],
        rsl:       2,
        bands:     FCC_BANDS,
    },
    ExceptionEntry {
        location:  "Russian Far East",
        authority: "Roskomnadzor",
        face:      Some(11),
        triangles: Some(&[0]),
        bbox:      [-90.0, 90.0, -180.0, 180.0],
        rsl:       2,
        bands:     &[],
    },
    ExceptionEntry {
        // East of the US-Russia border, which runs between the Diomede Islands near
        // 169° W.
        location:  "Alaska North Slope, Canadian Arctic",
        authority: "FCC, ISED",
        face:      Some(11),
        triangles: Some(&[0]),
        bbox:      [50.0, 90.0, -169.0, -60.0],
        rsl:       5,
        bands:     FCC_BANDS,
    },
    ExceptionEntry {
        location:  "French Polynesia",
        authority: "ARCEP",
        face:      None,
        triangles: None,
        bbox:      [-28.0, -7.0, -155.0, -134.0],
        rsl:       4,
        bands:     ETSI_BANDS,
    },
    ExceptionEntry {
        location:  "New Caledonia",
        authority: "ARCEP",
        face:      None,
        triangles: None,
        bbox:      [-23.0, -19.5, 163.5, 168.2],
        rsl:       4,
        bands:     ETSI_BANDS,
    },
    ExceptionEntry {
        location:  "Wallis and Futuna",
        authority: "ARCEP",
        face:      None,
        triangles: None,
        bbox:      [-14.4, -13.2, -178.3, -176.1],
        rsl:       4,
        bands:     ETSI_BANDS,
    },
];

/// The entry with `band_id` on `face`, at face level.
pub fn lookup_face(face: u8, band_id: u32) -> Option<&'static BandEntry> {
    bands_for_face(face).find(|e| e.band_id == band_id)
}

/// A face's face-level entries.
pub fn bands_for_face(face: u8) -> impl Iterator<Item = &'static BandEntry> {
    FACE_TABLE
        .iter()
        .filter(move |&&(f, _)| f == face)
        .flat_map(|&(_, bands)| bands.iter().copied())
}

// suppress unused import warning for ModulationType
const _: ModulationType = ModulationType::Any;
