/// Writes bits into a fixed 8-byte buffer MSB-first.
pub struct BitWriter {
    buf: [u8; 8],
    pos: u8, // next bit position to write (0 = MSB of byte 0)
}

impl BitWriter {
    pub fn new() -> Self {
        Self { buf: [0u8; 8], pos: 0 }
    }

    /// Write `count` bits from the LSBs of `value`, MSB first.
    pub fn write(&mut self, value: u64, count: u8) {
        debug_assert!(count <= 64);
        debug_assert!((self.pos as u16 + count as u16) <= 64);
        for i in (0..count).rev() {
            let bit = ((value >> i) & 1) as u8;
            let byte_idx = (self.pos / 8) as usize;
            let bit_idx  = 7 - (self.pos % 8);
            self.buf[byte_idx] |= bit << bit_idx;
            self.pos += 1;
        }
    }

    /// Return buffer truncated to `octets` bytes (1–8).
    pub fn finish(&self, octets: usize) -> &[u8] {
        &self.buf[..octets]
    }
}

/// Reads bits from a byte slice MSB-first.
pub struct BitReader<'a> {
    buf: &'a [u8],
    pos: u8,
}

impl<'a> BitReader<'a> {
    pub fn new(buf: &'a [u8]) -> Self {
        Self { buf, pos: 0 }
    }

    /// Read `count` bits, returned in the LSBs of a u64.
    pub fn read(&mut self, count: u8) -> Result<u64, crate::Error> {
        if self.pos as usize + count as usize > self.buf.len() * 8 {
            return Err(crate::Error::BufferTooShort);
        }
        let mut val = 0u64;
        for _ in 0..count {
            let byte_idx = (self.pos / 8) as usize;
            let bit_idx  = 7 - (self.pos % 8);
            let bit = ((self.buf[byte_idx] >> bit_idx) & 1) as u64;
            val = (val << 1) | bit;
            self.pos += 1;
        }
        Ok(val)
    }

    pub fn bits_remaining(&self) -> usize {
        self.buf.len() * 8 - self.pos as usize
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip_nibbles() {
        let mut w = BitWriter::new();
        w.write(0b1010, 4);
        w.write(0b0011, 4);
        let bytes = w.finish(1);

        let mut r = BitReader::new(bytes);
        assert_eq!(r.read(4).unwrap(), 0b1010);
        assert_eq!(r.read(4).unwrap(), 0b0011);
    }

    #[test]
    fn cross_octet_boundary() {
        // Write 3 bits in byte 0 LSB, then 2 bits across boundary
        let mut w = BitWriter::new();
        w.write(0b111, 3);  // bits 7-5 of byte0
        w.write(0b10101, 5); // fills remaining 5 bits of byte0
        w.write(0b11, 2);   // first 2 bits of byte1
        let bytes = w.finish(2);

        let mut r = BitReader::new(bytes);
        assert_eq!(r.read(3).unwrap(), 0b111);
        assert_eq!(r.read(5).unwrap(), 0b10101);
        assert_eq!(r.read(2).unwrap(), 0b11);
    }

    #[test]
    fn full_64_bits() {
        let val: u64 = 0xDEAD_BEEF_CAFE_1234;
        let mut w = BitWriter::new();
        w.write(val, 64);
        let bytes = w.finish(8);
        assert_eq!(bytes, &val.to_be_bytes());

        let mut r = BitReader::new(bytes);
        assert_eq!(r.read(64).unwrap(), val);
    }
}
