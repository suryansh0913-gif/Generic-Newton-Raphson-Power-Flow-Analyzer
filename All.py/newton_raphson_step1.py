raw_file = input("Enter RAW file path: ").strip().replace('"', '')

with open(raw_file, "r", encoding="utf-8", errors="ignore") as f:
    lines = [line.strip() for line in f]

# =====================================
# BUS DATA
# =====================================

bus_info = {}

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

        bus_info[bus_no] = {
            "type": bus_type,
            "V": vm,
            "delta": va
        }

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

        PG[bus] = PG.get(bus, 0) + float(data[2])
        QG[bus] = QG.get(bus, 0) + float(data[3])

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

        PL[bus] = PL.get(bus, 0) + float(data[5])
        QL[bus] = QL.get(bus, 0) + float(data[6])

    except:
        pass

# =====================================
# DISPLAY BUS SUMMARY
# =====================================

print("\nBUS SUMMARY\n")

for bus in sorted(bus_info):

    pspec = PG.get(bus, 0) - PL.get(bus, 0)
    qspec = QG.get(bus, 0) - QL.get(bus, 0)

    print(
        f"Bus {bus:2d} | "
        f"{bus_info[bus]['type']:5s} | "
        f"V={bus_info[bus]['V']:.4f} | "
        f"d={bus_info[bus]['delta']:.4f} | "
        f"Pspec={pspec:.4f} | "
        f"Qspec={qspec:.4f}"
    )

# =====================================
# VOLTAGE VECTORS
# =====================================

V = [bus_info[b]["V"] for b in sorted(bus_info)]
delta = [bus_info[b]["delta"] for b in sorted(bus_info)]

print("\nVoltage Vector:")
print(V)

print("\nAngle Vector:")
print(delta)
