from base import load_instance_from_txt
from copy import deepcopy
from solution import Solution

INSTANCE_PATH = "toy.txt"

def build_minimum_facilities_greedy(s:Solution):
    while not s.check_total_capacity():
        for i in s.cap_over_fcost.argsort(descending=True):
            if s.facilities[i] == 0: 
                s.facilities[i] = 1
            elif i == len(s.facilities) - 1:
                raise Solution.InfeasibleDemand()

def build_clients_greedy(s:Solution):
    tally_demanda = deepcopy(s.demandas)
    tally_capacidade = deepcopy(s.capacidades) * s.facilities
    while not s.check_total_demand():
        for i in [i for i in range(s.I) if tally_demanda[i]>0]:
            for j in [j for j in range(s.J) if tally_capacidade[j]>0]:
                if tally_demanda[i] <= tally_capacidade[j]:
                    s.clients[i,j] += tally_demanda[i]
                    conflicts = s.check_conflitos()
                    if len(conflicts)>0:
                        s.clients[i,j] -= tally_demanda[i]
                        break
                    tally_capacidade[j] -= tally_demanda[i]
                    tally_demanda[i] -= tally_demanda[i]
                else:
                    over = tally_demanda[i] - tally_capacidade[j]
                    s.clients[i,j] += (tally_demanda[i] - over)
                    conflicts = s.check_conflitos()
                    if len(conflicts)>0:
                        s.clients[i,j] -= (tally_demanda[i] - over)
                        break
                    tally_demanda[i] = over
                    tally_capacidade[j] = 0
        
    print()

    return s.facilities, s.clients

def build_solution_greedy(instance:Solution):
    s = Solution(instance)
    build_minimum_facilities_greedy(s)
    build_clients_greedy(s)
    name = f"solution_greedy_{INSTANCE_PATH.split('.')[0]}"
    s.save(f"{name}.npz")
    s.plot(path=f"{name}.png")

if __name__ == "__main__":
    instance = load_instance_from_txt(INSTANCE_PATH)
    build_solution_greedy(instance=instance)