import numpy as np
import csv
import os

def load_from_file(filepath):

    buses = []
    lines = []

    bus_file = filepath + "_BusData.csv"
    line_file = filepath + "_BranchData.csv"

    if not os.path.exists(bus_file) or not os.path.exists(line_file):
        print(f"Couldn't find {bus_file} or {line_file}")
        return None, None
    
    with open(bus_file, newline="") as f:
        for row in csv.DictReader(f):
            buses.append({
                "id": int(row["Bus No"]),
                "type": int(row["Type"]),
                "V": float(row["Voltage(pu)"]),
                "delta": float(row["Angle(deg)"]) * np.pi / 180,
                "P_sch": 0.0,
                "Q_sch": 0.0,
            })
    with open(line_file, newline="") as f:
        for row in csv.DictReader(f):
            lines.append({
                "from": int(row["From Bus"]),
                "to": int(row["To Bus"]),
                "R": float(row["R"]),
                "X": float(row["X"]),
                "B_shunt": float(row["B"]),
            })

    print(f"Loaded {len(buses)} buses and {len(lines)} lines.")
    return buses, lines


def load_from_raw(raw_file):

    print("Reading RAW file...")

    buses = []
    lines = []

    section = "BUS"

    with open(raw_file, "r", encoding="utf-8", errors="ignore") as f:

        for line in f:
            print("LINE =", line[:80])
            if "BRANCH" in line.upper():
                print("FOUND BRANCH =",line)
            
            line = line.strip()

            if not line:
                continue

            if "END OF BUS DATA" in line.upper():
                section = None
                continue

            if "BEGIN LOAD DATA" in line.upper():
                section = "LOAD"
                continue

            if "END OF LOAD DATA" in line.upper():
                section = None
                continue

            if "BEGIN GENERATOR DATA" in line.upper():
                section = "GEN"
                continue

            if "END OF GENERATOR DATA" in line.upper():
                if "BEGIN BRANCH DATA" in line.upper():
                    section = "BRANCH"
                    print("BRANCH SECTION STARTED")
                else:
                    section = None

                continue
            
            if "BEGIN BRANCH DATA" in line.upper():
                section = "BRANCH"
                print("BRANCH SECTION STARTED")
                continue
            
            if "END OF BRANCH DATA" in line.upper():
                section = None
                continue

            if line.startswith("0") and "BEGIN BRANCH DATA" not in line.upper():
                continue
                
            if section == "BUS" and "'" in line:

                parts = [x.strip() for x in line.split(",")]

                try:
                    buses.append({
                        "id": int(parts[0]),
                        "type": int(parts[3]),
                        "V": float(parts[7]),
                        "delta": float(parts[8]) * np.pi / 180,
                        "P_sch": 0.0,
                        "Q_sch": 0.0
                    })
                except:
                    pass

            elif section == "BRANCH":
                
                print("INSIDE BRANCH")
                parts = [x.strip() for x in line.split(",")]
                print("PARTS =", parts)

                try:
                    lines.append({
                        "from": int(parts[0]),
                        "to": int(parts[1]),
                        "R": float(parts[3]),
                        "X": float(parts[4]),
                        "B_shunt": float(parts[5])
                    })

                    print("LINE ADDED =", len(lines))
                except Exception as e:
                    print("ERROR =", e)
                    print("LINE =", line)
                    pass

                parts = [x.strip() for x in line.split(",")]

                try:
                    lines.append({
                        "from": int(parts[0]),
                        "to": int(parts[1]),
                        "R": float(parts[3]),
                        "X": float(parts[4]),
                        "B_shunt": float(parts[5])
                    })
                except:
                    pass
    print("LINES COUNT =", len(lines))

    print(f"\nLoaded {len(buses)} buses and {len(lines)} lines from RAW file")

    return buses, lines
def load_from_user():
    n_buses = int(input("Number of buses: "))
    n_lines = int(input("Number of lines: "))

    buses = []
    print("\nBus types: 1 = Slack,  2 = PV,  3 = PQ")
    for i in range(n_buses):
        print(f"\nBus {i+1}")
        bus_id = int(input("  Bus number: "))
        bus_type = int(input("  Type (1/2/3): "))
        V = float(input("  Voltage magnitude (pu): "))
        delta_deg = float(input("  Voltage angle (deg): "))
        P_gen = float(input("  P generated (pu): "))
        Q_gen = float(input("  Q generated (pu): "))
        P_load = float(input("  P load (pu): "))
        Q_load = float(input("  Q load (pu): "))
        buses.append({
            "id": bus_id,
            "type": bus_type,
            "V": V,
            "delta": delta_deg * np.pi / 180,
            "P_sch": P_gen - P_load,
            "Q_sch": Q_gen - Q_load,
        })

    lines = []
    print("\nLine data (per unit):")
    for i in range(n_lines):
        print(f"\nLine {i+1}")
        from_bus = int(input("  From bus: "))
        to_bus = int(input("  To bus: "))
        R = float(input("  R (pu): "))
        X = float(input("  X (pu): "))
        B = float(input("  B shunt (pu), enter 0 if none: "))
        lines.append({
            "from": from_bus,
            "to": to_bus,
            "R": R,
            "X": X,
            "B_shunt": B,
        })

    return buses, lines


