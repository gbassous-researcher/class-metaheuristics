import numpy as np
from base import Instance
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from typing import List, Tuple

class Solution(Instance):
    class InfeasibleDemand(Exception):
        pass
    class FacilityConflict(Exception):
        pass
    class OverFacilityDemand(Exception):
        pass

    def __init__(self, instance:Instance):
        self.__dict__.update(instance.__dict__)
        self.facilities = np.zeros(self.J,np.bool)
        self.clients = np.zeros((self.I, self.J), np.int32)
        self.cap_over_fcost: np.ndarray = self.capacidades / self.custos_fixos
        self.vcost: np.ndarray = self.custos_transporte
        self.sorted_fcost_index: np.ndarray = self.cap_over_fcost.argsort(descending=True)
        self.next_cheapest_facility_index:int = 0
        self.sorted_vcost_index: np.ndarray = self.vcost.argsort(axis=1,descending=False)

    def check_total_capacity(self) -> bool:
        return (self.facilities * self.capacidades).sum() >= self.demandas.sum()

    def check_total_demand(self) -> bool:
        return self.clients.sum() == self.demandas.sum()
    
    def check_conflitos(self, facilities_index:List[int]) -> List[Tuple[int,int],]:
        violated = list()
        for j in facilities_index:
            return [self.clients[c[0],j] > 0 and self.clients[c[1],j] > 0 for c in self.pares_conflitantes_0based]

    def check_per_facility_capacity(self) -> List[Tuple[int,np.ndarray]]:
        over = list()
        for j in range(self.J):
            if (self.clients[:,j] > self.facilities[j]*self.capacidades[j]).sum():
                over.append((j, self.clients[:,j] - self.facilities[j]*self.capacidades[j]))
        return over

    def open_facility(self, facility_index:int):
        assert self.facilities[facility_index] == 0
        self.facilities[facility_index] = np.True_

    def get_next_cheapest_facility(self)-> int:
        return (self.sorted_fcost_index == self.next_cheapest_facility_index).argmax()
    
    def open_next_cheapest_facility(self):
        assert self.facilities.sum() < self.next_cheapest_facility_index + 1
        to_open = self.get_next_cheapest_facility()
        self.open_facility(to_open)
        self.next_cheapest_facility_index += 1
        return to_open

    def get_x_next_cheapest_vcost(self, i, j_list, x = 1):
        sub = self.sorted_vcost_index[i,:]
        return sub[np.isin(sub,j_list[:x])]

    def assign_demand(self, facility_j, client_i, demand) -> int:
        remaining_cap = self.capacidades[facility_j] - self.clients[:,facility_j].sum()
        if remaining_cap >= demand:
            self.clients[client_i,facility_j] += demand
            return 0
        else:
            over = demand - remaining_cap
            self.clients[client_i,facility_j] += remaining_cap
            return over

    def unassign_demand(self, facility_j, client_i, demand):
        self.clients[client_i,facility_j] -= demand
        

    def facility_cost(self):
        return (self.custos_fixos * self.facilities).sum()

    def shipping_cost(self):
        return (self.clients * self.custos_transporte).sum()

    def total_cost(self):
        return self.shipping_cost() + self.facility_cost()

    def save(self, path: str):
        """Save the decision variables (facilities, clients) to a .npz file.
        The instance data is not stored; pass it to load() to rebuild."""
        np.savez(path, facilities=self.facilities, clients=self.clients,
                 facility_cost=self.facility_cost(), shipping_cost=self.shipping_cost())

    @classmethod
    def load(cls, path: str, instance: Instance) -> "Solution":
        """Rebuild a Solution for `instance` from a file written by save()."""
        s = cls(instance)
        with np.load(path) as data:
            facilities = data["facilities"]
            clients = data["clients"]
        if facilities.shape != (s.J,) or clients.shape != (s.I, s.J):
            raise ValueError(
                f"Saved solution (facilities {facilities.shape}, clients {clients.shape}) "
                f"does not match instance (J={s.J}, I={s.I})."
            )
        s.facilities = facilities.astype(bool)
        s.clients = clients.astype(np.int32)
        return s

    def plot(self, path: str | None = None, show: bool = True):
            """One figure of the current state: one bar per facility, stacked by
            the demand each client sends to it. Closed facilities are hatched grey;
            the dashed outline of each bar is the facility's capacity."""
    
            cmap = plt.get_cmap("tab20")
            fig, ax = plt.subplots(figsize=(max(6, 0.9 * self.J + 2), 5))
    
            for j in range(self.J):
                is_open = bool(self.facilities[j])
                ax.add_patch(Rectangle(
                    (j - 0.4, 0), 0.8, self.capacidades[j], fill=not is_open,
                    facecolor="#e6e6e6", edgecolor="#555555" if is_open else "#999999",
                    hatch=None if is_open else "//", linestyle="--", linewidth=1, zorder=1,
                ))
                bottom = 0
                for i in range(self.I):
                    qty = self.clients[i, j]
                    if qty > 0:
                        ax.bar(j, qty, bottom=bottom, width=0.8, color=cmap(i % 20),
                               edgecolor="white", linewidth=0.8, zorder=2)
                        ax.text(j, bottom + qty / 2, f"C{i}: {qty}", ha="center",
                                va="center", fontsize=8, zorder=3)
                        bottom += qty
    
            for i in range(self.I):  # legend: one entry per client
                ax.bar(0, 0, color=cmap(i % 20), label=f"Client {i} (demand {self.demandas[i]})")
    
            ax.set_xticks(range(self.J))
            ax.set_xticklabels([f"F{j}\n{'open' if self.facilities[j] else 'closed'}"
                                for j in range(self.J)])
            ax.set_xlim(-0.6, self.J - 0.4)
            ax.set_ylim(0, max(self.capacidades) * 1.08)
            ax.set_ylabel("Demand assigned (dashed outline = capacity)")
            ax.set_title(f"Solution state: {int(sum(self.facilities))}/{self.J} facilities open")
            ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=8, frameon=False)
            fig.tight_layout()
    
            if path:
                fig.savefig(path, dpi=150, bbox_inches="tight")
            if show:
                plt.show()
            return fig

    