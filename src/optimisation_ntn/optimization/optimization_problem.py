""" Optimization problem class """

from pymoo.core.problem import ElementwiseProblem


class OptimizationProblem(ElementwiseProblem):
    """Problem definition for pymoo optimization"""

    def __init__(self, simulation, n_requests: int, n_nodes: int):
        """Initialize the optimization problem.

        Args:
            simulation: Simulation instance
            n_requests: Number of requests to optimize
            n_nodes: Number of compute nodes available
        """
        super().__init__(
            n_var=n_requests,  # Number of variables (assignments)
            n_obj=1,  # Single objective (energy)
            n_ieq_constr=1,  # One constraint (QoS satisfaction)
            xl=0,  # Lower bound for node IDs
            xu=n_nodes - 1,  # Upper bound for node IDs
            vtype=int,  # Integer variables
        )
        self.simulation = simulation
        self.n_requests = n_requests
        self.n_nodes = n_nodes

    def _evaluate(self, x, out, *args, **kwargs):
        """Evaluate a solution vector.

        Args:
            x: Solution vector (assignment vector)
            out: Output dictionary for objectives and constraints

        Returns:
            None (updates out dictionary)
        """
        # Run simulation with this assignment vector
        self.simulation.reset()
        energy, satisfaction = self.simulation.run_with_assignment(x)

        # Set objective (energy consumption)
        out["F"] = [energy * ((5 - satisfaction) / 5)]  # bonus of 20% for satisfaction

        # Set constraint (QoS satisfaction must be >= 90%)
        out["G"] = [0.90 - satisfaction]
