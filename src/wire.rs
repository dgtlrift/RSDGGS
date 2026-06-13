use crate::{
    bits::{BitReader, BitWriter},
    types::{Body, RsdggsIndex},
    Error,
};

/// Pack an [`RsdggsIndex`] into a big-endian 64-bit wire value.
///
/// Bits below the last significant level are left as zero (reserved).
pub fn to_wire(idx: &RsdggsIndex) -> u64 {
    let mut w = BitWriter::new();
    w.write(idx.body as u64, 4);
    w.write(idx.face as u64, 4);
    if let Some(tri) = idx.triangle {
        w.write(tri as u64, 3);
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
/// If `depth` is 8 (the default), all 64 bits are consumed — the final bit is reserved
/// and expected to be zero.
pub fn from_wire(value: u64, depth: usize) -> Result<RsdggsIndex, Error> {
    if depth < 1 || depth > 8 {
        return Err(Error::InvalidDepth(depth));
    }
    let all_bytes = value.to_be_bytes();
    let mut r = BitReader::new(&all_bytes[..depth]);

    let body = Body::try_from(r.read(4)? as u8)?;
    let face = r.read(4)? as u8;

    if depth == 1 {
        return Ok(RsdggsIndex { body, face, triangle: None, levels: vec![] });
    }

    let tri = r.read(3)? as u8;
    // Each additional octet beyond the first yields 8 bits; 3 are used for
    // the triangle selector, leaving pairs for subdivision levels.
    let num_levels = ((depth - 1) * 8 - 3) / 2;
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
    let num_levels = ((depth - 1) * 8 - 3) / 2;
    RsdggsIndex {
        body:     idx.body,
        face:     idx.face,
        triangle: idx.triangle,
        levels:   idx.levels[..num_levels.min(idx.levels.len())].to_vec(),
    }
}
