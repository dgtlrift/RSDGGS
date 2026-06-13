pub mod bits;
pub mod cbor;
pub mod cities;
pub mod constants;
pub mod decode;
pub mod encode;
pub mod regulatory;
pub mod types;
pub mod wire;

pub use decode::{decode, cell_center};
pub use encode::encode;
pub use types::{BandEntry, Body, BoundingCell, RsdggsIndex};
pub use wire::{from_wire, to_wire, truncate};

#[derive(Debug)]
pub enum Error {
    InvalidDepth(usize),
    InvalidBody(u8),
    InvalidFace(u8),
    InvalidTriangle(u8),
    InvalidLevel(u8),
    BufferTooShort,
    BandNotFound { face: u8, band_id: u32 },
    NonEarthNotSupported,
}

impl std::fmt::Display for Error {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Error::InvalidDepth(d)      => write!(f, "invalid depth {d} (must be 1-8)"),
            Error::InvalidBody(b)       => write!(f, "invalid body selector {b:#x}"),
            Error::InvalidFace(v)       => write!(f, "invalid face {v} (must be 0-11)"),
            Error::InvalidTriangle(v)   => write!(f, "invalid triangle {v} (must be 0-4)"),
            Error::InvalidLevel(v)      => write!(f, "invalid level child {v} (must be 0-3)"),
            Error::BufferTooShort       => write!(f, "bit buffer too short"),
            Error::BandNotFound { face, band_id } =>
                write!(f, "no band {band_id} for face {face}"),
            Error::NonEarthNotSupported => write!(f, "only Earth body is supported"),
        }
    }
}

impl std::error::Error for Error {}
