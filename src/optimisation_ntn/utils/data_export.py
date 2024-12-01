import os
import csv


def export_to_csv(filename, data, headers):
    """Export data to a CSV file."""
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if headers:
                writer.writerow(headers)
            writer.writerows(data)
        print(f"Data successfully exported to {os.path.abspath(filename)}")
    except Exception as e:
        print(f"Error while writing to {os.path.abspath(filename)}: {e}")


def collect_graph_data(all_iterations_data):
    """Aggregate data from all iterations for different plots."""
    success_rate_vs_total_requests = []
    energy_consumed_data = []
    completed_requests_data = []

    for iteration_data in all_iterations_data:
        total_requests = iteration_data["total_requests"]
        success_rate = iteration_data["success_rate"]
        total_energy_bs = iteration_data["total_energy_bs"]
        total_energy_haps = iteration_data["total_energy_haps"]
        total_energy_leo = iteration_data["total_energy_leo"]

        success_rate_vs_total_requests.append([total_requests, success_rate])
        energy_consumed_data.append([total_requests, total_energy_bs, "BS"])
        energy_consumed_data.append([total_requests, total_energy_haps, "HAPS"])
        energy_consumed_data.append([total_requests, total_energy_leo, "LEO"])
        completed_requests_data.append(
            [total_requests, total_energy_bs + total_energy_haps + total_energy_leo]
        )

    base_directory = os.path.join(os.getcwd(), "Statistic_csv")
    if not os.path.exists(base_directory):
        os.makedirs(base_directory)

    export_to_csv(
        os.path.join(base_directory, "success_rate_vs_request.csv"),
        success_rate_vs_total_requests,
        ["Number of Requests", "Success Rate"],
    )
    export_to_csv(
        os.path.join(base_directory, "energy_consumed_vs_request.csv"),
        energy_consumed_data,
        ["Number of Requests", "Energy Consumed (by type)", "Node Type"],
    )
    export_to_csv(
        os.path.join(base_directory, "energy_vs_completed.csv"),
        completed_requests_data,
        ["Completed Requests", "Total Energy Consumed"],
    )
    print(f"CSV files generated in: {base_directory}")
