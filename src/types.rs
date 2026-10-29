#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Body {
    Earth = 0x0,
    Moon  = 0x1,
    Mars  = 0x2,
}

impl TryFrom<u8> for Body {
    type Error = crate::Error;
    fn try_from(v: u8) -> Result<Self, Self::Error> {
        match v {
            0 => Ok(Body::Earth),
            1 => Ok(Body::Moon),
            2 => Ok(Body::Mars),
            _ => Err(crate::Error::InvalidBody(v)),
        }
    }
}

/// RSDGGS index — variable resolution, 1–8 octets.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RsdggsIndex {
    pub body:     Body,
    pub face:     u8,         // 0..=11
    pub triangle: Option<u8>, // 0..=4; present when depth >= 2 octets
    pub levels:   Vec<u8>,    // 0..=3 each; up to 26 entries
}

impl RsdggsIndex {
    /// Octet length of the encoded index (1–8).
    pub fn depth_octets(&self) -> usize {
        // Octet 0 = body+face. Triangle + levels fill subsequent bits.
        // 4-bit triangle + 2*n level bits, packed from bit 55 downward.
        // Minimum bits needed beyond octet 0:
        let payload_bits = if self.triangle.is_some() {
            crate::wire::TRIANGLE_BITS + 2 * self.levels.len()
        } else {
            0
        };
        // Octet 0 holds bits 63-56 (8 bits); each additional octet adds 8 bits.
        let total_bits = 8 + payload_bits;
        (total_bits + 7) / 8
    }
}

#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PowerRef { Erp = 0, Eirp = 1, Conducted = 2 }

#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ModulationType {
    Fsk = 0, Gfsk = 1, LoRa = 2, Dsss = 3,
    Ofdm = 4, Ook = 5, Bpsk = 6, Any = 255,
}

#[derive(Debug, Clone)]
pub struct ChannelEntry {
    pub cf_khz: u32,
    pub bw_khz: u32,
}

#[derive(Debug, Clone)]
pub struct BandEntry {
    pub band_id:       u32,
    pub authority:     &'static str,
    pub citation:      &'static str,
    pub freq_lo_khz:   u32,
    pub freq_hi_khz:   u32,
    pub power_mw:      f32,
    pub power_ref:     PowerRef,
    pub duty_cycle:    Option<f32>,
    pub dwell_s:       Option<f32>,
    pub lbt:           bool,
    pub hop_required:  bool,
    pub min_hop_set:   Option<u32>,
    pub channels:      Option<&'static [ChannelEntry]>,
    pub modulation:    Option<&'static [ModulationType]>,
    pub whitespace_db: Option<&'static str>,
    pub available:     bool,
    pub exception:     bool,
    /// The entry applies only to emissions at least this wide (kHz): FCC 15.247(a)(2)'s
    /// 500 kHz for digital modulation, for example.
    pub min_bw_khz:    Option<u32>,
    /// Power spectral density limit, mW per MHz, by `power_ref`.
    pub psd_mw_per_mhz: Option<f32>,
    /// `duty_cycle` applies only above this power (mW, by `power_ref`): EN 300 328's
    /// medium utilisation limit for non-adaptive equipment above 10 dBm e.i.r.p.
    pub duty_cycle_above_mw: Option<f32>,
    /// The window `dwell_s` is measured in, seconds: at most `dwell_s` of air time on
    /// any one channel within any sliding window of this length.
    pub dwell_window_s: Option<f32>,
    /// The power limit (mW, by `single_channel_power_ref`) for a transmitter that has
    /// used no other channel in the band within the last `single_channel_window_s`.
    pub single_channel_power_mw: Option<f32>,
    pub single_channel_power_ref: Option<PowerRef>,
    pub single_channel_window_s: Option<f32>,
}

/// A location the face-level database gets wrong (draft section 8.3): its own band
/// entries, for cells at its resolution sufficiency level whose centre falls inside its
/// bounding box (and, where given, on its face and triangles).
#[derive(Debug, Clone)]
pub struct ExceptionEntry {
    pub location:  &'static str,
    pub authority: &'static str,
    /// The face it is on; `None`: any whose cell centre falls in `bbox`.
    pub face:      Option<u8>,
    /// The face's triangles it covers; `None`: any.
    pub triangles: Option<&'static [u8]>,
    /// [lat_min, lat_max, lon_min, lon_max], degrees; lon_min > lon_max crosses the
    /// antimeridian.
    pub bbox:      [f64; 4],
    /// Resolution sufficiency level: the index depth, octets, the test is made at.
    pub rsl:       usize,
    /// The bands in force there; empty if none is known to be available.
    pub bands:     &'static [&'static BandEntry],
}

/// Bounding cell returned by decode().
#[derive(Debug, Clone)]
pub struct BoundingCell {
    /// The three unit-vector vertices of the bounding spherical triangle.
    pub vertices: [[f64; 3]; 3],
    /// Geographic bounding box [lat_min, lat_max, lon_min, lon_max] in degrees.
    pub bbox: [f64; 4],
}
