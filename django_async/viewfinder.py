import types


def get_all_functions(current_globals):
    all_functions = []
    for name, value in current_globals.items():
        if isinstance(value, types.FunctionType) and name != "get_all_functions":
            all_functions.append((name, value))
    return all_functions
