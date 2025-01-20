import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
import glob


def load_data(metric_type="energy"):
    """
    Load data from CSV files for either energy or request metrics.

    Parameters:
        metric_type (str): Either "energy_history" or "request_stats"
    """
    dict_df = defaultdict(list)

    # Determine file pattern based on metric type
    pattern = f"../output/{metric_type}_*.csv"
    print(f"Looking for files matching pattern: {pattern}")

    files = glob.glob(pattern)
    if not files:
        print(f"No files found matching pattern: {pattern}")
        return dict_df

    print(f"Found {len(files)} files:")
    for file in files:
        print(f"Processing file: {file}")
        try:
            # Extract strategies from file name
            # Example filename: energy_history_AllOnStrategy_TimeGreedy_56.csv
            # or: request_stats_AllOnStrategy_TimeGreedy_56.csv
            parts = file.split("_")
            if len(parts) < 5:
                print(f"Skipping file {file} - unexpected filename format")
                continue

            power_strategy = parts[2]
            assignment_strategy = parts[3]
            user_count = int(parts[4].replace(".csv", ""))

            # Create a combined strategy key
            strategy_key = f"{power_strategy} + {assignment_strategy}"

            # Read the file into a DataFrame
            df = pd.read_csv(file)
            print(f"Loaded {file} with shape {df.shape}")

            # Store the data grouped by combined strategies
            dict_df[strategy_key].append(
                {
                    "user_count": user_count,
                    "power_strategy": power_strategy,
                    "assignment_strategy": assignment_strategy,
                    "data": df,
                }
            )

        except Exception as e:
            print(f"Error processing file {file}: {str(e)}")

    print(f"Loaded data for {len(dict_df)} strategy combinations")
    return dict_df


def plot_metrics(
    energy_dict, request_dict, power_strategy=None, assignment_strategy=None
):
    """
    Create a subplot with energy consumption and success rate metrics.

    Parameters:
        energy_dict (dict): Dictionary containing energy data
        request_dict (dict): Dictionary containing request data
        power_strategy (list or str): Power strategy/strategies to analyze
        assignment_strategy (list or str): Assignment strategy/strategies to analyze
    """
    # Ensure strategies are lists
    if isinstance(power_strategy, str):
        power_strategy = [power_strategy]
    if isinstance(assignment_strategy, str):
        assignment_strategy = [assignment_strategy]

    # Filter data by strategies
    def filter_data(data_dict):
        return {
            strategy_key: data
            for strategy_key, data in data_dict.items()
            if (not power_strategy or any(ps in strategy_key for ps in power_strategy))
            and (
                not assignment_strategy
                or any(as_ in strategy_key for as_ in assignment_strategy)
            )
        }

    filtered_energy = filter_data(energy_dict)
    filtered_request = filter_data(request_dict)

    # Create subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Define line styles
    line_styles = [
        ("solid", "o"),
        ("dashed", "s"),
        ("dashdot", "^"),
        ("dotted", "D"),
        ("-", "v"),
        ("--", "p"),
    ]

    # Plot energy data
    for idx, (strategy_key, data) in enumerate(filtered_energy.items()):
        user_counts = []
        energies = []

        for entry in data:
            total_energy = entry["data"].sum().sum()
            user_counts.append(entry["user_count"])
            energies.append(total_energy)

        # Sort the data
        sorted_data = sorted(zip(user_counts, energies))
        user_counts, energy_values = zip(*sorted_data)

        line_style, marker = line_styles[idx % len(line_styles)]
        ax1.plot(
            user_counts,
            energy_values,
            linestyle=line_style,
            marker=marker,
            markersize=8,
            label=strategy_key,
        )

    ax1.set_title("Energy Consumption vs Number of Users")
    ax1.set_xlabel("Number of Users")
    ax1.set_ylabel("Total Energy (J)")
    ax1.grid(True)
    ax1.legend(title="Strategies", bbox_to_anchor=(1.05, 1), loc="upper left")

    # Plot success rate data
    for idx, (strategy_key, data) in enumerate(filtered_request.items()):
        user_counts = []
        success_rates = []

        for entry in data:
            request_stats = entry["data"]
            completed_requests = request_stats[
                request_stats["status"] == "RequestStatus.COMPLETED"
            ].shape[0]
            failed_requests = request_stats[
                request_stats["status"] == "RequestStatus.FAILED"
            ].shape[0]

            total_requests = completed_requests + failed_requests
            success_rate = (
                (completed_requests / total_requests * 100) if total_requests > 0 else 0
            )

            user_counts.append(entry["user_count"])
            success_rates.append(success_rate)

        # Sort the data
        sorted_data = sorted(zip(user_counts, success_rates))
        user_counts, rates = zip(*sorted_data)

        line_style, marker = line_styles[idx % len(line_styles)]
        ax2.plot(
            user_counts,
            rates,
            linestyle=line_style,
            marker=marker,
            markersize=8,
            label=strategy_key,
        )

    ax2.set_title("Success Rate vs Number of Users")
    ax2.set_xlabel("Number of Users")
    ax2.set_ylabel("Success Rate (%)")
    ax2.grid(True)
    ax2.legend(title="Strategies", bbox_to_anchor=(1.05, 1), loc="upper left")

    plt.tight_layout()
    plt.show()


