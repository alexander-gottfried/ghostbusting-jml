import boolexpr
import itertools

def from_program(initial_state, methods: dict[str, (boolexpr.BoolExpr, boolexpr.BoolExpr)]):
    stack = [name for name, (pre, _) in methods.items()
             if boolexpr.satisfies(initial_state, pre)]

    graph = {}
    graph['init'] = set(stack)

    while len(stack) > 0:
        name = stack.pop()
        _, post = methods[name]
        graph[name] = set(other_name for other_name, (other_pre, _) in methods.items()
                          if boolexpr.expr_satisfies(post, other_pre))
        stack.extend(other_name for other_name in graph[name]
                     if other_name not in graph)

    return graph


def from_program(possible_states,
                 methods: dict[str, (boolexpr.BoolExpr, boolexpr.BoolExpr)],
                 satisfies=boolexpr.satisfies):
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

