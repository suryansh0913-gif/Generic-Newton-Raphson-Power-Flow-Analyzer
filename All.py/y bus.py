import numpy as np

raw_file = input("Enter RAW file path: ").strip().replace('"', '')

with open(raw_file, "r", encoding="utf-8", errors="ignore") as f:
    lines = [line.strip() for line in f]

buses = []
bus_section = False

for line in lines:

    if "BEGIN LOAD DATA" in line:
        break

    if "'" in line and "," in line:
        try:
            bus_no = int(line.split(",")[0])
            buses.append(bus_no)
        except:
            pass

bus_map = {bus: i for i, bus in enumerate(sorted(buses))}
nbus = len(bus_map)

print("Total Buses =", nbus)

Ybus = np.zeros((nbus, nbus), dtype=complex)

branch_start = False

for line in lines:

    if "BEGIN BRANCH DATA" in line:
        branch_start = True
        continue

    if "END OF BRANCH DATA" in line:
        break

    if not branch_start:
        continue

    if not line:
        continue

    try:

        data = [x.strip() for x in line.split(",")]

        fb = int(data[0])
        tb = int(data[1])

        R = float(data[3])
        X = float(data[4])
        B = float(data[5])

        y = 1 / complex(R, X)

        i = bus_map[fb]
        j = bus_map[tb]

       
        Ybus[i, j] -= y
        Ybus[j, i] -= y

        Ybus[i, i] += y + 1j * (B / 2)
        Ybus[j, j] += y + 1j * (B / 2)

    except:
        pass

print("\nY-BUS MATRIX\n")

for row in Ybus:
    print(["{:.4f}{:+.4f}j".format(z.real, z.imag) for z in row])

with open("Ybus.csv", "w") as f:

    for row in Ybus:

        line = []

        for z in row:
            line.append(f"{z.real:.6f}+j{z.imag:.6f}")

        f.write(",".join(line) + "\n")

print("\nYbus.csv saved successfully.")
