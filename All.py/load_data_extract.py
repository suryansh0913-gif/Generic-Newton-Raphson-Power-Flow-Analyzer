raw_file = input("Enter RAW file path: ").strip().replace('"', '')

with open(raw_file, "r", encoding="utf-8", errors="ignore") as f:
    lines = [line.strip() for line in f]

print("\nLOAD DATA\n")

load_start = False

for line in lines:

    if "BEGIN LOAD DATA" in line:
        load_start = True
        continue

    if "END OF LOAD DATA" in line:
        break

    if not load_start:
        continue

    if not line:
        continue

    try:

        data = [x.strip() for x in line.split(",")]

        bus_no = int(data[0])

        PL = float(data[5])
        QL = float(data[6])

        if PL != 0 or QL != 0:

            print(
                f"Bus {bus_no:3d} | "
                f"PL = {PL:.4f} MW | "
                f"QL = {QL:.4f} MVAR"
            )

    except:
        pass
