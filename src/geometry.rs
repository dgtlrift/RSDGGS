//! Cell geometry for drawing and covering an area: a face's pentagon, a cell's children,
//! a cap that bounds a cell, and the cells at a level that touch a latitude and longitude
//! box. Everything follows the draft's section 6: the faces of section 6.1, the five
//! triangles of a face of section 6.2 (the face center, vertex k and vertex k + 1), and
//! the subdivision of section 6.3, `mid(A, B) = normalize(A + B)` with child 0 the apex
//! sub-triangle, 1 the left base, 2 the right base and 3 the central inverted one. These
//! are API additions: encoding, decoding and the wire format are unchanged.

use crate::{
    Error,
    constants::{FACE_CENTERS, FACE_PENTAGON_VERTS},
    types::{Body, RsdggsIndex},
    wire::levels_for_depth,
};

/// A triangle's corners: apex, left, right.
type Tri = ([f64; 3], [f64; 3], [f64; 3]);

/// The most subdivision levels an index holds (8 octets).
pub const MAX_LEVELS: usize = levels_for_depth(8);

fn dot(a: [f64; 3], b: [f64; 3]) -> f64 {
    a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
}

fn normalize(v: [f64; 3]) -> [f64; 3] {
    let len = libm::sqrt(dot(v, v));
    [v[0] / len, v[1] / len, v[2] / len]
}

fn mid(a: [f64; 3], b: [f64; 3]) -> [f64; 3] {
    normalize([a[0] + b[0], a[1] + b[1], a[2] + b[2]])
}

/// The angle between two unit vectors, radians: `atan2(|a × b|, a · b)`, accurate for the
/// deepest cells (about 1e-8 rad), where `acos` of the dot product is not.
fn angle(a: [f64; 3], b: [f64; 3]) -> f64 {
    let c = [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ];
    libm::atan2(libm::sqrt(dot(c, c)), dot(a, b))
}

/// A unit vector as (latitude, longitude) in degrees.
pub fn latlon(v: [f64; 3]) -> (f64, f64) {
    (
        libm::asin(v[2].clamp(-1.0, 1.0)).to_degrees(),
        libm::atan2(v[1], v[0]).to_degrees(),
    )
}

/// A latitude and longitude in degrees as a unit vector.
pub fn unit(lat_deg: f64, lon_deg: f64) -> [f64; 3] {
    crate::encode::latlon_to_vec(lat_deg, lon_deg)
}

/// A face's five pentagon vertices, in the order its triangles use them: triangle k has
/// corners the face center, vertex k and vertex k + 1 (mod 5).
pub fn face_pentagon(face: u8) -> Result<[[f64; 3]; 5], Error> {
    FACE_PENTAGON_VERTS
        .get(usize::from(face))
        .copied()
        .ok_or(Error::InvalidFace(face))
}

/// The children of a cell, in index order: a face's five triangles (a 1-octet index has
/// no triangle), or a triangle's four sub-triangles, child 0 (apex) to 3 (central
/// inverted).
///
/// # Errors
///
/// [`Error::InvalidFace`], [`Error::InvalidTriangle`] or [`Error::InvalidLevel`] for a bad
/// index, and [`Error::InvalidDepth`] for one already at [`MAX_LEVELS`].
pub fn children(idx: &RsdggsIndex) -> Result<Vec<RsdggsIndex>, Error> {
    face_pentagon(idx.face)?;
    let Some(triangle) = idx.triangle else {
        return Ok((0..5)
            .map(|t| RsdggsIndex {
                triangle: Some(t),
                levels: Vec::new(),
                ..idx.clone()
            })
            .collect());
    };
    if triangle >= 5 {
        return Err(Error::InvalidTriangle(triangle));
    }
    if let Some(&bad) = idx.levels.iter().find(|&&c| c > 3) {
        return Err(Error::InvalidLevel(bad));
    }
    if idx.levels.len() >= MAX_LEVELS {
        return Err(Error::InvalidDepth(idx.levels.len() + 1));
    }
    Ok((0..4)
        .map(|c| {
            let mut levels = idx.levels.clone();
            levels.push(c);
            RsdggsIndex {
                levels,
                ..idx.clone()
            }
        })
        .collect())
}

