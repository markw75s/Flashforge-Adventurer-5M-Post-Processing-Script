#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Author        :   markw75s
# Date          :   26.06.2025
# Version       :   1.0
# License       :   MIT
# Description   :   Post-processing script that reorders a sliced .gcode file
#                   for the Flashforge Adventurer 5M 3D printer to ensure
#                   proper metadata display on the printer screen.
#                   It also includes an option to enable the
#                   spaghetti detector feature (enabled by default).
#                   Compatibility confirmed with: OrcaSlicer
# Source        :   https://github.com/markw75s/Flashforge-Adventurer-5M-Post-Processing-Script
# ---------------------------------------------------------------------------

import sys

input_path = sys.argv[1]
output_path = input_path

enable_spaghetti_detector = True # Enable/Disable the spaghetti detector (default: True)

print(">>> [Post-Processing Script for the Flashforge Adventurer 5M] <<<\n")
print(">>> Working... <<<")

with open(input_path, "r", encoding="utf-8") as file:
    lines = file.readlines()

thumbnail_block = []
header_block = []
config_block = []
pre_config_fields = []
main_gcode = []

in_config = False
in_thumbnail = False
in_header = False
collecting_pre_config = True

for line in lines:
    stripped = line.strip()

    # CONFIG block
    if stripped == "; CONFIG_BLOCK_START":
        in_config = True
        config_block.append("\n")
        config_block.append(line)
        continue
    elif stripped == "; CONFIG_BLOCK_END":
        config_block.append(line)
        config_block.append("\n")
        in_config = False
        continue
    elif in_config:
        config_block.append(line)
        continue

    # HEADER block
    if stripped == "; HEADER_BLOCK_START":
        in_header = True
        header_block.append("\n")
        header_block.append(line)
        continue
    elif stripped == "; HEADER_BLOCK_END":
        header_block.append(line)
        header_block.append("\n")
        in_header = False
        continue
    elif in_header:
        header_block.append(line)
        continue

    # THUMBNAIL block
    if stripped == "; THUMBNAIL_BLOCK_START":
        in_thumbnail = True
    elif stripped == "; THUMBNAIL_BLOCK_END":
        in_thumbnail = False

    if in_thumbnail or stripped == "; THUMBNAIL_BLOCK_END":
        thumbnail_block.append(line)
        continue

    # Pre-config comments (filament usage and estimated printing time)
    if collecting_pre_config:
        if any(field in stripped for field in [
            "; filament used [mm]", "; filament used [cm3]", "; filament used [g]",
            "; filament cost", "; total filament used [g]", "; total filament cost",
            "; total layers count", "; estimated printing time (normal mode)"
        ]):
            pre_config_fields.append(line)
            continue
        elif stripped == "; CONFIG_BLOCK_START":
            collecting_pre_config = False

    main_gcode.append(line)

# Add Spaghetti-Detector commands (using the comments from the slicer as marker)
final_gcode = []
for line in main_gcode:
    if enable_spaghetti_detector and "; filament start gcode" in line:
        final_gcode.append("M981 S1 P20000 ; Enable spaghetti detector\n")
    elif enable_spaghetti_detector and "; filament end gcode" in line:
        final_gcode.append("M981 S0 P20000 ; Disable spaghetti detector\n")
    final_gcode.append(line)

# Compile all modifications into the output file
final_output = []
for line in thumbnail_block:
    final_output.append(line)
    if line.strip() == "; THUMBNAIL_BLOCK_END":
        final_output.extend(header_block)
        final_output.extend(pre_config_fields)
        final_output.extend(config_block)

final_output.extend(final_gcode)

with open(output_path, "w", encoding="utf-8") as file:
    file.writelines(final_output)
    
print(">>> Post-Processing successfully completed! <<<")