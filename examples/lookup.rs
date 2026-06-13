/// Usage: cargo run --example lookup -- <lat> <lon> <depth>
/// Example: cargo run --example lookup -- 39.0 -98.0 4
use rsdggs::{decode, encode, decode::cell_center, regulatory};

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 4 {
        eprintln!("Usage: {} <lat_deg> <lon_deg> <depth 1-8>", args[0]);
        std::process::exit(1);
    }
    let lat:   f64   = args[1].parse().expect("lat must be f64");
    let lon:   f64   = args[2].parse().expect("lon must be f64");
    let depth: usize = args[3].parse().expect("depth must be usize");

    let idx = encode(lat, lon, depth).unwrap_or_else(|e| {
        eprintln!("encode error: {e}");
        std::process::exit(1);
    });

    println!("Input:     {lat:.6}°N  {lon:.6}°E");
    println!("Face:      {}", idx.face);
    println!("Triangle:  {:?}", idx.triangle);
    println!("Levels:    {:?}", idx.levels);
    println!("Depth:     {} octets", idx.depth_octets());

    let cell = decode(&idx).unwrap();
    let (clat, clon) = cell_center(&cell);
    let [lat_min, lat_max, lon_min, lon_max] = cell.bbox;
    println!("Cell center: {clat:.6}°N  {clon:.6}°E");
    println!("Cell bbox:   lat [{lat_min:.4}, {lat_max:.4}]  lon [{lon_min:.4}, {lon_max:.4}]");

    println!("\nISM bands for face {}:", idx.face);
    let bands: Vec<_> = regulatory::earth::bands_for_face(idx.face).collect();
    if bands.is_empty() {
        println!("  (none in table)");
    }
    for b in bands {
        println!(
            "  [{}] {} {} — {}-{} kHz  {} mW {:?}  duty={:?}  hop={}",
            b.band_id, b.authority, b.citation,
            b.freq_lo_khz, b.freq_hi_khz,
            b.power_mw, b.power_ref,
            b.duty_cycle, b.hop_required
        );
    }
}
