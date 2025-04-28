import itertools
import boolexpr


def from_program(possible_states,
                 methods: dict[str, (boolexpr.BoolExpr, boolexpr.BoolExpr)],
                 satisfies=boolexpr.satisfies):
    """
    Return a graph with transitions prestate--method-->poststate from all
    possible prestates of a method to all its possible poststates. Possible
    transitions are determined with the function `satisfies`.

    The graph is of type dict[state->dict[method->state]].
    """
    graph = {}
    print(possible_states)

    def satisying_states(x):
        return [state for state in possible_states
                if satisfies(state, x)]

    def valid_transitions(precond, postcond):
        pres = satisying_states(precond)
        return [(pre, post)
                for pre in pres
                for post in possible_states
                if satisfies(post, postcond, prestate=pre)]

    for name, (precond, postcond) in methods.items():
        if not postcond.contains_old():
            pres_posts = itertools.product(
                    satisying_states(precond),
                    satisying_states(postcond))
        else:
            pres_posts = valid_transitions(precond, postcond)

        for pre, post in pres_posts:
            if pre not in graph:
                graph[pre] = {}
            if name not in graph[pre]:
                graph[pre][name] = []
            graph[pre][name].append(post)

    return graph
