import numpy as np
from base import Instance
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

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
        self.cap_over_vcost: np.ndarray = self.capacidades / self.custos_transporte

    def check_total_capacity(self) -> bool:
        return sum(self.facilities * self.capacidades) >= sum(self.demandas)

    def check_total_demand(self) -> bool:
        return sum(sum(self.clients)) == sum(self.demandas)
    
    def check_conflitos(self) -> list:
        violated = list()
        for c in self.pares_conflitantes_0based:
            for j in range(self.J):
                if self.clients[c[0],j] > 0 and self.clients[c[1],j] > 0:
                    violated.append(c)
        return violated

    def check_per_facility_capacity(self) -> list:
        over = list()
        for j in range(self.J):
            if sum(self.clients[:,j] > self.facilities[j]*self.capacidades[j]):
                over.append((j, self.clients[:,j] - self.facilities[j]*self.capacidades[j]))
        return over

    def facility_cost(self):
        return sum(self.custos_fixos * self.facilities)

    def shipping_cost(self):
        return sum(sum(self.clients * self.custos_transporte))

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

    