import os
from os import path


def list_dir(dir):
    children = sorted([c for c in os.listdir(dir) if not c.startswith('.')])
    order_file = path.join(dir, '.order')
    if os.isfile(order_file):
        with open(order_file, 'r') as f:
            ordered = []
            for line in f.readlines():
                if line in children:
                    ordered.append(line)
                    children.remove(line)
                else:
                    print "WARN: %s contains item that is missing from the " +\
                        "file system: %s" % (order_file, line)
        for remaining in children:
            print "WARN: %s is missing an entry for: %s" % (order_file,
                                                            remaining)
            ordered.append(remaining)
        children = ordered
    return children
