pub mod earth;

use crate::{
    Error,
    decode::{cell_center, decode},
    types::{BandEntry, Body, ExceptionEntry, RsdggsIndex},
    wire::truncate,
};

pub fn lookup(
    face: u8,
    body: Body,
    band_id: u32,
) -> Result<&'static BandEntry, Error> {
    match body {
        Body::Earth => earth::lookup_face(face, band_id).ok_or(Error::BandNotFound { face, band_id }),
        _ => Err(Error::NonEarthNotSupported),
    }
}

/// Return all face-level regulatory band entries for the given face and body.
pub fn bands_for_face(face: u8, body: Body) -> impl Iterator<Item = &'static BandEntry> {
    match body {
        Body::Earth => earth::bands_for_face(face),
        _ => earth::bands_for_face(255), // empty — no other bodies have data
    }
}

/// The exception (draft section 8.3) whose territory holds `idx`, if any: the deepest
/// RSL among those that match.
///
/// # Errors
///
/// [`Error::NonEarthNotSupported`]; [`Error::InsufficientResolution`] if `idx` is shorter
/// than an exception's RSL on its face, so it can't be told whether it applies.
pub fn exception_for_index(idx: &RsdggsIndex) -> Result<Option<&'static ExceptionEntry>, Error> {
    if idx.body != Body::Earth {
        return Err(Error::NonEarthNotSupported);
    }
    let mut best: Option<&'static ExceptionEntry> = None;
    for e in earth::EXCEPTIONS {
        if e.face.is_some_and(|f| f != idx.face) {
            continue;
        }
        if let Some(t) = e.triangles
            && !idx.triangle.is_some_and(|tri| t.contains(&tri))
        {
            continue;
        }
        if idx.depth_octets() < e.rsl {
            if e.face.is_some() {
                return Err(Error::InsufficientResolution { needed: e.rsl });
            }
            continue;
        }
        let cell = decode(&truncate(idx, e.rsl))?;
        let (lat, lon) = cell_center(&cell);
        let [lat_lo, lat_hi, lon_lo, lon_hi] = e.bbox;
        let in_lon = if lon_lo <= lon_hi {
            (lon_lo..=lon_hi).contains(&lon)
        } else {
            lon >= lon_lo || lon <= lon_hi
        };
        if (lat_lo..=lat_hi).contains(&lat) && in_lon && best.is_none_or(|b| e.rsl > b.rsl) {
            best = Some(e);
        }
    }
    Ok(best)
}

/// The band entries in force in `idx`'s cell: its exception's, if the overlay has one for
/// it, otherwise its face's.
///
/// # Errors
///
/// As [`exception_for_index`].
pub fn bands_for_index(idx: &RsdggsIndex) -> Result<Vec<&'static BandEntry>, Error> {
    Ok(match exception_for_index(idx)? {
        Some(e) => e.bands.to_vec(),
        None => earth::bands_for_face(idx.face).collect(),
    })
}

/// The band entries in force at a point, from its 8-octet index.
///
/// # Errors
///
/// As [`crate::encode`] and [`bands_for_index`].
pub fn bands_for_location(lat_deg: f64, lon_deg: f64) -> Result<Vec<&'static BandEntry>, Error> {
    bands_for_index(&crate::encode(lat_deg, lon_deg, 8)?)
}
