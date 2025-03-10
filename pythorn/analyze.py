import inspect


def analyze_callable(func):
    """
    This function will analyze the provided callable.

    :param func: The callable to analyze.
    :return: A dictionary with information on the callable.
    """
    positional_params = []
    positional_or_keyword = []
    keyword_params = []
    count = 0
    has_varargs = False  # True if *args exists
    has_kwargs = False  # True if **kwargs exists

    if callable(func):
        sig = inspect.signature(func)
        params = sig.parameters

        for param in params.values():
            count += 1
            if param.kind == param.POSITIONAL_ONLY:
                positional_params.append(param.name)
            elif param.kind == param.POSITIONAL_OR_KEYWORD:
                positional_or_keyword.append(param.name)
            elif param.kind == param.KEYWORD_ONLY:
                keyword_params.append(param.name)
            elif param.kind == param.VAR_POSITIONAL:  # *args
                has_varargs = True
            elif param.kind == param.VAR_KEYWORD:  # **kwargs
                has_kwargs = True

    return {
        "positional": positional_params,
        "keyword": keyword_params,
        "positional_or_keyword": positional_or_keyword,
        "has_args": has_varargs,
        "has_kwargs": has_kwargs,
        "arg_count": len(positional_params)+len(positional_or_keyword),
        "count": count
    }