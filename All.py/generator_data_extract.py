raw_file = input("Enter RAW file path: ").strip().replace('"', '')

with open(raw_file, "r", encoding="utf-8", errors="ignore") as f:
    lines = [line.strip() for line in f]

print("\nGENERATOR DATA\n")

gen_start = False

for line in lines:

    if "BEGIN GENERATOR DATA" in line:
        gen_start = True
        continue

    if "END OF GENERATOR DATA" in line:
        break

    if not gen_start:
        continue

    if not line:
        continue

    try:

        data = [x.strip() for x in line.split(",")]

        bus_no = int(data[0])

        pg = float(data[2])
        qg = float(data[3])

        print(
            f"Bus {bus_no:3d} | "
            f"PG = {pg:.4f} MW | "
            f"QG = {qg:.4f} MVAR"
        )

    except:
        pass
