use std::{
    env,
    fs,
    path::{Path, PathBuf},
    process::Command,
};

fn main() {
    let out_dir = PathBuf::from(env::var("OUT_DIR").unwrap());

    // Locate the cddlc binary: CDDLC env var overrides PATH lookup.
    let cddlc = env::var("CDDLC").unwrap_or_else(|_| "cddlc".to_string());

    let schemas: &[(&str, &str)] = &[
        ("cddl/rsdggs.cddl",    "rsdggs"),
        ("cddl/regulatory.cddl", "regulatory"),
    ];

    let gen_root = out_dir.join("cddlc_gen");

    for &(schema_path, stem) in schemas {
        println!("cargo:rerun-if-changed={schema_path}");

        run_cddlc(&cddlc, schema_path, &gen_root);

        // cddlc writes to <gen_root>/<stem>-cbor/src/lib.rs
        let lib_rs = gen_root.join(format!("{stem}-cbor/src/lib.rs"));
        let content = fs::read_to_string(&lib_rs)
            .unwrap_or_else(|e| panic!("cannot read {}: {e}", lib_rs.display()));

        // Strip crate-level #![...] attributes: they are invalid inside
        // a mod {} block (which is where include!() will paste this content).
        let stripped = strip_crate_attrs(&content);

        let dest = out_dir.join(format!("{stem}_cbor.rs"));
        fs::write(&dest, stripped)
            .unwrap_or_else(|e| panic!("cannot write {}: {e}", dest.display()));
    }
}

fn run_cddlc(cddlc: &str, schema: &str, out_dir: &Path) {
    let status = Command::new(cddlc)
        .args([schema, "--lang", "rust", "--output"])
        .arg(out_dir)
        .status()
        .unwrap_or_else(|e| {
            panic!(
                "failed to run cddlc '{cddlc}' on '{schema}': {e}\n\
                 Hint: set the CDDLC environment variable to the full path of the cddlc binary,\n\
                 e.g.  CDDLC=/path/to/cddlc cargo build"
            )
        });

    if !status.success() {
        panic!("cddlc exited with status {status} while processing {schema}");
    }
}

/// Remove crate-level `#![...]` attributes that are invalid inside a module block.
///
/// cddlc emits `#![cfg_attr(feature = "no-std", no_std)]` for standalone-crate
/// use.  When the output is include!()'d inside a `mod {}` block those attrs
/// would annotate the enclosing crate, not the module, so we strip them.
/// Item-level `#[allow(unexpected_cfgs)]` attrs emitted by cddlc handle the
/// no-std feature-gate warnings at the point of each gated item instead.
fn strip_crate_attrs(src: &str) -> String {
    src.lines()
        .filter(|line| !line.trim_start().starts_with("#!["))
        .collect::<Vec<_>>()
        .join("\n")
}
