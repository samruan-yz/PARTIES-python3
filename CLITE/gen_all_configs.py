#!/usr/bin/python

# Number of applications co-located
NUM_APPS      = 3

# Number of resources being partitioned e.g., cores, LLC ways, and memory b/w
NUM_RESOURCES = 3

# Number of units of each resource (in order) e.g., [number of cores, number of LLC ways, level of memory b/w]
NUM_UNITS     = [10, 11, 10]

# Example of a configuration in the above scenario: [c11, c12, c21, c22, c31, c33] = [1, 2, 4, 4, 5, 3]
# c11 = 1 = App 1's allocation of resource 1
# c12 = 2 = App 2's allocation of resource 1
# c13 = 10 - 1 - 2 = 7 = App 3's allocation of resource 1 (inferred but not explicitly shown)
# c21 = 4 = App 1's allocation of resource 2
# c22 = 4 = App 2's allocation of resource 2
# c33 = 11 - 4 - 4 = 3 = App 3's allocation of resource 2 (inferred but not explicitly shown)
# c31 = 5 = App 1's allocation of resource 3
# c32 = 5 = App 2's allocation of resource 3
# c33 = 10 - 5 - 3 = 2 = App 3's allocation of resource 3 (inferred but not explicitly shown)

CONFIGS_LIST  = None

def gen_configs_recursively(u, r, a):

    # Generate allocations configurations starting with application 'a' given 'u' units of resource 'r'
    if (a == NUM_APPS-1):
        return None
    else:
        ret = []
        for i in range(1, NUM_UNITS[r]-u+1-NUM_APPS+a+1):
            confs = gen_configs_recursively(u+i, r, a+1)
            if not confs:
                ret.append([i])
            else:
                for c in confs:
                    ret.append([i])
                    for j in c:
                        ret[-1].append(j)
        return ret

def gen_configs():

    global CONFIGS_LIST

    # Generate all possible configurations of resource allocations recursively
    for r in range(NUM_RESOURCES):
        if not CONFIGS_LIST:
            CONFIGS_LIST = gen_configs_recursively(0, r, 0)
        else:
            CONFIGS_LIST = [x + y for x in CONFIGS_LIST for y in gen_configs_recursively(0, r, 0)]

def main():

    # Generate all possible configurations of resource allocations for the japps
    gen_configs()

    print('Number of Dimensions: %d' % (len(CONFIGS_LIST[0]) + NUM_RESOURCES))
    print('Size of Configuration Space: %d' % (len(CONFIGS_LIST)))

if __name__ == '__main__':

    # Invoke the main function
    main()
