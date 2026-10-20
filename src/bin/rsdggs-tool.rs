//! rsdggs-tool — interactive tester for the RSDGGS library.
//!
//! USAGE
//!   cargo run --example rsdggs-tool -- encode <lat> <lon>  [--depth N] [--truncate N]
//!   cargo run --example rsdggs-tool -- decode <value>       [--depth N] [--truncate N]
//!
//! `value` may be decimal (e.g. 2594073385365405696) or hex (e.g. 0x2400000000000000).
//! `--depth N`    sets encoding depth (1–8 octets, default 8); for decode, specifies
//!                how many octets of the value are significant (default 8).
//! `--truncate N` reduces the result to N octets of precision and warns when that is
//!                insufficient for reliable regulatory determination.

use rsdggs::{
    BoundingCell, RsdggsIndex,
    cell_center, decode, encode,
    from_wire, to_wire, truncate,
    cities::{metro_context, MetroRef},
    regulatory::bands_for_face,
    types::{Body, PowerRef},
};

// ── Face labels ────────────────────────────────────────────────────────────────

const FACE_LABELS: [&str; 12] = [
    "Antarctica / New Zealand", // F0
    "Europe",                   // F1
    "North America",            // F2
    "Asia",                     // F3
    "South Atlantic",           // F4
    "Africa / Middle East",     // F5
    "South America",            // F6
    "Eastern Australia",        // F7
    "Southern Indian Ocean",    // F8
    "West Africa",              // F9
    "Central Pacific",          // F10
    "North Pacific",            // F11
];

// ── Entry point ────────────────────────────────────────────────────────────────

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.is_empty() || args[0] == "--help" || args[0] == "-h" {
        print_usage();
        return;
    }
    let result = match args[0].as_str() {
        "encode" => cmd_encode(&args[1..]),
        "decode" => cmd_decode(&args[1..]),
        other    => Err(format!("unknown subcommand '{other}'; try encode or decode")),
    };
    if let Err(e) = result {
        eprintln!("error: {e}");
        std::process::exit(1);
    }
}

// ── Encode subcommand ──────────────────────────────────────────────────────────

fn cmd_encode(args: &[String]) -> Result<(), String> {
    if args.len() < 2 {
        return Err("encode requires <lat> <lon>".into());
    }
    let lat: f64 = args[0].parse().map_err(|_| format!("invalid latitude '{}'", args[0]))?;
    let lon: f64 = args[1].parse().map_err(|_| format!("invalid longitude '{}'", args[1]))?;

    if !(-90.0..=90.0).contains(&lat) {
        return Err(format!("latitude {lat} out of range −90..90"));
    }
    if !(-180.0..=180.0).contains(&lon) {
        return Err(format!("longitude {lon} out of range −180..180"));
    }

    let opts = parse_opts(&args[2..])?;
    let depth      = opts.depth.unwrap_or(8);
    let trunc_depth = opts.truncate;

    let idx = encode(lat, lon, depth)
        .map_err(|e| format!("encode error: {e}"))?;

    separator();
    println!(" RSDGGS ENCODE");
    separator();

    println!(" Input");
    println!("   Latitude  : {:>12.6}°", lat);
    println!("   Longitude : {:>12.6}°", lon);
    println!("   Depth     :  {} octets{}", depth, if depth == 8 { " (max)" } else { "" });

    print_index_and_regulatory(&idx, trunc_depth);
    Ok(())
}

// ── Decode subcommand ──────────────────────────────────────────────────────────

fn cmd_decode(args: &[String]) -> Result<(), String> {
    if args.is_empty() {
        return Err("decode requires <value>".into());
    }

    let raw = &args[0];
    let value: u64 = parse_u64(raw)
        .map_err(|e| format!("invalid value '{}': {}", raw, e))?;

    let opts = parse_opts(&args[1..])?;
    let depth       = opts.depth.unwrap_or(8);
    let trunc_depth = opts.truncate;

    let idx = from_wire(value, depth)
        .map_err(|e| format!("decode error: {e}"))?;

    separator();
    println!(" RSDGGS DECODE");
    separator();

    println!(" Input");
    if raw.starts_with("0x") || raw.starts_with("0X") {
        println!("   Value (hex) : {}", raw.to_uppercase().replace("0X", "0x"));
        println!("   Value (dec) : {}", value);
    } else {
        println!("   Value (dec) : {}", value);
        println!("   Value (hex) : {:#018x}", value);
    }
    println!("   Depth       :  {} octets{}", depth,
        if opts.depth.is_none() { " (assumed max)" } else { "" });

    print_index_and_regulatory(&idx, trunc_depth);
    Ok(())
}

// ── Shared display logic ───────────────────────────────────────────────────────

