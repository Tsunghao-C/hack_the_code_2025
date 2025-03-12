import os
import sys

def read_input(file_path):
    """Reads the input file and parses the game parameters, resources, and turns."""
    with open(file_path, 'r') as f:
        lines = f.read().strip().split('\n')

    # Read initial parameters
    D, R, T = map(int, lines[0].split())

    # Read available resources
    resources = []
    for i in range(1, R + 1):
        parts = lines[i].split()
        resource = {
            "RI": int(parts[0]), "RA": int(parts[1]), "RP": int(parts[2]), "RW": int(parts[3]),
            "RM": int(parts[4]), "RL": int(parts[5]), "RU": int(parts[6]), "RT": parts[7],
            "RE": int(parts[8]) if len(parts) > 8 else 0  # Only present for special resources
        }
        resources.append(resource)

    # Read turns
    turns = []
    for i in range(R + 1, R + 1 + T):
        TM, TX, TR = map(int, lines[i].split())
        turns.append({"TM": TM, "TX": TX, "TR": TR})

    return D, resources, turns


def apply_special_effects(resources, base_value, key):
    """Applies the special effects of active resources to a given base value."""
    for res in resources:
        if res["RT"] in ["A", "B", "C", "D"] and res["RE"] > 0:
            if res["RT"] == "A" and key == "RU":
                base_value += int(base_value * (res["RE"] / 100))
            elif res["RT"] == "B" and key in ["TM", "TX"]:
                base_value += int(base_value * (res["RE"] / 100))
            elif res["RT"] == "C" and key == "RL":
                base_value += int(base_value * (res["RE"] / 100))
            elif res["RT"] == "D" and key == "TR":
                base_value += int(base_value * (res["RE"] / 100))
    return base_value


def simulate_game(D, resources, turns):
    """Simulates the game, managing purchases, maintenance costs, and profits."""
    active_resources = []
    output_lines = []
    score = 0

    for t, turn in enumerate(turns):
        TM, TX, TR = turn["TM"], turn["TX"], turn["TR"]

        # Apply special effects
        TM = apply_special_effects(active_resources, TM, "TM")
        TX = apply_special_effects(active_resources, TX, "TX")
        TR = apply_special_effects(active_resources, TR, "TR")

        # Purchase Strategy: Buy multiple resources per turn, prioritizing efficiency
        affordable_resources = [r for r in resources if r["RA"] <= D]
        affordable_resources.sort(key=lambda r: (r["RU"] / r["RA"], -r["RA"]), reverse=True)  # Sort by efficiency

        purchased_resources = []
        for res in affordable_resources:
            if D >= res["RA"]:
                purchased_resources.append(res["RI"])
                D -= res["RA"]
                active_resources.append(res.copy())

        if purchased_resources:
            output_lines.append(f"{t} {len(purchased_resources)} {' '.join(map(str, purchased_resources))}")

        # Compute powered buildings
        powered_buildings = sum(r["RU"] for r in active_resources if r["RW"] > 0)
        powered_buildings = min(powered_buildings, TX)

        # Compute profit
        profit = powered_buildings * TR if powered_buildings >= TM else 0
        score += profit

        # Deduct periodic maintenance costs
        total_cost = sum(r["RP"] for r in active_resources if r["RW"] > 0)
        D += profit - total_cost

        # Update resource life cycle
        for r in active_resources[:]:  # Iterate over a copy to modify the list safely
            r["RW"] -= 1
            if r["RW"] == 0:
                r["RW"] = r["RM"]
                if r["RL"] > 0:
                    r["RL"] -= 1
                if r["RL"] == 0:
                    active_resources.remove(r)  # Remove obsolete resource

    return output_lines, score


def write_output(file_path, output_lines):
    """Writes the game output to a file."""
    with open(file_path, 'w') as f:
        f.write('\n'.join(output_lines) + '\n')


def main():
    try:
        if len(sys.argv) != 2:
            raise AssertionError("Wrong number of input arguments")
        input_file = sys.argv[1]
        if not os.path.exists(input_file):
            raise FileNotFoundError("File not found")
        
        output_file = "output.txt"

        D, resources, turns = read_input(input_file)
        output_lines, score = simulate_game(D, resources, turns)
        print(f"Total Score: {score}")
        write_output(output_file, output_lines)

    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    main()