/// A triangle's corners (apex, left, right), as `decode` gives them.
fn corners(face: u8, triangle: u8) -> Tri {
    let v = &FACE_PENTAGON_VERTS[usize::from(face)];
    let k = usize::from(triangle);
    (FACE_CENTERS[usize::from(face)], v[k], v[(k + 1) % 5])
}

fn child(c: u8, (a, l, r): Tri) -> Tri {
    let (m_al, m_ar, m_lr) = (mid(a, l), mid(a, r), mid(l, r));
    match c {
        0 => (a, m_al, m_ar),
        1 => (m_al, l, m_lr),
        2 => (m_ar, m_lr, r),
        _ => (m_lr, m_ar, m_al),
    }
}

/// A spherical cap, its center and angular radius in radians, that holds the whole cell:
/// the face's pentagon, or the triangle with its great-circle edges (a cap under a
/// hemisphere is convex, so holding the corners holds the edges).
///
/// # Errors
///
/// As [`crate::decode()`].
pub fn cap(idx: &RsdggsIndex) -> Result<([f64; 3], f64), Error> {
    let corners: Vec<[f64; 3]> = match idx.triangle {
        None => face_pentagon(idx.face)?.to_vec(),
        Some(_) => crate::decode(idx)?.vertices.to_vec(),
    };
    let sum = corners
        .iter()
        .fold([0.0; 3], |s, v| [s[0] + v[0], s[1] + v[1], s[2] + v[2]]);
    let center = normalize(sum);
    let radius = corners
        .iter()
        .map(|&v| angle(center, v))
        .fold(0.0, f64::max);
    Ok((center, radius))
}

/// A cap that holds a latitude and longitude box `[lat_min, lat_max, lon_min, lon_max]`
/// (degrees; `lon_min > lon_max` crosses the antimeridian): the box's middle, out to the
/// farthest of points along its edges, with a margin for the edges between them.
fn box_cap(bbox: [f64; 4]) -> ([f64; 3], f64) {
    let [s, n, w, e] = bbox;
    let span = if e >= w { e - w } else { e + 360.0 - w };
    if n - s >= 90.0 || span >= 180.0 {
        return ([0.0, 0.0, 1.0], core::f64::consts::PI);
    }
    let center = unit((s + n) / 2.0, w + span / 2.0);
    let mut radius: f64 = 0.0;
    const STEPS: u32 = 16;
    for i in 0..=STEPS {
        let f = f64::from(i) / f64::from(STEPS);
        let lat = s + (n - s) * f;
        let lon = w + span * f;
        for p in [
            unit(s, lon),
            unit(n, lon),
            unit(lat, w),
            unit(lat, w + span),
        ] {
            radius = radius.max(angle(center, p));
        }
    }
    // Between samples an edge strays from the chord by at most a sample's spacing.
    let step = (n - s).max(span).to_radians() / f64::from(STEPS);
    (center, radius + step)
}

