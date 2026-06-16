raw_file = input("Enter RAW file path: ").strip().replace('"', '')

with open(raw_file, "r", encoding="utf-8", errors="ignore") as f:
    lines = [line.strip() for line in f]

# =====================================
# BUS LIST
# =====================================

buses = []

bus_start = False

for line in lines:

    if "BEGIN BUS DATA" in line:
        bus_start = True
        continue

    if "END OF BUS DATA" in line:
        break

    if not bus_start:
        continue

    try:
        data = [x.strip() for x in line.split(",")]
        buses.append(int(data[0]))
    except:
        pass

# =====================================
# GENERATOR DATA
# =====================================

PG = {}
QG = {}

gen_start = False

for line in lines:

    if "BEGIN GENERATOR DATA" in line:
        gen_start = True
        continue

    if "END OF GENERATOR DATA" in line:
        break

    if not gen_start:
        continue

    try:

        data = [x.strip() for x in line.split(",")]

        bus = int(data[0])

        pg = float(data[2])
        qg = float(data[3])

        PG[bus] = PG.get(bus, 0) + pg
        QG[bus] = QG.get(bus, 0) + qg

    except:
        pass

# =====================================
# LOAD DATA
# =====================================

PL = {}
QL = {}

load_start = False

for line in lines:

    if "BEGIN LOAD DATA" in line:
        load_start = True
        continue

    if "END OF LOAD DATA" in line:
        break

    if not load_start:
        continue

    try:

        data = [x.strip() for x in line.split(",")]

        bus = int(data[0])

        pl = float(data[5])
        ql = float(data[6])

        PL[bus] = PL.get(bus, 0) + pl
        QL[bus] = QL.get(bus, 0) + ql

    except:
        pass

# =====================================
# PSPEC QSPEC
# =====================================

print("\nPSPEC AND QSPEC\n")

for bus in sorted(buses):

    pspec = PG.get(bus, 0) - PL.get(bus, 0)
    qspec = QG.get(bus, 0) - QL.get(bus, 0)

    print(
        f"Bus {bus:3d} | "
        f"Pspec = {pspec:10.4f} | "
        f"Qspec = {qspec:10.4f}"
    )
