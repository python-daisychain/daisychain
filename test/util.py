def compare_trees(ob1, ob2):
    if not (isinstance(ob1, basestring) and isinstance(ob2, basestring)):
        assert type(ob1) == type(ob2), "{!r} != {!r}".format(ob1, ob2)

    if isinstance(ob1, dict):
        keys = set(ob1.keys() + ob2.keys())
        for key in keys:
            assert key in ob1, "Key {!r} not in {!r}".format(key, ob1)
            assert key in ob2, "Key {!r} not in {!r}".format(key, ob2)
            compare_trees(ob1[key], ob2[key])
    else:
        assert ob1 == ob2, "{!r} != {!r}".format(ob1, ob2)
