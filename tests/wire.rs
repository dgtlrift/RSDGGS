use rsdggs::{encode, from_wire, to_wire, truncate, wire::levels_for_depth, Error};

const CASES: [(f64, f64); 6] = [
    (39.0, -98.0),
    (51.5, -0.1),
    (-33.9, 151.2),
    (35.7, 139.7),
    (-23.5, -46.6),
    (0.0, 0.0),
];

/// Keep the first `depth` octets of a wire value.
fn drop_octets(wire: u64, depth: usize) -> u64 {
    if depth == 8 { wire } else { wire & !(u64::MAX >> (8 * depth)) }
}

#[test]
fn levels_per_depth() {
    let levels: Vec<usize> = (1..=8).map(levels_for_depth).collect();
    assert_eq!(levels, [0, 2, 6, 10, 14, 18, 22, 26]);
}

#[test]
fn every_bit_of_eight_octets_is_used() {
    for (lat, lon) in CASES {
        let idx = encode(lat, lon, 8).unwrap();
        assert_eq!(idx.levels.len(), 26);
        assert_eq!(idx.depth_octets(), 8);
    }
}

#[test]
fn wire_roundtrip_all_depths() {
    for (lat, lon) in CASES {
        for depth in 1..=8 {
            let idx = encode(lat, lon, depth).unwrap();
            let back = from_wire(to_wire(&idx), depth).unwrap();
            assert_eq!(back.face, idx.face);
            assert_eq!(back.triangle, idx.triangle);
            assert_eq!(back.levels, idx.levels);
        }
    }
}

/// With a 4-bit triangle field no level straddles an octet boundary, so
/// dropping trailing octets is exactly truncation (draft §5.4).
#[test]
fn dropping_octets_is_truncation() {
    for (lat, lon) in CASES {
        let full = encode(lat, lon, 8).unwrap();
        let wire = to_wire(&full);
        for depth in 1..=8 {
            let cut = drop_octets(wire, depth);
            assert_eq!(cut, to_wire(&truncate(&full, depth)), "depth {depth}");
            assert_eq!(cut, to_wire(&encode(lat, lon, depth).unwrap()), "depth {depth}");
        }
    }
}

#[test]
fn reserved_triangle_and_face_values_are_rejected() {
    for tri in 5u64..=15 {
        let wire = (0x02u64 << 56) | (tri << 52);
        assert!(matches!(from_wire(wire, 2), Err(Error::InvalidTriangle(t)) if u64::from(t) == tri));
    }
    for face in 12u64..=15 {
        assert!(matches!(from_wire(face << 56, 1), Err(Error::InvalidFace(_))));
    }
}
