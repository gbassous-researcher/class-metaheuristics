import random
import re
import numpy as np

CAMINHO_INSTANCIA = "toy.txt"

# ===============
# CLASSE INSTANCE
# ===============
class Instance:
    def __init__(
        self,
        n_facilidades,
        n_clientes,
        capacidades,
        custos_fixos,
        demandas,
        custos_transporte,
        n_conflitos,
        pares_conflitantes,
    ):
        if not isinstance(n_facilidades, int) or n_facilidades <= 0:
            raise ValueError(f"Número de facilidades inválido: {n_facilidades}. Deve ser > 0.")
        if not isinstance(n_clientes, int) or n_clientes <= 0:
            raise ValueError(f"Número de clientes inválido: {n_clientes}. Deve ser > 0.")

        cap_arr = np.asarray(capacidades, dtype=int)
        cfixo_arr = np.asarray(custos_fixos, dtype=int)
        dem_arr = np.asarray(demandas, dtype=int)

        if cap_arr.ndim != 1 or len(cap_arr) != n_facilidades:
            raise ValueError(
                f"Capacidades deve ter tamanho {n_facilidades}, mas recebeu {len(cap_arr)}."
            )
        if cfixo_arr.ndim != 1 or len(cfixo_arr) != n_facilidades:
            raise ValueError(
                f"CustosFixos deve ter tamanho {n_facilidades}, mas recebeu {len(cfixo_arr)}."
            )
        if dem_arr.ndim != 1 or len(dem_arr) != n_clientes:
            raise ValueError(
                f"Demandas deve ter tamanho {n_clientes}, mas recebeu {len(dem_arr)}."
            )

        if not isinstance(custos_transporte, (list, np.ndarray)) or len(custos_transporte) != n_clientes:
            raise ValueError(
                f"CustosTransporte deve ter {n_clientes} linhas, mas recebeu {len(custos_transporte)}."
            )
        for idx, linha in enumerate(custos_transporte):
            if len(linha) != n_facilidades:
                raise ValueError(
                    f"Linha {idx + 1} de CustosTransporte deve ter {n_facilidades} colunas, mas recebeu {len(linha)}."
                )

        ctransp_arr = np.array(custos_transporte, dtype=int)

        if np.any(cap_arr < 0):
            raise ValueError("Capacidades não podem ser negativas.")
        if np.any(cfixo_arr < 0):
            raise ValueError("CustosFixos não podem ser negativos.")
        if np.any(dem_arr < 0):
            raise ValueError("Demandas não podem ser negativas.")
        if np.any(ctransp_arr < 0):
            raise ValueError("CustosTransporte não podem conter valores negativos.")
        if np.sum(cap_arr) < np.sum(dem_arr):
            raise ValueError(
                f"Capacidade total ({np.sum(cap_arr)}) é menor que a demanda total ({np.sum(dem_arr)})."
            )

        if not isinstance(n_conflitos, int) or n_conflitos < 0:
            raise ValueError(f"Conflitos deve ser um inteiro não negativo, recebeu {n_conflitos}.")

        pares_list = list(pares_conflitantes) if pares_conflitantes is not None else []
        if len(pares_list) != n_conflitos:
            raise ValueError(
                f"Inconsistência: Conflitos = {n_conflitos}, mas ParesConflitantes possui {len(pares_list)} par(es)."
            )

        self.J = n_facilidades
        self.I = n_clientes
        self.capacidades = cap_arr
        self.custos_fixos = cfixo_arr
        self.demandas = dem_arr
        self.custos_transporte = ctransp_arr
        self.n_conflitos = n_conflitos
        self.conflitos = {i: set() for i in range(self.I)}
        self.pares_conflitantes_brutos = []
        self.pares_conflitantes_0based = []

        for idx, par in enumerate(pares_list):
            if len(par) != 2:
                raise ValueError(
                    f"Par conflitante na posição {idx + 1} deve ter exatamente 2 clientes, recebeu: {par}."
                )
            i1, i2 = int(par[0]), int(par[1])
            if not (1 <= i1 <= self.I) or not (1 <= i2 <= self.I):
                raise ValueError(
                    f"Par conflitante ({i1}, {i2}) fora do intervalo de clientes [1, {self.I}]."
                )
            if i1 == i2:
                raise ValueError(f"Auto-conflito inválido no par ({i1}, {i2}).")

            self.pares_conflitantes_brutos.append([i1, i2])
            u, v = i1 - 1, i2 - 1
            self.pares_conflitantes_0based.append((u, v))
            self.conflitos[u].add(v)
            self.conflitos[v].add(u)


# ===============================
# LEITURA DO ARQUIVO DE INSTÂNCIA
# ===============================
def load_instance_from_txt(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        raw_text = f.read()

    def extract_int(name):
        match = re.search(rf"\b{name}\s*=\s*(-?\d+)\s*;", raw_text)
        if not match:
            raise ValueError(f"Campo inteiro '{name}' não encontrado ou mal formatado em '{filepath}'.")
        return int(match.group(1))

    def extract_1d_array(name):
        match = re.search(rf"\b{name}\s*=\s*\[(.*?)\]\s*;", raw_text, re.DOTALL)
        if not match:
            raise ValueError(f"Vetor '{name}' não encontrado ou mal formatado em '{filepath}'.")
        content = match.group(1).strip()
        if not content:
            return []
        try:
            return [int(x.strip()) for x in content.split(",")]
        except ValueError as exc:
            raise ValueError(f"Valor não inteiro encontrado em '{name}'.") from exc

    def extract_2d_array(name, allow_empty=False):
        match = re.search(rf"\b{name}\s*=\s*\[\|(.*?)\|\]\s*;", raw_text, re.DOTALL)
        if not match:
            if allow_empty and re.search(rf"\b{name}\s*=\s*\[\s*\]\s*;", raw_text):
                return []
            raise ValueError(f"Matriz '{name}' não encontrada ou mal formatada em '{filepath}'.")
        body = match.group(1).strip()
        if not body:
            return []
        rows = [r.strip() for r in body.split("|") if r.strip()]
        matrix = []
        for r in rows:
            try:
                nums = [int(x.strip()) for x in r.split(",") if x.strip()]
            except ValueError as exc:
                raise ValueError(f"Valor não inteiro encontrado na linha '{r}' de '{name}'.") from exc
            if nums:
                matrix.append(nums)
        return matrix

    n_facilidades = extract_int("Facilidades")
    n_clientes = extract_int("Clientes")
    capacidades = extract_1d_array("Capacidades")
    custos_fixos = extract_1d_array("CustosFixos")
    demandas = extract_1d_array("Demandas")
    custos_transporte = extract_2d_array("CustosTransporte")
    n_conflitos = extract_int("Conflitos")
    pares_conflitantes = extract_2d_array("ParesConflitantes", allow_empty=True)

    return Instance(
        n_facilidades=n_facilidades,
        n_clientes=n_clientes,
        capacidades=capacidades,
        custos_fixos=custos_fixos,
        demandas=demandas,
        custos_transporte=custos_transporte,
        n_conflitos=n_conflitos,
        pares_conflitantes=pares_conflitantes,
    )

# ====
# MAIN
# ====

instance = load_instance_from_txt(CAMINHO_INSTANCIA)
print(
    f"Instância carregada com sucesso ({CAMINHO_INSTANCIA}).\n"
    f"Facilidades: {instance.J}, Clientes: {instance.I}, Conflitos: {instance.n_conflitos}"
)