#!/usr/bin/env python

import matplotlib.pyplot as plt
import matplotlib.transforms as transforms
import numpy as np
import tkinter
from random import random


SLIVER_COST = 15000
COSTS = [[25000],
        [750000, 5000000],
        [4000000, 1000000, 20000000],
        [8000000, 20000000, 40000000, 65000000, 100000000, 250000000, 750000000,
            2000000000, 4000000000, 6000000000]]
ITEM_COST = 5000000

DUST_REFUND = 1 / 6
CORE_REFUND = 1 / 33
GOLD_REFUND = 1 / 100
ITEM_REFUND = 1 / 250
UPGRADED_ITEM_REFUND = 1 / 1000


def main():
    sim_tier(4, 4)


def sim_tier(c, t):
    results = [sim(c, t) for i in range(100000)]
    total_costs = [(ITEM_COST * i[0] + SLIVER_COST * 100 * i[2] + i[3]) / 1000000 for i in results]
    item_counts = [i[0] for i in results]
    gold_counts = [i[3] / 1000000 for i in results]
    avg = sum(total_costs) / len(total_costs)
    print(f'min: {min(total_costs)}kk')
    print(f'max: {max(total_costs)}kk')
    print(f'avg: {avg}kk')
    print(f'avg item count: {sum(item_counts) / len(item_counts)}')
    print(f'avg gold count: {sum(gold_counts) / len(gold_counts)}')
    min_cost = int(min(total_costs))
    max_cost = int(max(total_costs))
    bin_size = max(1, (max_cost - min_cost) // 200)
    bins = range(min_cost, max_cost, bin_size)
    fig, ax = plt.subplots()
    plt.hist(total_costs, density=True, bins=bins, color='#D0EEA0')
    plt.xticks(range(0, max_cost + 1, 100))
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

    i = 0
    for q in np.percentile(total_costs, quartiles):
        plt.axvline(q, ymax=heights[i], linewidth=4, color='orange')
        plt.text(q, heights[i] + 0.01, f'{quartiles[i]}%\n{int(q)}kk', size=12, weight='bold', ha='center', transform=trans)
        i += 1
    plt.axvline(avg, ymax=mean_height, linewidth=4, color='red')
    plt.text(avg, mean_height + 0.01, f'mean\n{int(avg)}kk', size=12, weight='bold', ha='center', transform=trans)
    plt.show()


def sim(c, tier):
    count = 0
    dust = 0
    cores = 0
    gold = 0
    items = [0] * (tier + 1)

    while True:
        if items[-1] > 0:  # we have finally made an item of the desired tier
            break

        for i in range(len(items) - 1, -1, -1):
            if i == 0:
                if items[0] < 2:  # keep adding tier 0 items if we don't have any left, and keep track of the total count
                    count += 2 - items[0]
                    items[0] = 2
            if items[i] >= 2:  # we have two items of the same tier, attempt fusion
                dust += 100
                cores += 2
                gold += COSTS[c - 1][i]
                if random() > 0.65:  # failed fusion
                    if random() > 0.5:  # tier loss
                        items[i] -= 1
                        if i > 0:  # if an item is tier 0, it's destroyed, not reduced in tier
                            items[i - 1] += 1
                else:  # successful fusion
                    if random() < DUST_REFUND: dust -= 100
                    elif random() < CORE_REFUND: cores -= 2
                    elif random() < GOLD_REFUND: gold -= COSTS[c - 1][i]
                    elif random() < ITEM_REFUND: items[i] += 1
                    elif random() < UPGRADED_ITEM_REFUND: items[i + 1] += 1
                    items[i] -= 2
                    items[i + 1] += 1
                break

    return (count, dust, cores, gold)


if __name__ == '__main__':
    main()