def build_ybus(buses, lines):

    # builds the admittance matrix from the line data
    # diagonal = sum of admittances at that bus
    # off-diagonal = negative of the line admittance between i and j
    n = len(buses)
    bus_idx = {b["id"]: i for i, b in enumerate(buses)}
    Y = np.zeros((n, n), dtype=complex)

    for line in lines:
        i = bus_idx[line["from"]]
        j = bus_idx[line["to"]]
        y = 1.0 / complex(line["R"], line["X"])
        ysh = complex(0, line["B_shunt"] / 2)

        Y[i][i] += y + ysh
        Y[j][j] += y + ysh
        Y[i][j] -= y
        Y[j][i] -= y
    print("\n" + "="*60)
    print("Y-BUS MATRIX")
    print("="*60)

    np.set_printoptions(precision=4, suppress=True)
    print("Y-Bus Shape =", Y.shape)
    print(Y[:10,:10])

    return Y, bus_idx


def gauss_seidel(buses, lines, tol=1e-6, max_iter=100):
    print("\n--- Gauss-Seidel ---")

    Y, bus_idx = build_ybus(buses, lines)
    n = len(buses)

    # start with the initial guesses given (flat start if user entered 1.0, 0.0)
    V = np.array([b["V"] * np.exp(1j * b["delta"]) for b in buses], dtype=complex)

    slack_buses = [bus_idx[b["id"]] for b in buses if b["type"] == 1]
    if not slack_buses:
        print("No slack bus defined. Exiting.")
        return None

    converged = False
    for itr in range(1, max_iter + 1):
        V_prev = V.copy()

        for bus in buses:
            k = bus_idx[bus["id"]]

            if bus["type"] == 1:
                continue  # slack bus is fixed

            P_sch = bus["P_sch"]
            Q_sch = bus["Q_sch"]

            # sum everything except the k-th term
            sum_YV = sum(Y[k][j] * V[j] for j in range(n) if j != k)

            if bus["type"] == 3:
                # PQ bus: update voltage directly
                V[k] = (1.0 / Y[k][k]) * ((P_sch - 1j * Q_sch) / np.conj(V[k]) - sum_YV)

            elif bus["type"] == 2:
                # PV bus: compute Q first, update voltage, then restore |V|
                Q_calc = -np.imag(np.conj(V[k]) * (Y[k][k] * V[k] + sum_YV))
                V_new = (1.0 / Y[k][k]) * ((P_sch - 1j * Q_calc) / np.conj(V[k]) - sum_YV)
                V[k] = bus["V"] * V_new / abs(V_new)

        max_change = np.max(np.abs(V - V_prev))
        print(f"  iter {itr:3d}  |  max dV = {max_change:.4e}")

        if max_change < tol:
            converged = True
            print(f"\nConverged after {itr} iterations.\n")
            break

    if not converged:
        print(f"\nDid not converge in {max_iter} iterations.\n")

    print_results(buses, V, Y, bus_idx, "Gauss-Seidel")
    return V


