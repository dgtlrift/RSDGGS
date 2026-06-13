pub mod earth;

use crate::{types::{BandEntry, Body}, Error};

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

/// Return all regulatory band entries for the given face and body.
pub fn bands_for_face(face: u8, body: Body) -> impl Iterator<Item = &'static BandEntry> {
    match body {
        Body::Earth => earth::bands_for_face(face),
        _ => earth::bands_for_face(255), // empty — no other bodies have data
    }
}
