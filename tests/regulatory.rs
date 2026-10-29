//! The regulatory database (draft sections 8 and 9): face-level entries, the exception
//! overlay at its resolution sufficiency levels, and the entries' figures.

use rsdggs::regulatory::{bands_for_index, bands_for_location, earth, exception_for_index};
use rsdggs::types::PowerRef;
use rsdggs::{Error, encode};

fn authorities(lat: f64, lon: f64) -> Vec<&'static str> {
    let mut a: Vec<&str> = bands_for_location(lat, lon)
        .unwrap()
        .iter()
        .map(|b| b.authority)
        .collect();
    a.dedup();
    a
}

fn exception(lat: f64, lon: f64) -> Option<&'static str> {
    exception_for_index(&encode(lat, lon, 8).unwrap())
        .unwrap()
        .map(|e| e.location)
}

#[test]
fn faces_give_their_regime() {
    assert_eq!(authorities(52.0, 4.0), ["ETSI"]); // Delft
    assert_eq!(authorities(40.71, -74.0), ["FCC"]); // New York
    assert_eq!(authorities(-33.87, 151.21), ["ACMA"]); // Sydney
    assert!(authorities(-23.55, -46.63).is_empty(), "face 6 has no entries yet");
}

#[test]
fn the_exception_overlay() {
    for (lat, lon, place) in [
        (22.30, 114.17, "Hong Kong"),
        (1.35, 103.82, "Singapore"),
        (22.19, 113.54, "Macau"),
        (35.89, -5.32, "Ceuta"),
        (35.29, -2.94, "Melilla"),
        (13.45, 144.79, "Guam"),
        (61.22, -149.90, "Alaska / Yukon"),
        (65.75, -168.93, "Alaska North Slope, Canadian Arctic"), // Little Diomede
        (65.78, -169.08, "Russian Far East"),                    // Big Diomede
        (4.93, -52.33, "French Guiana"),
        (-17.53, -149.57, "French Polynesia"),
        (18.43, -64.62, "British Virgin Islands"),
    ] {
        assert_eq!(exception(lat, lon), Some(place), "{lat}, {lon}");
    }
    assert_eq!(exception(52.0, 4.0), None);
    assert_eq!(authorities(22.30, 114.17), ["OFCA"]);
    assert_eq!(authorities(13.45, 144.79), ["FCC"]);
    assert!(authorities(65.78, -169.08).is_empty(), "no Roskomnadzor entries yet");
}

/// A face with an exception needs the exception's RSL before the lookup can answer.
#[test]
fn a_short_index_is_refused_where_an_exception_may_apply() {
    let short = encode(22.30, 114.17, 3).unwrap();
    assert!(matches!(
        bands_for_index(&short),
        Err(Error::InsufficientResolution { needed: 5 })
    ));
    assert!(bands_for_index(&encode(52.0, 4.0, 3).unwrap()).is_ok());
}

/// EN 300 220-2 Table B.1 and EN 300 220-3-1, -3-2: the 863-870 MHz sub-bands tile the
/// band, each with its own power and duty cycle.
#[test]
fn the_etsi_868_sub_bands() {
    let expect = [
        (863_000, 865_000, 25.0, Some(0.001)),
        (865_000, 868_000, 25.0, Some(0.01)),
        (868_000, 868_600, 25.0, Some(0.01)),
        (868_600, 868_700, 10.0, Some(0.01)),
        (868_700, 869_200, 25.0, Some(0.001)),
        (869_200, 869_250, 10.0, Some(0.001)),
        (869_250, 869_300, 10.0, Some(0.001)),
        (869_300, 869_400, 10.0, Some(0.01)),
        (869_400, 869_650, 500.0, Some(0.10)),
        (869_650, 869_700, 25.0, Some(0.10)),
        (869_700, 870_000, 5.0, None),
        (869_700, 870_000, 25.0, Some(0.01)),
    ];
    let got: Vec<_> = earth::ETSI_BANDS
        .iter()
        .filter(|b| (863_000..=870_000).contains(&b.freq_lo_khz))
        .map(|b| (b.freq_lo_khz, b.freq_hi_khz, b.power_mw, b.duty_cycle))
        .collect();
    assert_eq!(got, expect);
    assert!(earth::ETSI_BANDS
        .iter()
        .filter(|b| b.freq_lo_khz < 1_000_000)
        .all(|b| b.power_ref == PowerRef::Erp));
}

/// 47 CFR 15.247 and 15.249 for 902-928 MHz.
#[test]
fn the_fcc_902_entries() {
    let h = &earth::FCC_902;
    assert_eq!((h.power_mw, h.power_ref), (1000.0, PowerRef::Conducted));
    assert_eq!((h.min_hop_set, h.dwell_s, h.dwell_window_s), (Some(50), Some(0.4), Some(20.0)));
    assert_eq!(
        (h.single_channel_power_mw, h.single_channel_window_s),
        (Some(0.75), Some(20.0))
    );
    // 50 mV/m at 3 m: EIRP = (E·d)² / 30 = 0.75 mW.
    let eirp_mw = (0.05f32 * 3.0).powi(2) / 30.0 * 1000.0;
    assert!((eirp_mw - 0.75).abs() < 1e-6);
    assert_eq!(earth::FCC_902_DTS.min_bw_khz, Some(500));
}
