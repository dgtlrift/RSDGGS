use std::{
    env,
    fs,
    path::{Path, PathBuf},
    process::Command,
};

fn main() {
    let out_dir = PathBuf::from(env::var("OUT_DIR").unwrap());

    // Locate the cddlc binary: the CDDLC environment variable, else `cddlc` on the PATH,
    // else the pinned release candidate, downloaded and checked against its SHA-256.
    println!("cargo:rerun-if-env-changed=CDDLC");
    let cddlc = find_cddlc(&out_dir);
    let cddlc = cddlc.to_str().expect("UTF-8 path");

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

/// The cddlc release this crate builds with when none is installed: a static x86-64
/// Linux binary (https://github.com/dgtlrift/cddlc/releases/tag/v1.1.0-rc.2).
const CDDLC_RELEASE: &str = "v1.1.0-rc.2";
const CDDLC_ASSET: &str = "cddlc-v1.1.0-rc.2-x86_64-unknown-linux-musl";
const CDDLC_SHA256: &str = "9d29584f6371059f7567053d9f4405ba664de7df4aa27eea5957c210b8a0499d";

/// `$CDDLC`, else `cddlc` on the PATH, else the release in `out_dir`, fetched with
/// `curl`, checked with `sha256sum` and unpacked with `tar` if it isn't there yet.
fn find_cddlc(out_dir: &Path) -> PathBuf {
    if let Ok(path) = env::var("CDDLC") {
        return PathBuf::from(path);
    }
    let on_path = Command::new("cddlc")
        .arg("--version")
        .output()
        .is_ok_and(|o| o.status.success());
    if on_path {
        return PathBuf::from("cddlc");
    }
    let host = env::var("HOST").unwrap_or_default();
    if !(host.starts_with("x86_64-") && host.contains("-linux-")) {
        panic!(
            "no cddlc found, and the release ({CDDLC_RELEASE}) is built for x86-64 Linux only, \
             not {host}.\nHint: install cddlc, or set CDDLC to its full path."
        );
    }
    let dir = out_dir.join("cddlc-release");
    let binary = dir.join(CDDLC_ASSET).join("cddlc");
    if binary.exists() {
        return binary;
    }
    fs::create_dir_all(&dir).expect("create the cddlc download directory");
    let archive = format!("{CDDLC_ASSET}.tar.gz");
    let url = format!(
        "https://github.com/dgtlrift/cddlc/releases/download/{CDDLC_RELEASE}/{archive}"
    );
    run(Command::new("curl").args(["-sSfL", "-o", &archive, &url]).current_dir(&dir));
    let sum = Command::new("sha256sum")
        .arg(&archive)
        .current_dir(&dir)
        .output()
        .expect("run sha256sum");
    let got = String::from_utf8_lossy(&sum.stdout);
    if got.split_whitespace().next() != Some(CDDLC_SHA256) {
        panic!("{url}: SHA-256 {got} is not the pinned {CDDLC_SHA256}");
    }
    run(Command::new("tar").args(["-xzf", &archive]).current_dir(&dir));
    binary
}

fn run(cmd: &mut Command) {
    let status = cmd
        .status()
        .unwrap_or_else(|e| panic!("failed to run {cmd:?}: {e}"));
    if !status.success() {
        panic!("{cmd:?} exited with {status}");
    }
}

fn run_cddlc(cddlc: &str, schema: &str, out_dir: &Path) {
    let status = Command::new(cddlc)
        .args(["generate", schema, "--lang", "rust", "--output"])
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
