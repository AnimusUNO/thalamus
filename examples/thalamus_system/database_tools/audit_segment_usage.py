#!/usr/bin/env python3
"""
Thalamus Segment Usage Audit Utility

Copyright (C) 2025 Mark "Rizzn" Hopkins, Athena Vernal, John Casaretto

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
from database import get_unrefined_segments, get_refined_segments
import json

def audit_segment_integrity():
    print("Auditing segment integrity...\n")

    unrefined_ids = [seg['id'] for seg in get_unrefined_segments()]
    print(f"🔍 Unrefined Segment IDs: {sorted(unrefined_ids)}")

    refined = get_refined_segments()
    all_used_ids = set()
    duplicates = set()

    for ref in refined:
        source = ref['source_segments']
        if not source:
            continue
        try:
            raw_ids = json.loads(source)
            for rid in raw_ids:
                if rid in all_used_ids:
                    duplicates.add(rid)
                all_used_ids.add(rid)
        except Exception as e:
            print(f"⚠️ Error decoding source_segments for refined id {ref['id']}: {e}")

    print(f"\n✅ Total Used Segment IDs: {len(all_used_ids)}")
    print(f"⚠️ Duplicate Raw Segment IDs Across Refined Segments: {sorted(duplicates)}" if duplicates else "✔️ No duplicate raw segments in refined data.")

    reused_unrefined = [rid for rid in unrefined_ids if rid in all_used_ids]
    if reused_unrefined:
        print(f"\n🛑 THESE RAW SEGMENTS ARE UNREFINED *AND* ALREADY USED: {reused_unrefined}")
    else:
        print("✔️ All unrefined segments are clean (not reused).")

if __name__ == "__main__":
    audit_segment_integrity()
