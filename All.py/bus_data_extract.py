raw_file = input("Enter RAW file path: ").strip().replace('"', '')

with open(raw_file, "r", encoding="utf-8", errors="ignore") as f:
    lines = [line.strip() for line in f]

print("\nBUS DATA\n")

bus_start = False

for line in lines:

    if "BEGIN BUS DATA" in line:
        bus_start = True
        continue

    if "END OF BUS DATA" in line:
        break

    if not bus_start:
        continue

    if "'" not in line:
        continue

    try:

        data = [x.strip() for x in line.split(",")]

        bus_no = int(data[0])
        ide = int(data[3])
        vm = float(data[7])
        va = float(data[8])

        if ide == 1:
            bus_type = "PQ"
        elif ide == 2:
            bus_type = "PV"
        elif ide == 3:
            bus_type = "SLACK"
        else:
            bus_type = "UNKNOWN"

        print(f"Bus {bus_no:3d} | Type = {bus_type:5s} | V = {vm:.4f} pu | Angle = {va:.4f} deg")

    except:
        pass
