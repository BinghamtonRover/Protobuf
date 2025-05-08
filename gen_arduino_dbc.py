"""
Generates C code from DBC files using cantools generate_c_source
"""

import os
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--sketch", "-s", type=str, required=True, help="Sketch name")
args = parser.parse_args()

destination = f"{args.sketch}/src/utils"
os.system(f'python -m cantools generate_c_source Protobuf/rover.dbc -o {destination} --use-float --bit-field')
