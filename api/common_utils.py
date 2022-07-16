def is_not_empty (var):
    if (isinstance(var, bool)):
        return var
    elif (isinstance(var, int)):
        return True
    empty_chars = ["", "null", "nil", "false", "none"]
    return var is not None and not any(c == "{}".format(var).lower() for c in empty_chars)

def is_true (var) :
    false_char = ["false", "ko", "no"]
    return is_empty(var) or not any(c == "{}".format(var).lower() for c in false_char)

def is_empty (var):
    return not is_not_empty(var)
