use rsdggs::constants::{FACE_CENTERS, FACE_PENTAGON_VERTS};
use rsdggs::encode;

fn dot(a: [f64; 3], b: [f64; 3]) -> f64 {
    a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
}

fn cross(a: [f64; 3], b: [f64; 3]) -> [f64; 3] {
    [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]
}

/// Faces of reference cities under the orientation of draft section 4.3. The low two
/// bits of each face number are the ITU Region of the face's main population (0: none).
#[test]
fn reference_cities() {
    let cases = [
        ("London", 51.51, -0.13, 1),
        ("Moscow", 55.76, 37.62, 1),
        ("Lisbon", 38.72, -9.14, 1),
        ("New York", 40.71, -74.01, 2),
        ("Los Angeles", 34.05, -118.24, 2),
        ("Mexico City", 19.43, -99.13, 2),
        ("Delhi", 28.61, 77.21, 3),
        ("Beijing", 39.90, 116.40, 3),
        ("Tokyo", 35.68, 139.69, 3),
        ("South Pole", -90.0, 0.0, 0),
        ("Auckland", -36.85, 174.76, 0),
        ("Cape Town", -33.92, 18.42, 4),
        ("Nairobi", -1.29, 36.82, 5),
        ("Sao Paulo", -23.55, -46.63, 6),
        ("Sydney", -33.87, 151.21, 7),
        ("Perth", -31.95, 115.86, 8),
        ("Lagos", 6.52, 3.38, 9),
        ("Honolulu", 21.31, -157.86, 10),
        ("Sapporo", 43.06, 141.35, 11),
    ];
    for (name, lat, lon, face) in cases {
        assert_eq!(encode(lat, lon, 1).unwrap().face, face, "{name}");
    }
}

/// Every face's vertices run counter-clockwise as seen from outside the sphere.
#[test]
fn vertices_counter_clockwise() {
    for f in 0..12 {
        let v = FACE_PENTAGON_VERTS[f];
        for k in 0..5 {
            assert!(
                dot(cross(v[k], v[(k + 1) % 5]), FACE_CENTERS[f]) > 0.0,
                "face {f} edge {k}"
            );
        }
    }
}