fn print_index_and_regulatory(idx: &RsdggsIndex, trunc_depth: Option<usize>) {
    // Optionally truncate
    let (display_idx, was_truncated) = match trunc_depth {
        Some(n) => (truncate(idx, n), true),
        None    => (idx.clone(), false),
    };

    if was_truncated {
        let orig_depth = idx.depth_octets();
        let new_depth  = display_idx.depth_octets();
        println!();
        println!(" Truncation");
        println!("   Original depth : {} octets", orig_depth);
        println!("   Truncated to   : {} octets", new_depth);
        check_truncation_warnings(&display_idx);
    }

    // Index fields
    println!();
    println!(" Index");
    let body_str = match display_idx.body {
        Body::Earth => "Earth",
        Body::Moon  => "Moon",
        Body::Mars  => "Mars",
    };
    println!("   Body     : {} ({:#03x})", body_str, display_idx.body as u8);
    let face = display_idx.face;
    println!("   Face     : {}  [{}]", face, FACE_LABELS[face as usize]);
    match display_idx.triangle {
        Some(t) => println!("   Triangle : {}", t),
        None    => println!("   Triangle : — (depth 1, not encoded)"),
    }
    if display_idx.levels.is_empty() {
        println!("   Levels   : [] (no subdivision)");
    } else {
        let lvl_str: Vec<String> = display_idx.levels.iter().map(|l| l.to_string()).collect();
        println!("   Levels   : [{}]  ({} steps)", lvl_str.join(", "), display_idx.levels.len());
    }

    // Wire value
    let wire = to_wire(&display_idx);
    println!();
    println!(" Wire Value");
    println!("   Hex     : {:#018x}", wire);
    println!("   Decimal : {}", wire);

    // Bounding cell
    let cell = decode(&display_idx).expect("decode of valid index should not fail");
    let (clat, clon) = cell_center(&cell);
    print_bounding_cell(&cell, clat, clon);

    // Regulatory
    print_regulatory(&display_idx);

    separator();
}

fn print_bounding_cell(cell: &BoundingCell, clat: f64, clon: f64) {
    let [lat_min, lat_max, lon_min, lon_max] = cell.bbox;
    let lat_span = lat_max - lat_min;
    let lon_span = lon_max - lon_min;

    // Rough km estimate: 1° lat ≈ 111 km
    let lat_km = lat_span * 111.0;
    let lon_km = lon_span * 111.0 * clat.to_radians().cos();

    let area_km2 = lat_km * lon_km;

    println!();
    println!(" Bounding Cell");
    println!("   Latitude  : {:>10.5}° – {:.5}°  (span {:.4}° / ~{:.1} km)",
        lat_min, lat_max, lat_span, lat_km);
    println!("   Longitude : {:>10.5}° – {:.5}°  (span {:.4}° / ~{:.1} km)",
        lon_min, lon_max, lon_span, lon_km);
    println!("   Area      :  ~{:.3} km²", area_km2);
    println!("   Center    :  {:.6}°{}, {:.6}°{}",
        clat.abs(), if clat >= 0.0 { "N" } else { "S" },
        clon.abs(), if clon >= 0.0 { "E" } else { "W" });
    let metro_line = match metro_context(cell.bbox, clat, clon) {
        MetroRef::Contains { name, pop_millions } =>
            format!("contains {} ({:.1}M pop.)", name, pop_millions),
        MetroRef::Within { name, dist_km } =>
            format!("within {} metro area (~{:.0} km from city center)", name, dist_km),
        MetroRef::Near { name, dist_km } =>
            format!("~{:.0} km from {}", dist_km, name),
    };
    println!("   Metro     :  {}", metro_line);
}

fn print_regulatory(idx: &RsdggsIndex) {
    let body  = idx.body;
    let face  = idx.face;
    let label = FACE_LABELS[face as usize];

    println!();
    println!(" Regulatory  (Face {} / {} — {})", face,
        match body { Body::Earth => "Earth", Body::Moon => "Moon", Body::Mars => "Mars" },
        label);

    let bands: Vec<_> = bands_for_face(face, body).collect();
    if bands.is_empty() {
        println!("   WARNING: No regulatory data for this face/region in the database.");
        println!("   Coverage is limited to faces 1 (Europe), 2 (North America), and 7 (Eastern Australia).");
        return;
    }

    for band in bands {
        println!();
        println!("   [{id}]  {auth}  {lo}–{hi} MHz",
            id   = band.band_id,
            auth = band.authority,
            lo   = band.freq_lo_khz / 1000,
            hi   = band.freq_hi_khz / 1000);
        println!("        Citation    : {}", band.citation);
        println!("        Power       : {} mW  ({})",
            band.power_mw,
            match band.power_ref {
                PowerRef::Erp       => "ERP",
                PowerRef::Eirp      => "EIRP",
                PowerRef::Conducted => "conducted",
            });
        println!("        Hop req.    : {}{}",
            if band.hop_required { "yes" } else { "no" },
            band.min_hop_set.map_or(String::new(), |n| format!("  (min {} channels)", n)).as_str());
        println!("        LBT         : {}", if band.lbt { "required" } else { "no" });
        println!("        Duty cycle  : {}",
            band.duty_cycle.map_or("unrestricted".to_string(), |d| format!("{:.0}%", d * 100.0)));
        if let Some(dwell) = band.dwell_s {
            println!("        Dwell limit : {:.3} s", dwell);
        }
        if let Some(ws) = band.whitespace_db {
            println!("        White space : {} dB", ws);
        }
        println!("        Available   : {}", if band.available { "YES" } else { "NO" });
        if band.exception {
            println!("        EXCEPTION   : this entry has exception status");
        }
    }
}