def normalize_values(values):
    """
    Normalize values to range [0, 1] using min-max normalization.
    """
    min_val = min(values)
    max_val = max(values)
    print(f"Min: {min_val}, Max: {max_val}")
    if max_val == min_val:
        return [1.0 for _ in values]  # All values are equal
    return [(x - min_val) / (max_val - min_val) for x in values]


def calculate_assignment_score(
    energy_value, success_rate, all_energies, all_success_rates
):
    """
    Calculate Assignment Score (AS*) using the formula:
    AS* = (0.5 X (1 - (E-Emin)/(Emax-Emin))) + (0.5 X TS/100)

    Parameters:
        energy_value: Energy consumption for this strategy (E)
        success_rate: Success rate for this strategy (TS)
        all_energies: List of energy values for all strategies
        all_success_rates: List of success rates for all strategies (not used anymore)
    """
    # Get minimum and maximum energy values
    e_min = min(all_energies)
    e_max = max(all_energies)

    # Avoid division by zero
    if e_max == e_min:
        energy_component = 0.5  # If all energies are equal
    else:
        # Normalize energy so that minimum energy gets highest score
        energy_component = 0.5 * (1 - (energy_value - e_min) / (e_max - e_min))

    # Success rate is already 0-100%
    success_component = success_rate / 100

    # Calculate final score
    return energy_component * success_component


def get_strategy_display_names():
    """
    Returns a dictionary mapping strategy keys to their display names.
    """
    return {
        # Assignment Strategies
        "TimeGreedyAssignment": "Time Greedy",
        "ClosestNodeAssignment": "Closest Node",
        "HAPSOnlyAssignment": "HAPS Only",
        "GA": "Genetic Algorithm",
        "PSO": "Particle Swarm",
        "DE": "Differential Evolution",
        "QLearningAssignment": "Q-Learning",
        # Power Strategies
        "OnDemand": "On Demand",
        "AllOnStrategy": "All On",
    }


def get_display_name(strategy_name):
    """
    Get the display name for a strategy.
    If no display name is found, returns the original name.
    """
    display_names = get_strategy_display_names()
    return display_names.get(strategy_name, strategy_name)


