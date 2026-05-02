import pandas as pd
from pyomo.environ import *
from pyomo.opt import TerminationCondition
import matplotlib.pyplot as plt
import numpy as np

# ==============================
# 0) MODEL PARAMETRELERİ
# ==============================
P = 5
TARGET_BRAND = "TotalEnergies"
TARGET_CITY = "Berlin"

KM_PER_DEG = 111.0
MIN_DIST_KM = 10.0
MIN_DIST_DEG2 = (MIN_DIST_KM / KM_PER_DEG) ** 2   # 10 km'nin kare derecesi

# ==============================
# 1) VERİLERİ OKU
# ==============================

# a) İstasyonlar (sadece görselleştirme için)
try:
    stations = pd.read_csv("stations.csv", encoding="utf-8")
except FileNotFoundError:
    stations = pd.read_csv("stations (1).csv", encoding="utf-8")

existing_stations = stations[
    (stations["brand"] == TARGET_BRAND) &
    (stations["city"] == TARGET_CITY)
].copy()
existing_stations = existing_stations[["name", "latitude", "longitude"]].reset_index(drop=True)

# b) Bezirke + ağırlıklar (proje1.xlsx / Sheet1)
zones = pd.read_excel("proje1.xlsx", sheet_name="Sheet1")

def parse_lat_lon(val):
    if isinstance(val, str):
        parts = val.split(',')
        if len(parts) == 2:
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())
            return lat, lon
    return None, None

lat_list, lon_list = zip(*zones["Lat / Lon (Merkez)"].apply(parse_lat_lon))
zones["latitude"] = lat_list
zones["longitude"] = lon_list


zones["weight"] = (
    0.25  * zones["Nüfus (1-10)"] +
    0.4 * zones["Trafik & Araç (1-10)"] +
    0.35  * zones["Sanayi (1-10)"]
)

demand_df = zones[["Bölge (Bezirk)", "latitude", "longitude", "weight"]].copy()
demand_df.reset_index(drop=True, inplace=True)

# ==============================
# 2) PARAMETRELER
# ==============================

I = list(demand_df.index)           # talep noktaları
J = list(range(1, P + 1))          # yeni tesisler

x_i = {i: float(demand_df.loc[i, "longitude"]) for i in I}
y_i = {i: float(demand_df.loc[i, "latitude"])  for i in I}

x_min, x_max = demand_df["longitude"].min(), demand_df["longitude"].max()
y_min, y_max = demand_df["latitude"].min(),  demand_df["latitude"].max()

w_ji = {(j, i): float(demand_df.loc[i, "weight"]) for j in J for i in I}

# Tesis çiftleri (mesafe kısıtları için)
J_pairs = [(j, k) for j in J for k in J if j < k]

# ==============================
# 3) PYOMO MODELİ (MFRLP - L1 + TESİS–TESİS MESAFE)
# ==============================

Model = ConcreteModel()

Model.I = Set(initialize=I)
Model.J = Set(initialize=J)
Model.J_pairs = Set(initialize=J_pairs, dimen=2)

Model.a = Param(Model.I, initialize=x_i)   # lon
Model.b = Param(Model.I, initialize=y_i)   # lat
Model.w = Param(Model.J, Model.I, initialize=w_ji)

# Yeni tesis koordinatları
Model.X = Var(Model.J, bounds=(x_min, x_max))
Model.Y = Var(Model.J, bounds=(y_min, y_max))

# Demand–facility L1 linearizasyonu
Model.r = Var(Model.J, Model.I, within=NonNegativeReals)
Model.s = Var(Model.J, Model.I, within=NonNegativeReals)
Model.u = Var(Model.J, Model.I, within=NonNegativeReals)
Model.t = Var(Model.J, Model.I, within=NonNegativeReals)

# ---- Fark eşitlikleri (L1 için) ----
def new_exist_x_diff(M, j, i):
    return M.r[j, i] - M.s[j, i] == M.X[j] - M.a[i]
Model.NEXD = Constraint(Model.J, Model.I, rule=new_exist_x_diff)

def new_exist_y_diff(M, j, i):
    return M.u[j, i] - M.t[j, i] == M.Y[j] - M.b[i]
Model.NEYD = Constraint(Model.J, Model.I, rule=new_exist_y_diff)

# ---- TESİS–TESİS MESAFE KISITI (EUCLIDEAN ≥ 10 KM) ----
def fac_fac_min_dist(M, j, k):
    return (M.X[j] - M.X[k])**2 + (M.Y[j] - M.Y[k])**2 >= MIN_DIST_DEG2
Model.FacSep = Constraint(Model.J_pairs, rule=fac_fac_min_dist)

# ---- AMAÇ FONKSİYONU: SADECE TALep–TESİS L1 ----
def obj_rule(M):
    return sum(
        M.w[j, i] * (M.r[j, i] + M.s[j, i] + M.u[j, i] + M.t[j, i])
        for j in M.J for i in M.I
    )
Model.Obj = Objective(rule=obj_rule, sense=minimize)

# ==============================
# 4) ÇÖZÜM
# ==============================

solver = SolverFactory("gurobi")
solver.options["NonConvex"] = 2   # kareli kısıtlar için

try:
    result = solver.solve(Model, tee=True)

    if result.solver.termination_condition in (
        TerminationCondition.optimal,
        TerminationCondition.feasible,
    ):
        new_stations = []
        for j in Model.J:
            x_val = value(Model.X[j])
            y_val = value(Model.Y[j])
            new_stations.append({"facility": j, "longitude": x_val, "latitude": y_val})
        new_df = pd.DataFrame(new_stations)

        print(f"\n{TARGET_CITY} için önerilen yeni tesis koordinatları (P={P}):")
        print(new_df)
        print(f"Minimum Toplam Ağırlıklı L1 Uzaklık: {value(Model.Obj):.2f}")

        # ======== GRAFİK ========
        plt.figure(figsize=(10, 8))

        # Talep bölgeleri
        plt.scatter(
            demand_df["longitude"],
            demand_df["latitude"],
            s=demand_df["weight"]**2.5 * 10,
            alpha=0.6,
            c="green",
            label="Talep Bölgeleri (Bezirk, ağırlıklı)"
        )
        for i, row in demand_df.iterrows():
            plt.text(row["longitude"], row["latitude"],
                     row["Bölge (Bezirk)"], fontsize=8, ha="center")

        # Mevcut istasyonlar
        if not existing_stations.empty:
            plt.scatter(
                existing_stations["longitude"],
                existing_stations["latitude"],
                c="blue",
                marker=".",
                s=40,
                alpha=0.6,
                label="Mevcut TotalEnergies İstasyonları (Berlin)"
            )

        # Yeni tesisler
        plt.scatter(
            new_df["longitude"],
            new_df["latitude"],
            s=250,
            marker="*",
            color="red",
            edgecolor="black",
            label="Yeni Tesisler (MFRLP + tesis–tesis ≥ 10 km)"
        )

        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.title(f"Multiple Facility Location (P={P}) - Berlin\n10 km tesis–tesis mesafe, normalize ağırlıklar")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.4)
        plt.show()
        plt.savefig("sonuc.png")
        

    else:
        print("Optimizasyon çözülemedi veya optimum çözüm bulunamadı.")
        print("Durum:", result.solver.termination_condition)

except Exception as e:
    print("\nÇözücü veya çalıştırma hatası:", e)
