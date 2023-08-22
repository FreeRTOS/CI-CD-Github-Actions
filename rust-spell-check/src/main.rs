#![deny(clippy::all, clippy::pedantic)]

use clap::Parser;
use libaspell_sys::{AspellDocumentChecker, AspellSpeller};
use std::{
    ffi::OsStr,
    fs,
    path::{Path, PathBuf},
    process::exit,
};

/// Spell checker for code repos
#[derive(Parser)]
struct Args {
    /// Additional wordlists to use
    #[clap(long, short)]
    wordlist: Vec<PathBuf>,
    /// Show context of misspellings
    #[clap(long, short)]
    context: bool,
    /// Files to check for spelling errors
    files: Vec<PathBuf>,
}

fn main() {
    let args = Args::parse();

    let error_count = args
        .files
        .iter()
        .map(|f| process_file(f, args.context, &args.wordlist))
        .sum();

    exit(error_count);
}

fn process_file<P: AsRef<Path>>(path: P, context: bool, wordlists: &[PathBuf]) -> i32 {
    let path = path.as_ref();
    let path_str = path.display();

    let contents = match fs::read_to_string(path) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("Error reading {}: {}", path_str, e);
            exit(-1);
        }
    };

    let mut speller = match SpellChecker::new(wordlists) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("Error initializing aspell: {}", e);
            exit(-1);
        }
    };

    let regions: Box<dyn Iterator<Item = LineRegion<'_>>> = match path
        .extension()
        .and_then(OsStr::to_str)
    {
        Some("c" | "h") => Box::new(extract_regions_treesitter(
            &contents,
            tree_sitter_c::language(),
            include_str!("../queries/c.scm"),
        )),
        Some("cc" | "cpp" | "cxx" | "hh" | "hpp" | "hxx") => Box::new(extract_regions_treesitter(
            &contents,
            tree_sitter_cpp::language(),
            include_str!("../queries/c.scm"),
        )),
        Some("py") => Box::new(extract_regions_treesitter(
            &contents,
            tree_sitter_python::language(),
            include_str!("../queries/python.scm"),
        )),
        _ => Box::new(extract_regions_text(&contents)),
    };

    let mut errors = 0;

    regions.for_each(|r| {
        speller.check_line(r.text).for_each(|(index, len)| {
            errors += 1;

            let join_str;
            let spell_error_str = if context {
                join_str = [
                    &r.text[..index],
                    "\x1B[0;31m", // Red
                    &r.text[index..index + len],
                    "\x1B[0m", // Clear formatting
                    &r.text[index + len..],
                ]
                .join("");
                &join_str
            } else {
                &r.text[index..index + len]
            };

            println!(
                "{} ({},{}): {}",
                path_str,
                r.line,
                r.offset + index,
                spell_error_str
            );
        });
    });

    errors
}

struct LineRegion<'a> {
    line: usize,
    offset: usize,
    text: &'a str,
}

fn extract_regions_text(text: &str) -> impl Iterator<Item = LineRegion<'_>> {
    text.lines().enumerate().map(|(n, l)| LineRegion {
        line: n + 1,
        offset: 0,
        text: l,
    })
}

fn extract_regions_treesitter<'a>(
    text: &'a str,
    language: tree_sitter::Language,
    query: &str,
) -> impl Iterator<Item = LineRegion<'a>> {
    use tree_sitter::{Parser, Query, QueryCursor};

    let mut parser = Parser::new();

    parser
        .set_language(language)
        .expect("Error loading treesitter language");

    let tree = parser.parse(text, None).expect("Error parsing file");
    let root_node = tree.root_node();

    QueryCursor::new()
        .matches(
            &Query::new(language, query).expect("Error loading query"),
            root_node,
            text.as_bytes(),
        )
        .map(|m| m.captures[0].node)
        .flat_map(|n| {
            n.utf8_text(text.as_bytes())
                .expect("utf8 parsing error")
                .lines()
                .enumerate()
                .map(move |(i, l)| LineRegion {
                    line: n.start_position().row + i + 1,
                    offset: if i == 0 { n.start_position().column } else { 0 },
                    text: l,
                })
        })
        .collect::<Vec<_>>()
        .into_iter()
}

struct SpellChecker {
    doc_checker: *mut AspellDocumentChecker,
    spell_checker: *mut AspellSpeller,
}

impl SpellChecker {
    fn new(wordlists: &[PathBuf]) -> Result<Self, &'static str> {
        use cstr::cstr;
        use libaspell_sys::{
            aspell_config_replace, aspell_error_message, aspell_error_number, delete_aspell_config,
            delete_aspell_speller, new_aspell_config, new_aspell_document_checker,
            new_aspell_speller, to_aspell_document_checker, to_aspell_speller,
        };
        use std::ffi::{CStr, CString};

        let spell_checker = unsafe {
            let config = new_aspell_config();

            aspell_config_replace(config, cstr!("lang").as_ptr(), cstr!("en_US").as_ptr());
            aspell_config_replace(config, cstr!("camel-case").as_ptr(), cstr!("true").as_ptr());
            aspell_config_replace(
                config,
                cstr!("run-together").as_ptr(),
                cstr!("true").as_ptr(),
            );
            for l in wordlists {
                let list = CString::new(l.to_str().unwrap()).unwrap();
                aspell_config_replace(config, cstr!("add-wordlists").as_ptr(), list.as_ptr());
            }

            let result = new_aspell_speller(config);

            delete_aspell_config(config);

            if aspell_error_number(result) != 0 {
                return Err(CStr::from_ptr(aspell_error_message(result))
                    .to_str()
                    .unwrap());
            }

            to_aspell_speller(result)
        };

        let doc_checker = unsafe {
            let result = new_aspell_document_checker(spell_checker);

            if aspell_error_number(result) != 0 {
                delete_aspell_speller(spell_checker);
                return Err(CStr::from_ptr(aspell_error_message(result))
                    .to_str()
                    .unwrap());
            }

            to_aspell_document_checker(result)
        };

        Ok(SpellChecker {
            doc_checker,
            spell_checker,
        })
    }

    fn check_line<'a>(&'a mut self, line: &str) -> SpellCheckerErrors<'a> {
        use libaspell_sys::aspell_document_checker_process;
        unsafe {
            aspell_document_checker_process(
                self.doc_checker,
                line.as_ptr().cast::<i8>(),
                line.len().try_into().expect("Line longer than i32 max."),
            );
        }
        SpellCheckerErrors { checker: self }
    }
}

impl Drop for SpellChecker {
    fn drop(&mut self) {
        use libaspell_sys::{delete_aspell_document_checker, delete_aspell_speller};
        unsafe {
            delete_aspell_document_checker(self.doc_checker);
            delete_aspell_speller(self.spell_checker);
        }
    }
}

struct SpellCheckerErrors<'a> {
    checker: &'a mut SpellChecker,
}

impl<'a> Iterator for SpellCheckerErrors<'a> {
    type Item = (usize, usize);

    fn next(&mut self) -> Option<Self::Item> {
        use libaspell_sys::aspell_document_checker_next_misspelling;
        let token = unsafe { aspell_document_checker_next_misspelling(self.checker.doc_checker) };
        if token.len == 0 {
            None
        } else {
            Some((token.offset as usize, token.len as usize))
        }
    }
}