def print_combined_table(
    energy_dict,
    request_dict,
    user_count=None,
    power_strategy=None,
    assignment_strategy=None,
):
    """
    Print a combined table showing energy consumption, success rates, and combined score.
    """
    # Find available user counts
    available_counts = set()
    for strategy_data in energy_dict.values():
        available_counts.update(run["user_count"] for run in strategy_data)

    if not available_counts:
        print("No data available")
        return None

    # If user_count not specified or invalid, use the smallest available
    if user_count is None or user_count not in available_counts:
        user_count = min(available_counts)
        print(f"Using user count: {user_count}")
        print(f"Available user counts: {sorted(available_counts)}")

    results = []

    # First pass to collect all values for normalization
    all_energies = []
    all_success_rates = []
    temp_data = []

    # Collect data for each strategy pair
    strategy_keys = set()
    for key in set(energy_dict.keys()) & set(request_dict.keys()):
        power_strat, assign_strat = key.split(" + ")
        if (not power_strategy or power_strat in power_strategy) and (
            not assignment_strategy or assign_strat in assignment_strategy
        ):
            strategy_keys.add(key)

    for strategy_key in strategy_keys:
        energy_run = next(
            (
                run
                for run in energy_dict[strategy_key]
                if run["user_count"] == user_count
            ),
            None,
        )
        request_run = next(
            (
                run
                for run in request_dict[strategy_key]
                if run["user_count"] == user_count
            ),
            None,
        )

        if energy_run and request_run:
            # Calculate metrics
            total_energy = energy_run["data"].sum().sum()

            request_stats = request_run["data"]
            completed_requests = request_stats[
                request_stats["status"] == "RequestStatus.COMPLETED"
            ].shape[0]
            failed_requests = request_stats[
                request_stats["status"] == "RequestStatus.FAILED"
            ].shape[0]

            total_requests = completed_requests + failed_requests
            success_rate = (
                (completed_requests / total_requests * 100) if total_requests > 0 else 0
            )

            # Store values for normalization
            all_energies.append(total_energy)
            all_success_rates.append(success_rate)

            # Store temporary data
            temp_data.append(
                {
                    "strategy_key": strategy_key,
                    "total_energy": total_energy,
                    "success_rate": success_rate,
                    "completed_requests": completed_requests,
                    "failed_requests": failed_requests,
                }
            )

    # Calculate combined scores
    for data in temp_data:
        combined_score = calculate_assignment_score(
            data["total_energy"], data["success_rate"], all_energies, all_success_rates
        )

        # Split strategy key into components
        power_strat, assign_strat = data["strategy_key"].split(" + ")

        # Add to results
        results.append(
            {
                "Power Strategy": get_display_name(power_strat),
                "Assignment Strategy": get_display_name(assign_strat),
                "Total Energy (J)": data["total_energy"],
                "Success Rate": data["success_rate"],
                "Combined Score": combined_score,
                "Completed Requests": data["completed_requests"],
                "Failed Requests": data["failed_requests"],
            }
        )

    if not results:
        print(f"No data found for user count {user_count}")
        return None

    # Convert to DataFrame for nice display
    results_df = pd.DataFrame(results)

    # Sort by combined score (descending, as higher is better)
    results_df = results_df.sort_values("Combined Score", ascending=False)

    # Format the numeric columns
    results_df["Total Energy (J)"] = results_df["Total Energy (J)"].map(
        "{:,.2f}".format
    )
    results_df["Success Rate"] = results_df["Success Rate"].map("{:.2f}".format)
    results_df["Combined Score"] = results_df["Combined Score"].map("{:.3f}".format)

    # Rename columns for display
    results_df = results_df.rename(
        columns={
            "Success Rate": "Success Rate (%)",
        }
    )

    print(f"\nCombined Metrics for {user_count} Users:")
    print("=" * 120)
    print(results_df.to_string(index=False))
    print("=" * 120)
    print("\nNote: Assignment Score (AS*) = (0.5 X (1 - E/Emax)) + (0.5 X TS/100)")
    print("Higher Assignment Score is better")

    return results_df


