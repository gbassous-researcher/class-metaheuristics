from base import load_instance_from_txt
from copy import deepcopy
from solution import Solution
import numpy as np

INSTANCE_PATH = "toy.txt"

def build_minimum_facilities_greedy(s:Solution):
    while not s.check_total_capacity():
        s.open_next_cheapest_facility()

def build_clients_greedy(s:Solution):
    tally_demanda:np.ndarray = deepcopy(s.demandas)
    tally_capacidade:np.ndarray = deepcopy(s.capacidades) * s.facilities
    for i in {x for pair in s.pares_conflitantes_0based for x in pair}:
        sorted_j = s.get_x_next_cheapest_vcost(i,np.flatnonzero(tally_capacidade),s.J)
        for j in sorted_j:
            over = s.assign_demand(j,i,tally_demanda[i])
            if any(s.check_conflitos([j])):
                s.unassign_demand(j,i,tally_demanda[i])
            else:
                tally_capacidade[j] -= (tally_demanda[i] - over)
                tally_demanda[i] -= (tally_demanda[i] - over)
                if tally_demanda[i] == 0: break

    while not s.check_total_demand():
        if tally_capacidade.sum() == 0:
            opened = s.open_next_cheapest_facility()
            tally_capacidade[opened] += s.capacidades[opened]

        for i in np.flatnonzero(tally_demanda):
            nonzeros = np.flatnonzero(tally_capacidade)
            sorted_j = s.get_x_next_cheapest_vcost(i,nonzeros,len(nonzeros))
            for j in sorted_j:
                over = s.assign_demand(j,i,tally_demanda[i])
                if any(s.check_conflitos([j])):
                    s.unassign_demand(j,i,tally_demanda[i])
                else:
                    tally_capacidade[j] -= (tally_demanda[i] - over)
                    tally_demanda[i] -= (tally_demanda[i] - over)
                    if tally_demanda[i] == 0: break
    print()

    return s.facilities, s.clients

def build_solution_greedy(instance:Solution):
    s = Solution(instance)
    build_minimum_facilities_greedy(s)
    build_clients_greedy(s)
    name = f"solution_greedy_{INSTANCE_PATH.split('.')[0]}"
    s.save(f"{name}.npz")
    s.plot(path=f"{name}.png")
    print(s.total_cost())

if __name__ == "__main__":
    instance = load_instance_from_txt(INSTANCE_PATH)
    build_solution_greedy(instance=instance)