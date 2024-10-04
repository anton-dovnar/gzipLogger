import gzip
import logging
from pathlib import Path


class GZipRotator:
    def __call__(self, source: str, dest: str) -> None:
        source_path = Path(source)
        dest_path = Path(dest)
        gz_path = f"{dest_path}.gz"

        try:
            source_path.rename(dest_path)
            with dest_path.open('rb') as f_in:
                with gzip.open(gz_path, 'wb') as f_out:
                    f_out.writelines(f_in)
        except Exception as e:
            logging.error(f"Error compressing log file: {e}")