/// The cells with `levels` subdivision levels (0 for a face's five triangles) that may
/// touch the box `[lat_min, lat_max, lon_min, lon_max]` in degrees (`lon_min > lon_max`
/// crosses the antimeridian), in index order. Each cell's cap is tested against the box's,
/// so every cell that touches the box is returned, and a few near it may be too.
///
/// # Errors
///
/// [`Error::InvalidDepth`] for `levels` above [`MAX_LEVELS`].
pub fn cover(bbox: [f64; 4], levels: usize) -> Result<Vec<RsdggsIndex>, Error> {
    if levels > MAX_LEVELS {
        return Err(Error::InvalidDepth(levels));
    }
    let (bc, br) = box_cap(bbox);
    let hits = |t: Tri| {
        let center = normalize([
            t.0[0] + t.1[0] + t.2[0],
            t.0[1] + t.1[1] + t.2[1],
            t.0[2] + t.1[2] + t.2[2],
        ]);
        let r = angle(center, t.0)
            .max(angle(center, t.1))
            .max(angle(center, t.2));
        angle(center, bc) <= r + br
    };
    let mut out = Vec::new();
    let mut stack: Vec<(u8, u8, Vec<u8>, Tri)> = Vec::new();
    for face in (0..12u8).rev() {
        for t in (0..5u8).rev() {
            stack.push((face, t, Vec::new(), corners(face, t)));
        }
    }
    while let Some((face, triangle, path, tri)) = stack.pop() {
        if !hits(tri) {
            continue;
        }
        if path.len() == levels {
            out.push(RsdggsIndex {
                body: Body::Earth,
                face,
                triangle: Some(triangle),
                levels: path,
            });
            continue;
        }
        for c in (0..4u8).rev() {
            let mut p = path.clone();
            p.push(c);
            stack.push((face, triangle, p, child(c, tri)));
        }
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::encode;

    #[test]
    fn a_face_has_five_children_and_a_triangle_four() {
        let face = encode(46.5, 7.0, 1).unwrap();
        let tris = children(&face).unwrap();
        assert_eq!(
            tris.iter().map(|c| c.triangle).collect::<Vec<_>>(),
            (0..5).map(Some).collect::<Vec<_>>()
        );
        let kids = children(&tris[2]).unwrap();
        assert_eq!(
            kids.iter().map(|c| c.levels.clone()).collect::<Vec<_>>(),
            [[0], [1], [2], [3]]
        );
        let deepest = RsdggsIndex {
            levels: vec![0; MAX_LEVELS],
            ..tris[0].clone()
        };
        assert!(matches!(children(&deepest), Err(Error::InvalidDepth(_))));
        assert!(matches!(face_pentagon(12), Err(Error::InvalidFace(12))));
    }

    /// A point's own cell at each level is among its parent's children, and inside the
    /// parent's cap; `cover` round a point returns the point's cell.
    #[test]
    fn children_cap_and_cover_agree_with_encode() {
        for &(lat, lon) in &[
            (46.5, 7.0),
            (-33.9, 151.2),
            (0.0, 179.99),
            (89.0, 10.0),
            (-60.0, -45.0),
        ] {
            let p = unit(lat, lon);
            for depth in 2..=8 {
                let cell = encode(lat, lon, depth).unwrap();
                let (c, r) = cap(&cell).unwrap();
                assert!(angle(c, p) <= r + 1e-12, "{lat},{lon} depth {depth}");
                if let Some(&last) = cell.levels.last() {
                    let parent = RsdggsIndex {
                        levels: cell.levels[..cell.levels.len() - 1].to_vec(),
                        ..cell.clone()
                    };
                    assert_eq!(children(&parent).unwrap()[usize::from(last)], cell);
                }
            }
            for levels in [0, 1, 3, 6] {
                let d = 0.01;
                let found = cover(
                    [lat - d, (lat + d).min(90.0), lon - d, (lon + d).min(180.0)],
                    levels,
                )
                .unwrap();
                let depth = (2..=8).find(|&o| levels_for_depth(o) >= levels).unwrap();
                let mut own = encode(lat, lon, depth).unwrap();
                own.levels.truncate(levels);
                assert!(
                    found.contains(&own),
                    "{lat},{lon} levels {levels}: {} cells",
                    found.len()
                );
                assert!(
                    found.len() < 40,
                    "{lat},{lon} levels {levels}: {} cells",
                    found.len()
                );
            }
        }
    }

    #[test]
    fn cover_handles_the_whole_globe_and_the_antimeridian() {
        assert_eq!(cover([-90.0, 90.0, -180.0, 180.0], 0).unwrap().len(), 60);
        assert_eq!(cover([-90.0, 90.0, -180.0, 180.0], 1).unwrap().len(), 240);
        let across = cover([-1.0, 1.0, 179.0, -179.0], 4).unwrap();
        let p = encode(0.0, 179.5, 4).unwrap();
        let mut own = p.clone();
        own.levels.truncate(4);
        assert!(across.contains(&own));
        assert!(matches!(
            cover([0.0, 1.0, 0.0, 1.0], MAX_LEVELS + 1),
            Err(Error::InvalidDepth(_))
        ));
    }

    #[test]
    fn latlon_and_unit_round_trip() {
        let (lat, lon) = latlon(unit(-12.25, 130.5));
        assert!((lat + 12.25).abs() < 1e-9 && (lon - 130.5).abs() < 1e-9);
    }
}
