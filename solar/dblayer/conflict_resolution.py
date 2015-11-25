from collections import Counter


def naive_resolver(riak_object):
    # for now we support deleted vs existing object
    siblings = riak_object.siblings
    siblings_len = map(
        lambda sibling: (len(sibling._get_encoded_data()), sibling), siblings)
    siblings_len.sort()
    c = Counter((x[0] for x in siblings_len))
    if len(c) > 2:
        raise RuntimeError(
            "Too many different siblings, not sure what to do with siblings")
    if not 0 in c:
        raise RuntimeError(
            "No empty object for resolution, not sure what to do with siblings")
    selected = max(siblings_len)
    # TODO: pass info to obj save_lazy too
    riak_object.siblings = [selected[1]]


dblayer_conflict_resolver = naive_resolver
