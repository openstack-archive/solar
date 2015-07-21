

class Chain(object):

    def __init__(self, dg, inprogress, added):
        self.dg = dg
        self.inprogress
        self.added = added
        self.rules = []

    def add_rule(self, rule):
        self.rules.append(rule)

    @property
    def filtered(self):
        for item in self.added:
            for rule in self.rules:
                if not rule(self.dg, self.inprogress, item):
                    break
            else:
                yield item

    def __iter__(self):
        return iter(self.filtered)


def get_default_chain(dg, inprogress, added):
    chain = Chain(dg, inprogress, added)
    chain.add_rule(items_rule)
    chain.add_rule(target_based_rule)
    chain.add_rule(type_based_rule)
    return chain


def type_based_rule(dg, inprogress, item):
    """condition will be specified like:
        type_limit: 2
    """
    _type = item['resource_type']
    type_count = 0
    for n in inprogress:
        if dg.node[n].get('resource_type') == _type:
            type_count += 1
    return item['type_limit'] > type_count


def target_based_rule(dg, inprogress, item, limit=1):
    target = item['target']
    target_count = 0
    for n in inprogress:
        if dg.node[n].get('target') == target:
            target_count += 1
    return limit > target_count


def items_rule(dg, inprogress, item, limit=10):
    return len(inprogress) < limit