def plot_efficiency_metrics(
    energy_dict, request_dict, power_strategy=None, assignment_strategy=None
):
    """
    Create a plot showing Energy/QoS ratio vs number of users.
    """
    # Ensure strategies are lists
    if isinstance(power_strategy, str):
        power_strategy = [power_strategy]
    if isinstance(assignment_strategy, str):
        assignment_strategy = [assignment_strategy]

    # Filter data by strategies
    def filter_data(data_dict):
        return {
            strategy_key: data
            for strategy_key, data in data_dict.items()
            if (not power_strategy or any(ps in strategy_key for ps in power_strategy))
            and (
                not assignment_strategy
                or any(as_ in strategy_key for as_ in assignment_strategy)
            )
        }

    filtered_energy = filter_data(energy_dict)
    filtered_request = filter_data(request_dict)

    # Create plot
    plt.figure(figsize=(12, 6))

    # Define line styles
    line_styles = [
        ("solid", "o"),
        ("dashed", "s"),
        ("dashdot", "^"),
        ("dotted", "D"),
        ("-", "v"),
        ("--", "p"),
    ]

    # Plot efficiency data
    for idx, strategy_key in enumerate(filtered_energy.keys()):
        if strategy_key not in filtered_request:
            continue

        user_counts = []
        efficiency_ratios = []

        energy_data = filtered_energy[strategy_key]
        request_data = filtered_request[strategy_key]

        # Match energy and request data by user count
        user_counts_set = set(run["user_count"] for run in energy_data)
        user_counts_set &= set(run["user_count"] for run in request_data)

        for user_count in sorted(user_counts_set):
            energy_run = next(
                run for run in energy_data if run["user_count"] == user_count
            )
            request_run = next(
                run for run in request_data if run["user_count"] == user_count
            )

            # Calculate metrics
            total_energy = energy_run["data"].sum().sum()

            request_stats = request_run["data"]
            completed = request_stats[
                request_stats["status"] == "RequestStatus.COMPLETED"
            ].shape[0]
            total = (
                completed
                + request_stats[
                    request_stats["status"] == "RequestStatus.FAILED"
                ].shape[0]
            )

            success_rate = (completed / total * 100) if total > 0 else 0
            efficiency_ratio = total_energy / (success_rate + 1e-10)

            user_counts.append(user_count)
            efficiency_ratios.append(efficiency_ratio)

        line_style, marker = line_styles[idx % len(line_styles)]
        plt.plot(
            user_counts,
            efficiency_ratios,
            linestyle=line_style,
            marker=marker,
            markersize=8,
            label=strategy_key,
        )

    plt.title("Energy Efficiency vs Number of Users")
    plt.xlabel("Number of Users")
    plt.ylabel("Energy/QoS Ratio (J/%)")
    plt.grid(True)
    plt.legend(title="Strategies", bbox_to_anchor=(1.05, 1), loc="upper left")

    plt.tight_layout()
    plt.show()


