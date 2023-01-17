use std::{
    fs::File,
    io::{ErrorKind, Read, Result, Seek, SeekFrom},
    path::PathBuf,
    time::{Duration, Instant},
};

const MIN_DURTION_BETWEEN_READS: Duration = Duration::from_secs(1);

struct Follow<T> {
    src: T,
    offset: u64,
    last_reached_end_at: Option<Instant>,
}

impl<T: Followable> Read for Follow<T> {
    fn read(&mut self, buf: &mut [u8]) -> Result<usize> {
        loop {
            let now = Instant::now();
            if let Some(last_reached_end_at) = self.last_reached_end_at {
                let delta = now.duration_since(last_reached_end_at);
                if delta < MIN_DURTION_BETWEEN_READS {
                    std::thread::sleep(MIN_DURTION_BETWEEN_READS - delta);
                    continue;
                }
            }

            let mut f = self.src.open()?;

            let size = f.seek(SeekFrom::End(0))?;
            if size < self.offset {
                // The src was truncated
                return Err(ErrorKind::UnexpectedEof.into());
            }

            if size == self.offset {
                self.last_reached_end_at = Some(now);
                continue;
            }

            f.seek(SeekFrom::Start(self.offset))?;

            let bytes_read = f.read(buf)?;
            self.offset += bytes_read as u64;

            if bytes_read < buf.len() {
                self.last_reached_end_at = Some(now);
            }

            return Ok(bytes_read);
        }
    }
}

pub trait Followable {
    type Output: Seek + Read;

    fn open(&self) -> Result<Self::Output>;
}

impl Followable for PathBuf {
    type Output = File;

    fn open(&self) -> Result<Self::Output> {
        File::open(self)
    }
}

/// Read the src and do not stop when end of file is reached, but rather to wait for additional data to be appended. Similar to `tail -f`.
pub fn follow<F: Followable>(src: F) -> impl Read {
    Follow {
        src,
        offset: 0,
        last_reached_end_at: None,
    }
}
