# run_all.py
# Script mestre para rodar toda a cadeia de processamento e comparacao GPM x MPAS

import subprocess
import os

# Diretórios base
scripts_dir = "scripts"
data_dir = "data_processed"
figs_dir = "figs"

# Cria diretórios, se não existirem
os.makedirs(data_dir, exist_ok=True)
os.makedirs(figs_dir, exist_ok=True)

print("[1/3] Reamostrando GPM para grade do MPAS...")
subprocess.run(["python", os.path.join(scripts_dir, "regrid_gpm_to_mpas.py")], check=True)

print("[2/3] Gerando comparação visual entre GPM reamostrado e MPAS...")
subprocess.run(["python", os.path.join(scripts_dir, "compare_gpm_remap_mpas.py")], check=True)

print("[3/3] Comparação finalizada. Verifique os resultados na pasta 'figs'.")