def newton_raphson(buses, lines, tol=1e-6, max_iter=20):
    print("\n--- Newton-Raphson ---")

    Y, bus_idx = build_ybus(buses, lines)
    n = len(buses)

    G = np.real(Y)
    B = np.imag(Y)

    delta = np.array([b["delta"] for b in buses])
    Vm = np.array([b["V"] for b in buses])

    slack_list = [bus_idx[b["id"]] for b in buses if b["type"] == 3]
    if not slack_list:
        print("No slack bus defined. Exiting.")
        return None
    slack = slack_list[0]

    non_slack = [bus_idx[b["id"]] for b in buses if b["type"] != 3]
    pq = [bus_idx[b["id"]] for b in buses if b["type"] == 1]

    P_sch = np.array([b["P_sch"] for b in buses])
    Q_sch = np.array([b["Q_sch"] for b in buses])

    converged = False
    for itr in range(1, max_iter + 1):

        # calculate P and Q at each bus from current voltages
        Pcalc = np.zeros(n)
        Qcalc = np.zeros(n)
        for i in range(n):
            for j in range(n):
                th = delta[i] - delta[j]
                Pcalc[i] += Vm[i] * Vm[j] * (G[i][j] * np.cos(th) + B[i][j] * np.sin(th))
                Qcalc[i] += Vm[i] * Vm[j] * (G[i][j] * np.sin(th) - B[i][j] * np.cos(th))

        # mismatch
        dP = (P_sch - Pcalc)[non_slack]
        dQ = (Q_sch - Qcalc)[pq]
        mismatch = np.max(np.abs(np.concatenate([dP, dQ])))
        print(f"  iter {itr:3d}  |  max mismatch = {mismatch:.4e}")

        if mismatch < tol:
            converged = True
            print(f"\nConverged after {itr} iterations.\n")
            break

        # build the Jacobian (4 sub-matrices)
        J1 = np.zeros((n, n))
        J2 = np.zeros((n, n))
        J3 = np.zeros((n, n))
        J4 = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                th = delta[i] - delta[j]
                if i != j:
                    J1[i][j] = Vm[i] * Vm[j] * (G[i][j] * np.sin(th) - B[i][j] * np.cos(th))
                    J2[i][j] = Vm[i] * Vm[j] * (G[i][j] * np.cos(th) + B[i][j] * np.sin(th))
                    J3[i][j] = -J2[i][j]
                    J4[i][j] = J1[i][j]
                else:
                    J1[i][i] = -Qcalc[i] - B[i][i] * Vm[i]**2
                    J2[i][i] = Pcalc[i] + G[i][i] * Vm[i]**2
                    J3[i][i] = Pcalc[i] - G[i][i] * Vm[i]**2
                    J4[i][i] = Qcalc[i] - B[i][i] * Vm[i]**2

        # trim rows/cols for slack and PV buses
        J = np.block([
            [J1[np.ix_(non_slack, non_slack)], J2[np.ix_(non_slack, pq)]],
            [J3[np.ix_(pq, non_slack)],        J4[np.ix_(pq, pq)]]
        ])
        if itr == 1:
                print("\n" + "="*60)
                print("JACOBIAN MATRIX (Iteration 1)")
                print("="*60)
                print("Jacobian Shape =", J.shape)
                print(J[:10,:10])

        try:
            x = np.linalg.solve(J, np.concatenate([dP, dQ]))
        except np.linalg.LinAlgError:
            print("Jacobian is singular, can't continue.")
            return None

        # update angles and magnitudes
        n_ns = len(non_slack)
        for k, i in enumerate(non_slack):
            delta[i] += x[k]
        for k, i in enumerate(pq):
            Vm[i] += x[n_ns + k] * Vm[i]

    if not converged:
        print(f"\nDid not converge in {max_iter} iterations.\n")

    V = Vm * np.exp(1j * delta)
    
    print_results(buses, V, Y, bus_idx, "Newton-Raphson")
    
    calculate_line_losses(lines, V, bus_idx)
    
    return V


def print_results(buses, V, Y, bus_idx, method):
    n = len(buses)
    print(f"Results ({method}):\n")
    print(f"  {'Bus':>4}  {'Type':>6}  {'|V| pu':>8}  {'Angle deg':>10}  {'P inj pu':>10}  {'Q inj pu':>10}")
    print("  " + "-" * 58)
    for bus in buses:
        k = bus_idx[bus["id"]]
        Vk = V[k]
        Ik = sum(Y[k][j] * V[j] for j in range(n))
        S = Vk * np.conj(Ik)
        btype = {1: "PQ", 2: "PV", 3: "Slack"}.get(bus["type"], "?")
        print(f"  {bus['id']:>4}  {btype:>6}  {abs(Vk):>8.5f}  {np.angle(Vk, deg=True):>10.4f}"
              f"  {np.real(S):>10.6f}  {np.imag(S):>10.6f}")
    print()

    def calculate_line_losses(lines, V, bus_idx):

        print("\n" + "="*70)
        print("TRANSMISSION LINE LOSSES")
        print("="*70)

    total_P_loss = 0
    total_Q_loss = 0

    print(f"{'From':>6} {'To':>6} {'P_loss':>12} {'Q_loss':>12}")

    for line in lines:

        i = bus_idx[line["from"]]
        j = bus_idx[line["to"]]

        z = complex(line["R"], line["X"])
        y = 1 / z

        Vi = V[i]
        Vj = V[j]

        Iij = (Vi - Vj) * y
        Iji = (Vj - Vi) * y

        Sij = Vi * np.conj(Iij)
        Sji = Vj * np.conj(Iji)

        Sloss = Sij + Sji

        P_loss = np.real(Sloss)
        Q_loss = np.imag(Sloss)

        total_P_loss += P_loss
        total_Q_loss += Q_loss

        print(f"{line['from']:>6} {line['to']:>6} "
              f"{P_loss:>12.6f} {Q_loss:>12.6f}")

    print("-"*70)
    print(f"TOTAL P LOSS = {total_P_loss:.6f} pu")
    print(f"TOTAL Q LOSS = {total_Q_loss:.6f} pu")
    


def main():

    print("Power Flow Analysis - Newton-Raphson & Gauss-Seidel\n")

    print("1. CSV File")
    print("2. RAW File")

    choice = input("Choice: ").strip()

    if choice == "1":

        prefix = input("Enter file prefix path: ").strip().replace('"','')
        buses, lines = load_from_file(prefix)

    elif choice == "2":

        raw_file = input("Enter RAW file path: ").strip().replace('"','')
        buses, lines = load_from_raw(raw_file)

    else:
        print("Invalid choice")
        return

    if buses is None:
        return

    newton_raphson(buses, lines)


if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")
