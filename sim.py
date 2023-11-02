#!/usr/bin/env python

import matplotlib.pyplot as plt
import matplotlib.transforms as transforms
import numpy as np
from random import random
import statistics

# The class and tier to be simulated
CLASS = 4
TIER = 5

# Average price you expect to spend per item
ITEM_COST = 3000000

# If set to non-zero value, will include transferring down to another item in the costs
# i.e. if TIER = 4, this will calculate making a T5 base and transferring onto a T4
TRANSFER_ITEM_COST = 100000000
CONVERGENCE_TRANSFER = True

# Average price you expect to spend per sliver
SLIVER_COST = 15000
CORE_COST = SLIVER_COST * 50

GOLD_FEES = [[25000],
        [750000, 5000000],
        [4000000, 10000000, 20000000],
        [8000000, 20000000, 40000000, 65000000, 100000000, 250000000, 750000000,
            2500000000, 8000000000, 15000000000]]
CONVERGENCE_GOLD_FEES = [0, 0, 0, 0, 2000000000] # TODO get the other values

TRANSFER_CORES = [1, 2, 5, 10, 15, 25, 35, 50, 100]  # the last 4 are guesses

# Estimated values for the bonus refund effects
DUST_REFUND = 1 / 6
CORE_REFUND = 1 / 20
GOLD_REFUND = 1 / 100
DOWNGRADED_ITEM_REFUND = 1 / 250
ITEM_REFUND = 1 / 500
UPGRADED_ITEM_REFUND = 1 / 1000

SIMULATION_ROUNDS = 100000


def main():
    results = [sim_one_round(CLASS, TIER, CONVERGENCE_TRANSFER) for i in range(SIMULATION_ROUNDS)]
    total_costs = [(ITEM_COST * i[0] + TRANSFER_ITEM_COST + CORE_COST * i[2] + i[3]) / 1000000 for i in results]
    item_counts = [i[0] for i in results]
    gold_counts = [i[3] / 1000000 for i in results]
    dusts = [i[1] for i in results]
    avg_dust = sum(dusts) / len(dusts)
    avg_cost = sum(total_costs) / len(total_costs)
    min_cost = int(min(total_costs))
    max_cost = int(max(total_costs))
    std_dev = statistics.stdev(total_costs)

    print(f'mean dust: {avg_dust}')
    print(f'standard deviation: {std_dev}kk')
    print(f'mean item count: {sum(item_counts) / len(item_counts)}')
    print(f'mean gold fees: {sum(gold_counts) / len(gold_counts)}kk')
    print(f'mean total cost: {(avg_cost)}kk')

    plot(total_costs, avg_cost, min_cost, max_cost)


def plot(total_costs, avg_cost, min_cost, max_cost):
    graph_end = int(np.percentile(total_costs, 100 - 1000 / SIMULATION_ROUNDS))
    bin_size = max(1, (graph_end - min_cost) // 150)
    bins = range(min_cost, graph_end, bin_size)
    fig, ax = plt.subplots()
    plt.hist(total_costs, density=True, bins=bins, color='#A0E0F0')
    plt.yticks([])

    quartiles = [1, 10, 25]
    quartiles.append(50)
    upper_quartiles = [100 - x for x in quartiles[:-1]]
    upper_quartiles.reverse()
    quartiles += upper_quartiles
    
    min_height = 0.08
    heights = [min_height] * len(quartiles)
    for i in range(len(quartiles) // 2):
        heights[i] *= i + 1
        heights[len(quartiles) - 1 - i] *= i + 1
    heights[len(quartiles) // 2] *= len(quartiles) // 2 + 1
    mean_height = max(heights) + min_height

    trans = transforms.blended_transform_factory(ax.transData, ax.transAxes)

    print('percentiles:')
    i = 0
    for q in np.percentile(total_costs, quartiles):
        print(f'{quartiles[i]}%: {int(q)}kk')
        plt.axvline(q, ymax=heights[i], linewidth=2, color='orange')
        plt.text(q, heights[i] + 0.01, f'{quartiles[i]}%\n{int(q)}kk', size=12, weight='bold', ha='center', transform=trans)
        i += 1

    plt.axvline(avg_cost, ymax=mean_height, linewidth=2, color='red')
    plt.text(avg_cost, mean_height + 0.01, f'mean\n{int(avg_cost)}kk', size=12, weight='bold', ha='center', transform=trans)
    plt.title(f'Class {CLASS}, Tier {TIER}', fontsize=30)

    fig.set_size_inches(18.5, 10.5)
    fig.savefig('fig.png', dpi=100, bbox_inches = 'tight')

    plt.show()


def sim_one_round(classif, tier, convergence):
    if TRANSFER_ITEM_COST > 0: tier += 1
    if convergence: tier -= 1
    item_count = 0
    dust = 0
    cores = 0
    gold = 0
    items = [0] * (tier + 1)

    while True:
        if items[-1] > 0:  # we have finally made an item of the desired tier
            break

        # Loop backwards so that we only buy new T0s when we absolutely have to
        for i in range(len(items) - 1, -1, -1):
            if i == 0:  # Add more tier 0 items if we don't have any left
                if items[0] < 2:
                    item_count += 2 - items[0]
                    items[0] = 2
            if items[i] >= 2:  # We have two items of the same tier, attempt fusion
                dust += 100
                gold += GOLD_FEES[classif - 1][i]

                # Decide whether to use cores
                cores_used = 0
                if classif < 4 and (GOLD_FEES[classif - 1][i] + ITEM_COST) * 0.15 < CORE_COST:
                    p_success = 0.5
                else:
                    p_success = 0.65
                    cores_used += 1
                if classif < 4 and i == 0 and ITEM_COST * (1 - p_success) * 0.5 < CORE_COST:
                    p_tier_loss = 1
                else:
                    p_tier_loss = 0.5
                    cores_used += 1

                cores += cores_used

                if random() > p_success:  # failed fusion
                    if random() < p_tier_loss:  # tier loss
                        items[i] -= 1
                        if i > 0:  # If an item is tier 0, it's destroyed, not reduced in tier
                            items[i - 1] += 1
                else:  # successful fusion, check for bonus refunds
                    if random() < DUST_REFUND: dust -= 100
                    elif random() < CORE_REFUND: cores -= cores_used
                    elif random() < GOLD_REFUND: gold -= GOLD_FEES[classif - 1][i]
                    elif random() < DOWNGRADED_ITEM_REFUND and i > 0: items[i - 1] += 1
                    elif random() < ITEM_REFUND: items[i] += 1
                    elif random() < UPGRADED_ITEM_REFUND: items[i + 1] += 1
                    items[i] -= 2
                    items[i + 1] += 1
                break

    if TRANSFER_ITEM_COST > 0:
        if convergence:
            dust += 160
            cores += TRANSFER_CORES[tier - 1]
            gold += CONVERGENCE_GOLD_FEES[tier - 1]
        else:
            dust += 100
            cores += TRANSFER_CORES[tier - 2]
            gold += GOLD_FEES[classif - 1][tier - 1]

    return (item_count, dust, cores, gold)


if __name__ == '__main__':
    main()

