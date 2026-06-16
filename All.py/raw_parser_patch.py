
import numpy as np

def load_from_raw(raw_file):
    print("Reading RAW file...")

    buses = []
    lines = []

    with open(raw_file, "r", encoding="utf-8", errors="ignore") as f:
        raw_lines = [x.strip() for x in f.readlines()]

    # Find BUS section
    bus_start = None
    for i, line in enumerate(raw_lines):
        if "BEGIN BUS DATA" in line.upper():
            bus_start = i + 2
            break

    if bus_start is None:
        # Older RAW formats (IEEE118)
        bus_start = 3

    # Read buses
    i = bus_start
    while i < len(raw_lines):
        line = raw_lines[i]
        if line.startswith("0"):
            break

        parts = [x.strip() for x in line.split(",")]
        try:
            bus_id = int(parts[0])
            ide = int(parts[3])

            buses.append({
                "id": bus_id,
                "type": {3:1, 2:2, 1:3}.get(ide, 3),  # Slack/PV/PQ mapping
                "V": float(parts[7]),
                "delta": np.radians(float(parts[8])),
                "P_sch": 0.0,
                "Q_sch": 0.0
            })
        except:
            pass
        i += 1

    print("Loaded buses =", len(buses))
    print("NOTE: Branch/Load/Generator parser still to be added.")
    return buses, lines
