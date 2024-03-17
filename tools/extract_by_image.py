# Extract a spectrogram for every image in the specified folder.
# This is typically used after searching, which generates images.
# Delete the images you don't want to keep, then run this to import the rest as training data.
# Two image file name formats are supported:
# 1) "rank~filename-offset~distance.png", e.g. "2~XC1000-95.00~0.067.png" for offset 95 of recording XC1000.mp3,
#    which is the second closest match at distance .067. This is the format generated by search.py.
# 2) "filename-offset.png", e.g. "XC1000-4.5.png" for offset 4.5 of recording XC1000.mp3.
#    This is the format generated by plot_from_db.py.

import argparse
import inspect
import os
import re
import shutil
import sys
import time
from pathlib import Path

# this is necessary before importing from a peer directory
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from core import extractor
from core import util

class ExtractByImage(extractor.Extractor):
    def __init__(self, audio_path, images_path, db_name, source, category, species_name, species_code, low_band, dest_dir):
        super().__init__(audio_path, db_name, source, category, species_name, species_code, low_band)
        self.images_path = images_path
        self.dest_dir = dest_dir

    # get list of specs from directory of images
    def _process_image_dir(self):
        self.offsets = {}
        for image_path in Path().glob(f"{self.images_path}/*.png"):
            name = Path(image_path).stem
            if '~' in name:
                result = re.split("\S+~(.+)~.*", name)
                result = re.split("(.+)-(.+)", result[1])
            else:
                result = re.split("(.+)-(.+)", name)
                if len(result) != 4:
                    result = re.split("(\S+)_(\S+)", name)

            if len(result) != 4:
                print(f"Error: unknown file name format: {image_path}")
                continue
            else:
                file_name = result[1]
                offset = float(result[2])

            if file_name not in self.offsets:
                self.offsets[file_name] = []

            self.offsets[file_name].append(offset)

    def run(self):
        self._process_image_dir()
        num_inserted = 0
        for recording_path in self.get_recording_paths():
            filename = Path(recording_path).stem
            if filename not in self.offsets:
                continue

            if self.dest_dir is not None:
                dest_path = os.path.join(self.dest_dir, Path(recording_path).name)
                if not os.path.exists(dest_path):
                    shutil.copy(recording_path, dest_path)

            print(f"Processing {recording_path}")
            num_inserted += self.insert_spectrograms(recording_path, self.offsets[filename])

        print(f"Inserted {num_inserted} spectrograms.")

if __name__ == '__main__':

    # command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', type=str, default=None, help='Source of recordings. By default, use the file names to get the source.')
    parser.add_argument('-b', type=str, default='bird', help='Category. Default = "bird"')
    parser.add_argument('-c', type=str, default=None, help='Species code (required)')
    parser.add_argument('-d', type=str, default=None, help='Directory containing recordings (required).')
    parser.add_argument('-e', type=str, default=None, help='Directory to copy recordings to (optional).')
    parser.add_argument('-f', type=str, default='training', help='Database name or full path ending in ".db". Default = "training"')
    parser.add_argument('-i', type=str, default=None, help='Directory containing spectrogram images (required).')
    parser.add_argument('-l', type=int, default=0, help='1 = low band (default=0)')
    parser.add_argument('-s', type=str, default=None, help='Species name (required)')

    args = parser.parse_args()
    if args.d is None:
        print("Error: -d argument is required (directory containing recordings).")
        quit()
    else:
        audio_path = args.d

    if args.i is None:
        print("Error: -i argument is required (directory containing images).")
        quit()
    else:
        image_path = args.i

    if args.s is None:
        print("Error: -s argument is required (species name).")
        quit()
    else:
        species_name = args.s

    if args.c is None:
        print("Error: -c argument is required (species code).")
        quit()
    else:
        species_code = args.c

    run_start_time = time.time()

    ExtractByImage(audio_path, image_path, args.f, args.a, args.b, species_name, species_code, args.l, args.e).run()

    elapsed = time.time() - run_start_time
    print(f'elapsed seconds = {elapsed:.1f}')