def plot_assignment_score(
    energy_dict, request_dict, power_strategy=None, assignment_strategy=None
):
    """
    Create a plot showing Assignment Score (AS*) vs number of users.
    AS* = (0.5 X (1 - E/Emax)) + (0.5 X TS/TSmax)
    Where:
    - E is the energy consumption for the current strategy
    - Emax is the maximum energy consumption among all strategies
    - TS is the success rate for the current strategy
    - TSmax is the maximum success rate among all strategies
    """
    # Ensure strategies are lists
    if isinstance(power_strategy, str):
        power_strategy = [power_strategy]
    if isinstance(assignment_strategy, str):
        assignment_strategy = [assignment_strategy]

    # Filter data by strategies
    def filter_data(data_dict):
        filtered = {}
        for strategy_key, data in data_dict.items():
            power_strat, assign_strat = strategy_key.split(" + ")
            if (not power_strategy or power_strat in power_strategy) and (
                not assignment_strategy or assign_strat in assignment_strategy
            ):
                filtered[strategy_key] = data
        return filtered

    # Filter strategies first
    filtered_energy = filter_data(energy_dict)
    filtered_request = filter_data(request_dict)

    # Create plot
    plt.figure(figsize=(12, 6))

    # Define line styles
    line_styles = [
        ("solid", "o"),
        ("dashed", "s"),
        ("dashdot", "^"),
        ("dotted", "D"),
        ("-", "v"),
        ("--", "p"),
    ]

    # For each user count, we need all strategies' data to normalize
    user_counts = set()
    for strategy_data in filtered_energy.values():
        user_counts.update(run["user_count"] for run in strategy_data)

    # Plot assignment scores
    for idx, strategy_key in enumerate(filtered_energy.keys()):
        if strategy_key not in filtered_request:
            continue

        scores = []
        available_counts = []

        energy_data = filtered_energy[strategy_key]
        request_data = filtered_request[strategy_key]

        # Process each user count
        for user_count in sorted(user_counts):
            # Get all strategies' data for this user count for normalization
            all_energies = []
            all_success_rates = []

            # Only use filtered strategies for normalization
            for s_key in filtered_energy.keys():
                if s_key not in filtered_request:
                    continue

                e_run = next(
                    (
                        run
                        for run in filtered_energy[s_key]
                        if run["user_count"] == user_count
                    ),
                    None,
                )
                r_run = next(
                    (
                        run
                        for run in filtered_request[s_key]
                        if run["user_count"] == user_count
                    ),
                    None,
                )

                if e_run and r_run:
                    total_energy = e_run["data"].sum().sum()
                    request_stats = r_run["data"]
                    completed = request_stats[
                        request_stats["status"] == "RequestStatus.COMPLETED"
                    ].shape[0]
                    total = (
                        completed
                        + request_stats[
                            request_stats["status"] == "RequestStatus.FAILED"
                        ].shape[0]
                    )
                    success_rate = (completed / total * 100) if total > 0 else 0

                    all_energies.append(total_energy)
                    all_success_rates.append(success_rate)

            # Calculate score for current strategy
            e_run = next(
                (run for run in energy_data if run["user_count"] == user_count),
                None,
            )
            r_run = next(
                (run for run in request_data if run["user_count"] == user_count),
                None,
            )

            if e_run and r_run and all_energies and all_success_rates:
                total_energy = e_run["data"].sum().sum()
                request_stats = r_run["data"]
                completed = request_stats[
                    request_stats["status"] == "RequestStatus.COMPLETED"
                ].shape[0]
                total = (
                    completed
                    + request_stats[
                        request_stats["status"] == "RequestStatus.FAILED"
                    ].shape[0]
                )
                success_rate = (completed / total * 100) if total > 0 else 0

                score = calculate_assignment_score(
                    total_energy, success_rate, all_energies, all_success_rates
                )
                scores.append(score)
                available_counts.append(user_count)

        if scores:
            line_style, marker = line_styles[idx % len(line_styles)]
            power_strat, assign_strat = strategy_key.split(" + ")
            display_name = (
                f"{get_display_name(power_strat)} + {get_display_name(assign_strat)}"
            )
            plt.plot(
                available_counts,
                scores,
                linestyle=line_style,
                marker=marker,
                markersize=8,
                label=display_name,
            )

    plt.title("Assignment Score vs Number of Users")
    plt.xlabel("Number of Users")
    plt.ylabel("Assignment Score (AS*)")
    plt.grid(True)
    plt.legend(title="Strategies", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.show()


def get_available_strategies(energy_dict, request_dict):
    """
    Get lists of available power and assignment strategies.

    Returns:
        tuple: (power_strategies, assignment_strategies)
    """
    # Get all strategy combinations
    strategy_keys = set(energy_dict.keys()) & set(request_dict.keys())

    # Split into power and assignment strategies
    power_strategies = set()
    assignment_strategies = set()

    for key in strategy_keys:
        power_strat, assign_strat = key.split(" + ")
        power_strategies.add(power_strat)
        assignment_strategies.add(assign_strat)

    return sorted(power_strategies), sorted(assignment_strategies)


def select_strategies():
    """
    Interactive function to select strategies for evaluation.

    Returns:
        tuple: (selected_power_strategies, selected_assignment_strategies)
    """
    print("\nLoading energy history data...")
    energy_dict = load_data("energy_history")

    print("\nLoading request stats data...")
    request_dict = load_data("request_stats")

    if not energy_dict or not request_dict:
        print(
            "Error: No data loaded. Please check if the data files exist in ../output/"
        )
        return None, None

    power_strategies, assignment_strategies = get_available_strategies(
        energy_dict, request_dict
    )

    print("\nAvailable Power Strategies:")
    for i, strategy in enumerate(power_strategies, 1):
        print(f"{i}. {strategy}")

    print("\nAvailable Assignment Strategies:")
    for i, strategy in enumerate(assignment_strategies, 1):
        print(f"{i}. {strategy}")

    # Select power strategies
    print("\nSelect power strategies (comma-separated numbers, or 'all'):")
    power_input = input("> ").strip().lower()

    if power_input == "all":
        selected_power = power_strategies
    else:
        try:
            indices = [int(x.strip()) - 1 for x in power_input.split(",")]
            selected_power = [power_strategies[i] for i in indices]
        except (ValueError, IndexError):
            print("Invalid input. Using all power strategies.")
            selected_power = power_strategies

    # Select assignment strategies
    print("\nSelect assignment strategies (comma-separated numbers, or 'all'):")
    assign_input = input("> ").strip().lower()

    if assign_input == "all":
        selected_assign = assignment_strategies
    else:
        try:
            indices = [int(x.strip()) - 1 for x in assign_input.split(",")]
            selected_assign = [assignment_strategies[i] for i in indices]
        except (ValueError, IndexError):
            print("Invalid input. Using all assignment strategies.")
            selected_assign = assignment_strategies

    print("\nSelected configurations:")
    print("Power Strategies:", ", ".join(selected_power))
    print("Assignment Strategies:", ", ".join(selected_assign))

    return energy_dict, request_dict, selected_power, selected_assign


def analyze_strategies(
    assignment_strategy=None,
    power_strategy=None,
    user_counts=[10, 20, 30, 40],
    show_plots=True,
    show_tables=True,
):
    """
    Analyze strategies with specified configurations.

    Parameters:
        assignment_strategy (list): List of assignment strategies to analyze.
                                  If None, all available strategies will be used.
        power_strategy (list): List of power strategies to analyze.
                             If None, all available strategies will be used.
        user_counts (list): List of user counts to analyze
        show_plots (bool): Whether to show the plots
        show_tables (bool): Whether to show the tables

    Returns:
        tuple: (energy_dict, request_dict, tables)
            - energy_dict: Dictionary containing energy data
            - request_dict: Dictionary containing request data
            - tables: Dictionary mapping user counts to their result tables
    """
    print("\nLoading energy history data...")
    energy_dict = load_data("energy_history")

    print("\nLoading request stats data...")
    request_dict = load_data("request_stats")

    if not energy_dict or not request_dict:
        print(
            "Error: No data loaded. Please check if the data files exist in ../output/"
        )
        return None, None, None

    # If no strategies specified, use all available ones
    if assignment_strategy is None or power_strategy is None:
        power_strats, assign_strats = get_available_strategies(
            energy_dict, request_dict
        )
        if assignment_strategy is None:
            assignment_strategy = assign_strats
        if power_strategy is None:
            power_strategy = power_strats

    # Plot assignment scores
    if show_plots:
        plot_assignment_score(
            energy_dict,
            request_dict,
            power_strategy=power_strategy,
            assignment_strategy=assignment_strategy,
        )

    # Print tables and collect them
    tables = {}
    if show_tables:
        for user_count in user_counts:
            tables[user_count] = print_combined_table(
                energy_dict,
                request_dict,
                user_count=user_count,
                power_strategy=power_strategy,
                assignment_strategy=assignment_strategy,
            )

    return energy_dict, request_dict, tables


if __name__ == "__main__":
    # Example of interactive usage
    result = select_strategies()

    if result is None:
        exit(1)

    energy_dict, request_dict, power_strategies, assignment_strategies = result

    # Analyze with selected strategies
    analyze_strategies(
        assignment_strategy=assignment_strategies,
        power_strategy=power_strategies,
    )
