import numpy as np
import csv
import os


def load_from_file(filepath):
    buses = []
    lines = []

    bus_file = filepath + "_buses.csv"
    line_file = filepath + "_lines.csv"

    if not os.path.exists(bus_file) or not os.path.exists(line_file):
        print(f"Couldn't find {bus_file} or {line_file}. Check the names and try again.")
        return None, None

    with open(bus_file, newline="") as f:
        for row in csv.DictReader(f):
            buses.append({
                "id": int(row["bus_id"]),
                "type": int(row["type"]),   # 1=Slack, 2=PV, 3=PQ
                "V": float(row["V_mag"]),
                "delta": float(row["V_angle_deg"]) * np.pi / 180,
                "P_sch": float(row["P_gen"]) - float(row["P_load"]),
                "Q_sch": float(row["Q_gen"]) - float(row["Q_load"]),
            })

    with open(line_file, newline="") as f:
        for row in csv.DictReader(f):
            lines.append({
                "from": int(row["from_bus"]),
                "to": int(row["to_bus"]),
                "R": float(row["R_pu"]),
                "X": float(row["X_pu"]),
                "B_shunt": float(row.get("B_shunt_pu", 0)),
            })

    print(f"Loaded {len(buses)} buses and {len(lines)} lines.")
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

    slack_list = [bus_idx[b["id"]] for b in buses if b["type"] == 1]
    if not slack_list:
        print("No slack bus defined. Exiting.")
        return None
    slack = slack_list[0]

    non_slack = [bus_idx[b["id"]] for b in buses if b["type"] != 1]
    pq = [bus_idx[b["id"]] for b in buses if b["type"] == 3]

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
        btype = {1: "Slack", 2: "PV", 3: "PQ"}.get(bus["type"], "?")
        print(f"  {bus['id']:>4}  {btype:>6}  {abs(Vk):>8.5f}  {np.angle(Vk, deg=True):>10.4f}"
              f"  {np.real(S):>10.6f}  {np.imag(S):>10.6f}")
    print()


def main():
    print("Power Flow Analysis — Newton-Raphson & Gauss-Seidel\n")

    print("Input data:")
    print("  1 - Load from CSV files")
    print("  2 - Enter manually")
    choice = input("\nChoice: ").strip()

    if choice == "1":
        prefix = input("File prefix (e.g. 'sample' for sample_buses.csv): ").strip()
        buses, lines = load_from_file(prefix)
        if buses is None:
            return
    elif choice == "2":
        buses, lines = load_from_user()
    else:
        print("Invalid choice.")
        return

    tol_in = input("\nTolerance (default 1e-6): ").strip()
    iter_in = input("Max iterations (default 50): ").strip()
    tol = float(tol_in) if tol_in else 1e-6
    max_iter = int(iter_in) if iter_in else 50

    print("\nWhich method?")
    print("  1 - Gauss-Seidel")
    print("  2 - Newton-Raphson")
    print("  3 - Both")
    method = input("\nChoice: ").strip()

    if method in ("1", "3"):
        gauss_seidel(buses, lines, tol=tol, max_iter=max_iter)
    if method in ("2", "3"):
        newton_raphson(buses, lines, tol=tol, max_iter=max_iter)
    if method not in ("1", "2", "3"):
        print("Invalid method choice.")


if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")