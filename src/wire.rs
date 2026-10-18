use crate::{
    bits::{BitReader, BitWriter},
    types::{Body, RsdggsIndex},
    Error,
};

/// Width of the triangle selector, the first field after octet 0 (draft §5.1).
///
/// Four bits (values 0–4 used, 5–15 reserved) keep every 2-bit level within one
/// octet, so truncating a cell is simply dropping trailing octets.
pub const TRIANGLE_BITS: usize = 4;

/// Number of subdivision levels carried by an index of `depth` octets (1–8):
/// 0, 2, 6, 10, 14, 18, 22, 26.
pub const fn levels_for_depth(depth: usize) -> usize {
    if depth < 2 { 0 } else { ((depth - 1) * 8 - TRIANGLE_BITS) / 2 }
}

/// Pack an [`RsdggsIndex`] into a big-endian 64-bit wire value.
///
/// Bits beyond the last significant level are zero.
pub fn to_wire(idx: &RsdggsIndex) -> u64 {
    let mut w = BitWriter::new();
    w.write(idx.body as u64, 4);
    w.write(idx.face as u64, 4);
    if let Some(tri) = idx.triangle {
        w.write(tri as u64, TRIANGLE_BITS as u8);
        for &level in &idx.levels {
            w.write(level as u64, 2);
        }
    }
    let bytes: [u8; 8] = w.finish(8)
        .try_into()
        .expect("finish(8) always yields 8 bytes");
    u64::from_be_bytes(bytes)
}

/// Unpack a 64-bit wire value into an [`RsdggsIndex`] at the given octet depth (1–8).
///
/// Only the first `depth` octets of `value` are decoded; bits beyond that are ignored.
/// Every bit of those octets is significant.
pub fn from_wire(value: u64, depth: usize) -> Result<RsdggsIndex, Error> {
    if depth < 1 || depth > 8 {
        return Err(Error::InvalidDepth(depth));
    }
    let all_bytes = value.to_be_bytes();
    let mut r = BitReader::new(&all_bytes[..depth]);

    let body = Body::try_from(r.read(4)? as u8)?;
    let face = r.read(4)? as u8;
    if face > 11 {
        return Err(Error::InvalidFace(face));
    }

    if depth == 1 {
        return Ok(RsdggsIndex { body, face, triangle: None, levels: vec![] });
    }

    let tri = r.read(TRIANGLE_BITS as u8)? as u8;
    if tri > 4 {
        return Err(Error::InvalidTriangle(tri));
    }
    let num_levels = levels_for_depth(depth);
    let mut levels = Vec::with_capacity(num_levels);
    for _ in 0..num_levels {
        levels.push(r.read(2)? as u8);
    }

    Ok(RsdggsIndex { body, face, triangle: Some(tri), levels })
}

/// Truncate an `RsdggsIndex` to the given octet depth.
///
/// Returns a new index whose triangle/level fields are clipped to the number
/// that fit in `depth` octets.  Panics if `depth` is not in 1–8.
pub fn truncate(idx: &RsdggsIndex, depth: usize) -> RsdggsIndex {
    assert!((1..=8).contains(&depth), "depth must be 1-8");
    if depth == 1 {
        return RsdggsIndex { body: idx.body, face: idx.face, triangle: None, levels: vec![] };
    }
    let num_levels = levels_for_depth(depth);
    RsdggsIndex {
        body:     idx.body,
        face:     idx.face,
        triangle: idx.triangle,
        levels:   idx.levels[..num_levels.min(idx.levels.len())].to_vec(),
    }
}
