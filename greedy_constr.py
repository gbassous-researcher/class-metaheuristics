from base import load_instance_from_txt, Instance
import numpy as np
from copy import deepcopy

class InfeasibleDemand(Exception):
    pass
class FacilityConflict(Exception):
    pass
class OverFacilityDemand(Exception):
    pass

INSTANCE_PATH = "toy.txt"

def check_total_capacity(instance:Instance, facilities:np.ndarray):
    return sum(facilities * instance.capacidades) >= sum(instance.demandas)

def check_total_demand(instance:Instance, clients:np.ndarray):
    return sum(sum(clients)) == sum(instance.demandas)

def check_conflitos(instance:Instance, clients:np.ndarray):
    violated = list()
    for c in instance.pares_conflitantes_0based:
        for j in range(instance.J):
            if clients[c[0],j] > 0 and clients[c[1],j] > 0:
                violated.append(c)
    return violated

def check_per_facility_capacity(instance:Instance, facilities:np.ndarray, clients:np.ndarray):
    over = list()
    for j in instance.J:
        if sum(clients[:,j]>facilities[j]*instance.capacidades[j]):
            over.append((j,clients[:,j] - facilities[j]*instance.capacidades[j]))
    return over

def build_minimum_facilities_greedy(instance: Instance, cap_over_fcost:np.ndarray, facilities:np.ndarray):
    while not check_total_capacity(instance,facilities):
        for i in cap_over_fcost.argsort(descending=True):
            if facilities[i] == 0: 
                facilities[i] = 1
            elif i == len(facilities) - 1:
                raise InfeasibleDemand()
    return facilities

def facility_cost(instance:Instance, facilities:np.ndarray):
    return sum(instance.custos_fixos * facilities)

def shipping_cost(instance:Instance, clients:np.ndarray):
    return sum(sum(clients * instance.custos_transporte))

def build_clients_greedy(instance:Instance, clients:np.ndarray, facilities:np.ndarray, cap_over_fcost:np.ndarray, cap_over_vcost:np.ndarray):
    tally_demanda = deepcopy(instance.demandas)
    tally_capacidade = deepcopy(instance.capacidades) * facilities
    while not check_total_demand(instance,clients):
        for i in [i for i in range(instance.I) if tally_demanda[i]>0]:
            for j in [j for j in range(instance.J) if tally_capacidade[j]>0]:
                if tally_demanda[i] <= tally_capacidade[j]:
                    clients[i,j] += tally_demanda[i]
                    conflicts = check_conflitos(instance,clients)
                    if len(conflicts)>0:
                        clients[i,j] -= tally_demanda[i]
                        break
                    tally_capacidade[j] -= tally_demanda[i]
                    tally_demanda[i] -= tally_demanda[i]
                else:
                    over = tally_demanda[i] - tally_capacidade[j]
                    clients[i,j] += (tally_demanda[i] - over)
                    if len(conflicts)>0:
                        clients[i,j] -= (tally_demanda[i] - over)
                        break
                    tally_demanda[i] = over
                    tally_capacidade[j] = 0
        
    print()

    return facilities, clients

def build_solution_greedy(instance:Instance):
    facilities = np.zeros(instance.J,np.bool)
    clients = np.zeros((instance.I, instance.J), np.int32)
    cap_over_fcost: np.ndarray = instance.capacidades / instance.custos_fixos
    cap_over_vcost: np.ndarray = instance.capacidades / instance.custos_transporte

    facilities = build_minimum_facilities_greedy(instance,cap_over_fcost,facilities)
    facilities, clients = build_clients_greedy(instance,clients,facilities,cap_over_fcost,cap_over_vcost)

if __name__ == "__main__":
    instance = load_instance_from_txt(INSTANCE_PATH)
    build_solution_greedy(instance=instance)