use std::path::{Path, PathBuf};

/// Splits [`Path`] into two parts separated by `target`. The `target` itself is included
/// in the end of first part.
/// 
/// ```
/// # use std::path::Path;
/// # use bazelci_agent::utils::split_path_inclusive;
///
/// let path = Path::new("a/b/c");
/// let (first, second) = split_path_inclusive(path, "b").unwrap();
/// assert_eq!(first, Path::new("a/b"));
/// assert_eq!(second, Path::new("c"));
/// ```
///
pub fn split_path_inclusive(path: &Path, target: &str) -> Option<(PathBuf, PathBuf)> {
    let mut iter = path.iter();

    let mut first = PathBuf::new();
    let mut found = false;
    while let Some(comp) = iter.next() {
        first.push(Path::new(comp));
        if comp == target {
            found = true;
            break;
        }
    }

    if found {
    let second: PathBuf = iter.collect();
    Some((first, second))

    } else {
        None
    }
}