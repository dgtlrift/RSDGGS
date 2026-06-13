use crate::{
    constants::{FACE_CENTERS, FACE_PENTAGON_VERTS},
    types::{Body, RsdggsIndex},
    Error,
};

fn dot(a: [f64; 3], b: [f64; 3]) -> f64 {
    a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
}

fn cross(a: [f64; 3], b: [f64; 3]) -> [f64; 3] {
    [
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0],
    ]
}

fn normalize(v: [f64; 3]) -> [f64; 3] {
    let len = libm::sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2]);
    [v[0]/len, v[1]/len, v[2]/len]
}

fn midpoint(a: [f64; 3], b: [f64; 3]) -> [f64; 3] {
    normalize([a[0]+b[0], a[1]+b[1], a[2]+b[2]])
}

/// True if `p` is on the same side of great-circle arc A→B as `ref_pt`.
/// Orientation-independent: works for both CW and CCW triangles.
#[inline]
fn same_side(a: [f64; 3], b: [f64; 3], ref_pt: [f64; 3], p: [f64; 3]) -> bool {
    let n = cross(a, b);
    dot(n, ref_pt) * dot(n, p) >= 0.0
}

/// True if P is inside spherical triangle (a, b, c).
fn in_triangle(a: [f64; 3], b: [f64; 3], c: [f64; 3], p: [f64; 3]) -> bool {
    same_side(a, b, c, p) && same_side(b, c, a, p) && same_side(c, a, b, p)
}

/// Convert lat/lon (degrees) to unit Cartesian vector.
pub(crate) fn latlon_to_vec(lat_deg: f64, lon_deg: f64) -> [f64; 3] {
    let lat = lat_deg.to_radians();
    let lon = lon_deg.to_radians();
    let clat = libm::cos(lat);
    [clat * libm::cos(lon), clat * libm::sin(lon), libm::sin(lat)]
}

/// Step 2: find which face contains P (max dot with face center).
fn assign_face(p: [f64; 3]) -> u8 {
    FACE_CENTERS
        .iter()
        .enumerate()
        .max_by(|(_, a), (_, b)| dot(p, **a).partial_cmp(&dot(p, **b)).unwrap())
        .map(|(i, _)| i as u8)
        .unwrap()
}

/// Step 3: find which of the 5 triangular sectors within `face` contains P.
/// Sector k = (face_center, pent_verts[k], pent_verts[(k+1)%5]).
fn assign_triangle(face: u8, p: [f64; 3]) -> u8 {
    let verts = &FACE_PENTAGON_VERTS[face as usize];
    let fc = FACE_CENTERS[face as usize];
    for k in 0..5usize {
        let vk  = verts[k];
        let vk1 = verts[(k + 1) % 5];
        if in_triangle(fc, vk, vk1, p) {
            return k as u8;
        }
    }
    // Boundary fallback: nearest sector centroid.
    (0..5usize)
        .max_by(|&k1, &k2| {
            let c1 = normalize([fc[0]+verts[k1][0]+verts[(k1+1)%5][0],
                                 fc[1]+verts[k1][1]+verts[(k1+1)%5][1],
                                 fc[2]+verts[k1][2]+verts[(k1+1)%5][2]]);
            let c2 = normalize([fc[0]+verts[k2][0]+verts[(k2+1)%5][0],
                                 fc[1]+verts[k2][1]+verts[(k2+1)%5][1],
                                 fc[2]+verts[k2][2]+verts[(k2+1)%5][2]]);
            dot(p, c1).partial_cmp(&dot(p, c2)).unwrap()
        })
        .unwrap() as u8
}

fn initial_triangle(face: u8, tri: u8) -> ([f64; 3], [f64; 3], [f64; 3]) {
    let verts = &FACE_PENTAGON_VERTS[face as usize];
    let fc = FACE_CENTERS[face as usize];
    let k = tri as usize;
    (fc, verts[k], verts[(k + 1) % 5])
}

/// Find 2-bit child index (0–3) of P within triangle (apex, left, right).
/// Returns (child_index, new_apex, new_left, new_right).
fn subdivide(
    p: [f64; 3],
    apex: [f64; 3], left: [f64; 3], right: [f64; 3],
) -> (u8, [f64; 3], [f64; 3], [f64; 3]) {
    let m_al = midpoint(apex, left);
    let m_ar = midpoint(apex, right);
    let m_lr = midpoint(left, right);

    if in_triangle(apex, m_al, m_ar, p) { return (0, apex, m_al, m_ar); }
    if in_triangle(m_al, left, m_lr, p) { return (1, m_al, left, m_lr); }
    if in_triangle(m_ar, m_lr, right, p) { return (2, m_ar, m_lr, right); }
    (3, m_lr, m_ar, m_al)
}

/// Encode (lat_deg, lon_deg) at `depth` octets (1–8) for Earth.
pub fn encode(lat_deg: f64, lon_deg: f64, depth: usize) -> Result<RsdggsIndex, Error> {
    if depth < 1 || depth > 8 {
        return Err(Error::InvalidDepth(depth));
    }
    let p = latlon_to_vec(lat_deg, lon_deg);
    let face = assign_face(p);

    if depth == 1 {
        return Ok(RsdggsIndex { body: Body::Earth, face, triangle: None, levels: vec![] });
    }

    let tri = assign_triangle(face, p);
    let (mut apex, mut left, mut right) = initial_triangle(face, tri);

    let level_bits = (depth - 1) * 8;
    if level_bits < 3 {
        return Ok(RsdggsIndex { body: Body::Earth, face, triangle: Some(tri), levels: vec![] });
    }
    let num_levels = (level_bits - 3) / 2;

    let mut levels = Vec::with_capacity(num_levels);
    for _ in 0..num_levels {
        let (child, na, nl, nr) = subdivide(p, apex, left, right);
        levels.push(child);
        apex  = na;
        left  = nl;
        right = nr;
    }

    Ok(RsdggsIndex { body: Body::Earth, face, triangle: Some(tri), levels })
}
