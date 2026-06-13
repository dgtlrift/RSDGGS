use crate::{
    constants::{FACE_CENTERS, FACE_PENTAGON_VERTS},
    types::{BoundingCell, RsdggsIndex},
    Error,
};

fn dot(a: [f64; 3], b: [f64; 3]) -> f64 {
    a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
}

fn normalize(v: [f64; 3]) -> [f64; 3] {
    let len = libm::sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2]);
    [v[0]/len, v[1]/len, v[2]/len]
}

fn midpoint(a: [f64; 3], b: [f64; 3]) -> [f64; 3] {
    normalize([a[0]+b[0], a[1]+b[1], a[2]+b[2]])
}

fn vec_to_latlon(v: [f64; 3]) -> (f64, f64) {
    let lat = libm::asin(v[2]).to_degrees();
    let lon = libm::atan2(v[1], v[0]).to_degrees();
    (lat, lon)
}

fn bbox_of(verts: &[[f64; 3]]) -> [f64; 4] {
    let mut lat_min =  90.0f64;
    let mut lat_max = -90.0f64;
    let mut lon_min =  180.0f64;
    let mut lon_max = -180.0f64;
    for &v in verts {
        let (lat, lon) = vec_to_latlon(v);
        lat_min = lat_min.min(lat);
        lat_max = lat_max.max(lat);
        lon_min = lon_min.min(lon);
        lon_max = lon_max.max(lon);
    }
    [lat_min, lat_max, lon_min, lon_max]
}

/// Decode an RSDGGS index into its bounding spherical triangle.
pub fn decode(idx: &RsdggsIndex) -> Result<BoundingCell, Error> {
    let face = idx.face as usize;
    if face >= 12 {
        return Err(Error::InvalidFace(idx.face));
    }

    // Depth 1: return the face itself as a pentagonal "cell" approximated by
    // bounding box of all 5 pentagon vertices.
    let Some(tri) = idx.triangle else {
        let verts = &FACE_PENTAGON_VERTS[face];
        let fc = FACE_CENTERS[face];
        // Use face center and first two pentagon verts as representative triangle.
        let vs = [fc, verts[0], verts[1]];
        let all: Vec<[f64; 3]> = verts.iter().copied().chain([fc]).collect();
        return Ok(BoundingCell { vertices: vs, bbox: bbox_of(&all) });
    };

    if tri >= 5 {
        return Err(Error::InvalidTriangle(tri));
    }

    let verts = &FACE_PENTAGON_VERTS[face];
    let fc    = FACE_CENTERS[face];
    let k     = tri as usize;
    let mut apex  = fc;
    let mut left  = verts[k];
    let mut right = verts[(k + 1) % 5];

    // Apply each subdivision level.
    for &child in &idx.levels {
        let m_al = midpoint(apex, left);
        let m_ar = midpoint(apex, right);
        let m_lr = midpoint(left, right);
        (apex, left, right) = match child {
            0 => (apex, m_al, m_ar),
            1 => (m_al, left, m_lr),
            2 => (m_ar, m_lr, right),
            3 => (m_lr, m_ar, m_al),
            _ => return Err(Error::InvalidLevel(child)),
        };
    }

    let vertices = [apex, left, right];
    let bbox = bbox_of(&vertices);
    Ok(BoundingCell { vertices, bbox })
}

/// Return the geographic centroid of the bounding cell (approximate).
pub fn cell_center(cell: &BoundingCell) -> (f64, f64) {
    let sum = [
        cell.vertices[0][0] + cell.vertices[1][0] + cell.vertices[2][0],
        cell.vertices[0][1] + cell.vertices[1][1] + cell.vertices[2][1],
        cell.vertices[0][2] + cell.vertices[1][2] + cell.vertices[2][2],
    ];
    vec_to_latlon(normalize(sum))
}

#[allow(dead_code)]
fn _dot_used() -> f64 { dot([0.0;3],[0.0;3]) }
