import itertools
from typing import Callable

from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from ortools.sat.python import cp_model

Arc = tuple[int, int]
Solver = Callable[[dict[Arc, int], int], list[int]]


def solve_tsp_routing(cost: dict[Arc, int], num_columns: int) -> list[int]:
    n = num_columns

    manager = pywrapcp.RoutingIndexManager(n + 1, 1, n)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(i: int, j: int) -> int:
        u = manager.IndexToNode(i)
        v = manager.IndexToNode(j)

        if v == n or u == n:
            return 0
        else:
            return cost[u, v]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        return []

    index = routing.Start(0)
    result = [manager.IndexToNode(index)]
    while not routing.IsEnd(index):
        index = solution.Value(routing.NextVar(index))
        result.append(manager.IndexToNode(index))

    assert len(result) == num_columns + 2
    return result[1:-1]


def solve_tsp_cp_sat(cost: dict[Arc, int], num_columns: int) -> list[int]:
    depot = num_columns
    n = num_columns + 1
    if n < 2:
        raise ValueError("Need at least two nodes")

    # Add depot to cost matrix
    full_cost = {
        (i, j): cost.get((i, j), 1_000_000)
        for i, j in itertools.permutations(range(num_columns), 2)
    }
    for i in range(n):
        full_cost[i, depot] = 0
        full_cost[depot, i] = 0

    model = cp_model.CpModel()

    # Binary arc variables
    x: dict[Arc, cp_model.IntVar] = {}
    for i, j in itertools.permutations(range(n), 2):
        x[(i, j)] = model.NewBoolVar(f"x_{i}_{j}")

    # Degree constraints
    for i in range(n):
        model.Add(sum(x[(i, j)] for j in range(n) if i != j) == 1)
        model.Add(sum(x[(j, i)] for j in range(n) if i != j) == 1)

    # MTZ subtour elimination
    u = [model.NewIntVar(0, n - 1, f"u_{i}") for i in range(n)]
    model.Add(u[depot] == 0)
    for i, j in itertools.permutations(range(n), 2):
        if i == depot or j == depot:
            continue

        model.Add(u[i] - u[j] + n * x[(i, j)] <= n - 1)

    # Objective: minimise total cost
    model.Minimize(sum(full_cost[(i, j)] * x[(i, j)] for (i, j) in x))

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("No solution found")

    # Extract tour by following arcs from depot
    tour_arcs = {i: j for (i, j), var in x.items() if solver.Value(var)}
    ordered_nodes: list[int] = []
    cur = depot
    for _ in range(num_columns):
        cur = tour_arcs[cur]
        ordered_nodes.append(cur)

    return ordered_nodes
