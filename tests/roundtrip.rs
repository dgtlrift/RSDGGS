use approx::assert_abs_diff_eq;
use rsdggs::{decode, encode, decode::cell_center};

/// Encode then decode; check the original point is inside the bounding cell's bbox.
fn roundtrip_check(lat: f64, lon: f64, depth: usize) {
    let idx = encode(lat, lon, depth).expect("encode failed");
    let cell = decode(&idx).expect("decode failed");

    // The original point should be within (or very close to) the bbox.
    let [lat_min, lat_max, lon_min, lon_max] = cell.bbox;
    assert!(
        lat >= lat_min - 0.01 && lat <= lat_max + 0.01,
        "lat {lat} out of bbox [{lat_min}, {lat_max}] at depth {depth}"
    );
    assert!(
        lon >= lon_min - 0.01 && lon <= lon_max + 0.01,
        "lon {lon} out of bbox [{lon_min}, {lon_max}] at depth {depth}"
    );
}

#[test]
fn anchor_point_face2() {
    // 39°N 98°W is the anchor for Face 2 (N. America)
    let idx = encode(39.0, -98.0, 2).unwrap();
    assert_eq!(idx.face, 2, "39°N 98°W should be in face 2");
}

#[test]
fn roundtrip_depths_1_to_8() {
    let cases = [
        (39.0, -98.0),   // Kansas (F2 anchor)
        (51.5, -0.1),    // London (F1 Europe)
        (-33.9, 151.2),  // Sydney (F11 Oceania)
        (35.7, 139.7),   // Tokyo (F3 E.Asia)
        (-23.5, -46.6),  // São Paulo (F8 S.America)
        (0.0, 0.0),      // Gulf of Guinea
    ];
    for (lat, lon) in cases {
        for depth in 1..=8 {
            roundtrip_check(lat, lon, depth);
        }
    }
}

#[test]
fn cell_shrinks_with_depth() {
    let lat = 39.0;
    let lon = -98.0;
    let mut prev_area = f64::INFINITY;
    for depth in 1..=8 {
        let idx = encode(lat, lon, depth).unwrap();
        let cell = decode(&idx).unwrap();
        let [lat_min, lat_max, lon_min, lon_max] = cell.bbox;
        let area = (lat_max - lat_min) * (lon_max - lon_min);
        if depth > 1 {
            assert!(area <= prev_area * 1.1, "cell did not shrink at depth {depth}");
        }
        prev_area = area;
    }
}

#[test]
fn cell_center_near_input() {
    let lat = 39.0;
    let lon = -98.0;
    let idx = encode(lat, lon, 6).unwrap();
    let cell = decode(&idx).unwrap();
    let (clat, clon) = cell_center(&cell);
    // At depth 6 (~1 km), centroid should be within ~1° of input
    assert_abs_diff_eq!(clat, lat, epsilon = 1.0);
    assert_abs_diff_eq!(clon, lon, epsilon = 1.0);
}

#[test]
fn regulatory_acma_face10() {
    use rsdggs::regulatory::lookup;
    use rsdggs::Body;
    let entry = lookup(10, Body::Earth, 4).unwrap();
    assert_eq!(entry.authority, "ACMA");
    assert_eq!(entry.freq_lo_khz, 915_000);
}

#[test]
fn regulatory_fcc_face2() {
    use rsdggs::regulatory::lookup;
    use rsdggs::Body;
    let entry = lookup(2, Body::Earth, 1).unwrap();
    assert_eq!(entry.authority, "FCC");
    assert_eq!(entry.freq_lo_khz, 902_000);
    assert!(entry.hop_required);
    assert_eq!(entry.min_hop_set, Some(50));
}

#[test]
fn regulatory_etsi_face1() {
    use rsdggs::regulatory::lookup;
    use rsdggs::Body;
    let e433 = lookup(1, Body::Earth, 2).unwrap();
    assert_eq!(e433.authority, "ETSI");
    assert_eq!(e433.duty_cycle, Some(0.10));

    let e868 = lookup(1, Body::Earth, 3).unwrap();
    assert_eq!(e868.freq_lo_khz, 863_000);
}

#[test]
fn regulatory_missing_returns_err() {
    use rsdggs::regulatory::lookup;
    use rsdggs::Body;
    assert!(lookup(0, Body::Earth, 999).is_err());
}
