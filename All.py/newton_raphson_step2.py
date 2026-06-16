import numpy as np
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

        if bus_no <= 3:
            print("\nBUS RAW DATA:")
            print(data)

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

V = np.array([bus_info[b]["V"] for b in sorted(bus_info)], dtype=float)

# Degree se radian me convert
delta = np.radians(
    np.array([bus_info[b]["delta"] for b in sorted(bus_info)], dtype=float)
)

print("\nVoltage Vector:")
print(V)

print("\nAngle Vector:")
print(delta)

# =====================================
# Y-BUS FORMATION
# =====================================

import numpy as np

bus_numbers = sorted(bus_info.keys())

bus_map = {bus: i for i, bus in enumerate(bus_numbers)}

nbus = len(bus_numbers)

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

print("\nY-BUS SIZE =", Ybus.shape)

print("\nFIRST 5 x 5 Y-BUS BLOCK\n")

for row in Ybus[:5, :5]:
    print(["{:.4f}{:+.4f}j".format(z.real, z.imag) for z in row])

# =====================================
# Pcalc Qcalc
# =====================================

G = Ybus.real
B = Ybus.imag

Pcalc = np.zeros(nbus)
Qcalc = np.zeros(nbus)

for i in range(nbus):

    for j in range(nbus):

        theta = delta[i] - delta[j]

        Pcalc[i] += (
            V[i] * V[j] *
            (
                G[i, j] * np.cos(theta)
                +
                B[i, j] * np.sin(theta)
            )
        )

        Qcalc[i] += (
            V[i] * V[j] *
            (
                G[i, j] * np.sin(theta)
                -
                B[i, j] * np.cos(theta)
            )
        )

print("\nPcalc\n")

for i in range(nbus):
    print(f"Bus {i+1:2d} : {Pcalc[i]:.6f}")

print("\nQcalc\n")

for i in range(nbus):
    print(f"Bus {i+1:2d} : {Qcalc[i]:.6f}")

    # =====================================
# MISMATCH VECTOR
# =====================================

Pspec = np.zeros(nbus)
Qspec = np.zeros(nbus)

for bus in bus_numbers:

    idx = bus_map[bus]

    Pspec[idx] = PG.get(bus, 0) - PL.get(bus, 0)
    Qspec[idx] = QG.get(bus, 0) - QL.get(bus, 0)

dP = Pspec - Pcalc
dQ = Qspec - Qcalc

print("\nDELTA P\n")

for i in range(nbus):
    print(f"Bus {i+1:2d} : {dP[i]:.6f}")

print("\nDELTA Q\n")

for i in range(nbus):
    print(f"Bus {i+1:2d} : {dQ[i]:.6f}")
    # =====================================
# BUS TYPE LISTS
# =====================================

slack_buses = []
pv_buses = []
pq_buses = []

for bus in sorted(bus_info):

    btype = bus_info[bus]["type"]

    if btype == "SLACK":
        slack_buses.append(bus)

    elif btype == "PV":
        pv_buses.append(bus)

    elif btype == "PQ":
        pq_buses.append(bus)

print("\nSLACK BUSES :", slack_buses)
print("PV BUSES    :", pv_buses)
print("PQ BUSES    :", pq_buses)

print("\nCounts")
print("Slack =", len(slack_buses))
print("PV    =", len(pv_buses))
print("PQ    =", len(pq_buses))
# =====================================
# NR STATE VECTOR INFO
# =====================================

angle_buses = pv_buses + pq_buses

n_angle = len(angle_buses)
n_voltage = len(pq_buses)

print("\nANGLE BUSES :", angle_buses)
print("PQ BUSES    :", pq_buses)

print("\nUnknown Angles =", n_angle)
print("Unknown Voltages =", n_voltage)

jacobian_size = n_angle + n_voltage

print("\nJacobian Size =",
      jacobian_size, "x", jacobian_size)
