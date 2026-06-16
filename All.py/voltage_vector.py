raw_file = input("Enter RAW file path: ").strip().replace('"', '')

with open(raw_file, "r", encoding="utf-8", errors="ignore") as f:
    lines = [line.strip() for line in f]

V = []
delta = []

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

        vm = float(data[7])
        va = float(data[8])

        V.append(vm)
        delta.append(va)

    except:
        pass

print("\nVoltage Vector V\n")
print(V)

print("\nAngle Vector Delta\n")
print(delta)