fn check_truncation_warnings(idx: &RsdggsIndex) {
    let depth = idx.depth_octets();

    if depth == 1 {
        println!();
        println!("   WARNING: Depth 1 provides face-level resolution only.");
        println!("            Triangle and subdivision data are absent.");
        println!("            The bounding cell spans a large portion of a continent.");
        println!("            Regulatory lookup is possible (face determines jurisdiction),");
        println!("            but the geographic area is not suitable for precise compliance.");
    } else if depth == 2 {
        println!();
        println!("   NOTE: Depth 2 — triangle level only (no subdivision).");
        println!("         Bounding cell covers a large sub-continental region.");
    }

    // Warn if no regulatory data for this face
    let bands: Vec<_> = bands_for_face(idx.face, idx.body).collect();
    if bands.is_empty() {
        println!();
        println!("   WARNING: Face {} ({}) has no regulatory entries in this database.",
            idx.face, FACE_LABELS[idx.face as usize]);
        println!("            Spectrum regulations for this region are not yet populated.");
    }
}

// ── Argument parsing ──────────────────────────────────────────────────────────

struct Opts {
    depth:    Option<usize>,
    truncate: Option<usize>,
}

fn parse_opts(args: &[String]) -> Result<Opts, String> {
    let mut depth    = None;
    let mut truncate = None;
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--depth" | "-d" => {
                i += 1;
                let n = args.get(i)
                    .ok_or("--depth requires a value")?
                    .parse::<usize>()
                    .map_err(|_| format!("invalid depth '{}'", args[i]))?;
                if n < 1 || n > 8 { return Err(format!("depth must be 1–8, got {n}")); }
                depth = Some(n);
            }
            "--truncate" | "-t" => {
                i += 1;
                let n = args.get(i)
                    .ok_or("--truncate requires a value")?
                    .parse::<usize>()
                    .map_err(|_| format!("invalid truncate depth '{}'", args[i]))?;
                if n < 1 || n > 8 { return Err(format!("truncate depth must be 1–8, got {n}")); }
                truncate = Some(n);
            }
            other => return Err(format!("unknown option '{other}'")),
        }
        i += 1;
    }
    if let (Some(d), Some(t)) = (depth, truncate) {
        if t > d { return Err(format!("--truncate {t} cannot exceed --depth {d}")); }
    }
    Ok(Opts { depth, truncate })
}

fn parse_u64(s: &str) -> Result<u64, String> {
    let s = s.trim();
    if let Some(hex) = s.strip_prefix("0x").or_else(|| s.strip_prefix("0X")) {
        u64::from_str_radix(hex, 16).map_err(|e| e.to_string())
    } else {
        s.parse::<u64>().map_err(|e| e.to_string())
    }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

fn separator() {
    println!("{}", "─".repeat(64));
}

fn print_usage() {
    println!("rsdggs-tool — RSDGGS library test tool");
    println!();
    println!("USAGE:");
    println!("  encode <lat> <lon> [--depth N] [--truncate N]");
    println!("  decode <value>     [--depth N] [--truncate N]");
    println!();
    println!("  <lat>   Latitude  in decimal degrees (−90..90)");
    println!("  <lon>   Longitude in decimal degrees (−180..180)");
    println!("  <value> 64-bit RSDGGS wire value — decimal or 0x-prefixed hex");
    println!();
    println!("OPTIONS:");
    println!("  -d, --depth N      Octet precision 1–8 (default: 8)");
    println!("                     For decode: significant octets in the wire value");
    println!("  -t, --truncate N   Reduce output to N-octet precision");
    println!("                     Warns when N is too coarse for regulatory use");
    println!("  -h, --help         Show this help");
    println!();
    println!("EXAMPLES:");
    println!("  encode  39.0 -98.0");
    println!("  encode  51.5 -0.1 --depth 5");
    println!("  encode  39.0 -98.0 --depth 8 --truncate 2");
    println!("  decode  0x2100000000000000");
    println!("  decode  2594073385365405696 --depth 4");
}
