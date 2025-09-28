from ortools.constraint_solver import pywrapcp, routing_enums_pb2


def solve_tsp_routing(cost: dict[tuple[int, int], int], num_columns: int) -> list[int]:
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
