import os
import sys


def read_input(file_path):
    with open(file_path, 'r') as f:
        lines = f.read().strip().split('\n')
    
    # Read first line which is initial params
    D, R, T = map(int, lines[0].split())

    # Read resources
    resources = []
    for i in range(1, R + 1):
        parts = lines[i].split()
        resources.append({
            "RI": int(parts[0]), "RA": int(parts[1]), "RP": int(parts[2]), "RW": int(parts[3]),
            "RM": int(parts[4]), "RL": int(parts[5]), "RU": int(parts[6]), "RT": parts[7],
            "RE": int(parts[8]) if len(parts) > 8 else 0,
            "active_turns": int(parts[3]), "remaining_life": int(parts[5]), "stored_energy": 0  # Track resource state
        })
    
    # Read turns
    turns = []
    for i in range(R + 1, R + 1 + T):
        TM, TX, TR = map(int, lines[i].split())
        turns.append({"TM": TM, "TX": TX, "TR": TR})
    
    return D, resources, turns


def apply_special_effects(resources) -> dict:
    bonus = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0}
    for r in resources:
        if r["RT"] == "A":  # Smart Meter
            bonus['A'] += r["RE"]
        elif r["RT"] == "B":  # Distribution Facility
            bonus['B'] += r["RE"]
        elif r["RT"] == "C":  # Maintenance Plan
            bonus['C'] += r["RE"]
        elif r["RT"] == "D":  # Renewable Plant
            bonus['D'] += r["RE"]
        elif r["RT"] == "E":  # Accumulator
            bonus['E'] += r["RE"]
    return bonus


def simulate_game(D, resources, turns):
    active_resources = []
    output_lines = []
    score = 0

    for t in range(len(turns)):
        TM, TX, TR = turns[t]["TM"], turns[t]["TX"], turns[t]["TR"]

        # Apply special effects
        bonus_effect = apply_special_effects(active_resources)
        TM = TM + (TM * bonus_effect["B"] // 100)
        TX = TX + (TX * bonus_effect["B"] // 100)
        TR = TR + (TR * bonus_effect["D"] // 100)

        for r in active_resources:
            if r["RT"] == "A":
                r["RU"] += (r["RU"] * bonus_effect["A"] // 100)
            if r["RT"] == "C":
                r["remaining_life"] += (r["remaining_life"] * bonus_effect["C"] // 100)

        # Determine total buildings powered by current resources
        current_powered = sum(r["RU"] for r in active_resources if r["active_turns"] > 0)

        # Use stored energy from accumulators if any
        if current_powered < TX and bonus_effect["E"] > 0:
            deficit = TM - current_powered
            used_energy = min(deficit, bonus_effect["E"])
            current_powered += used_energy
            bonus_effect["E"] -= used_energy
        
        # # If current power is sufficient, limit purchases
        # if current_powered < TX:
        #     needed_buildings = TX - current_powered

        #     # Prioritize resources that give the best power-to-cost ratio
        #     affordable_resouces = sorted(
        #         [r for r in resources if r["RA"] <= D and r["RU"] > 0],
        #         key=lambda r: r["RA"] / max(1, r["RU"])
        #     )
        #     purchased_resources = []

        #     for res in affordable_resouces:
        #         # Ensure maintenance costs do not bankrupt the game
        #         projected_maintenance = sum(r["RP"] for r in active_resources if r["active_turns"] > 0)
        #         if D < projected_maintenance:
        #             break
        #         if D >= res["RA"] and needed_buildings > 0:
        #             D -= res["RA"]
        #             active_resources.append(res.copy())
        #             purchased_resources.append(str(res['RI']))
        #             needed_buildings -= res["RU"]
        
        # Purchase resources while maintaining sustainability
        needed_buildings = max(TM - current_powered, 0)
        affordable_resources = sorted(
            [r for r in resources if r["RA"] <= D and r["RU"] > 0 and D - r["RA"] >= sum(r["RP"] for r in active_resources)],
            key=lambda r: (r["RP"], r["RA"] / max(1, r["RU"]))
        )
        purchased_resources = []
        
        for res in affordable_resources:
            if D >= res["RA"] and needed_buildings > 0:
                D -= res["RA"]
                active_resources.append(res.copy())
                purchased_resources.append(str(res['RI']))
                needed_buildings -= res["RU"]

        if purchased_resources:
            print(f"{t} {len(purchased_resources)} {' '.join(purchased_resources)}")
            output_lines.append(f"{t} {len(purchased_resources)} {' '.join(purchased_resources)}")
        
        # Compute total buildings powered
        powered_buildings = sum(r["RU"] for r in active_resources if r["active_turns"] > 0)
        powered_buildings = min(powered_buildings, TX)

        # Compoute profit if the minum is met
        profit = powered_buildings * TR if powered_buildings >= TM else 0
        # print(powered_buildings, TM, TR, profit)
        # accumulate score (profit generated per turn)
        score += profit

        # Store excess power in accumulators
        excess_power = max(0, powered_buildings - TX)
        if (excess_power > 0 and bonus_effect["E"] > 0):
            bonus_effect["E"] += excess_power

        # Deduct periodic maintenance costs
        total_cost = sum(r["RP"] for r in active_resources if r["active_turns"] > 0)
        D += profit - total_cost

        # Update resource life cycle
        for r in active_resources[:]:  # Iterate over a copy to allow removal
            if r["active_turns"] > 0:
                r["active_turns"] -= 1
            elif r["active_turns"] == 0 and r["RM"] > 0:
                r["active_turns"] = -r["RM"]  # Enter maintenance mode
            elif r["active_turns"] < 0:
                r["active_turns"] += 1  # Maintenance countdown
                if r["active_turns"] == 0:
                    r["active_turns"] = r["RW"]  # Resume operation
            r["remaining_life"] -= 1
            if r["remaining_life"] == 0:
                active_resources.remove(r) # Remove expired resources

    return output_lines, score


def write_output(file_path, output_lines):
    with open(file_path, 'w') as f:
        f.write('\n'.join(output_lines) + '\n')


def main():

    if len(sys.argv) != 2:
        raise AssertionError("wrong number of input")
    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        raise FileNotFoundError("File not found")
    output_file = "output.txt"

    D, resouces, turns = read_input(input_file)
    output_lines, score = simulate_game(D, resouces, turns)
    print(f"Total Score is: {score}")
    write_output(output_file, output_lines)

if __name__ == "__main__":
    main()
