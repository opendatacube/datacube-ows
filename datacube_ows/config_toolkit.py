def deepinherit(parent, child):
    for k in parent:
        if k in child:
            if isinstance(child[k], dict):
                # recurse dictionary
                deepinherit(parent[k], child[k])
            elif isinstance(child[k], str):
                # Keep child's version of str
                pass
            else:
                try:
                    iter(child[k])
                    # non-str iterable - append child to parent
                    child[k] = parent[k] + child[k]
                except TypeError:
                    # Non-iterable - keep child's version
                    pass
        else:
            child[k] = parent[k]

