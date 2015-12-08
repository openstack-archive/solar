def make_arr(data):
    t = {}
    for ov in data:
        if t.get(ov['resource']) is None:
            t[ov['resource']] = {}
        t[ov['resource']][ov['other_input']] = ov['value']
    return t
