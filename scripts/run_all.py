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


scripts_dir = "scripts"

def run(script):
    print(f"[INFO] Executando: {script}")
    subprocess.run(["python", os.path.join(scripts_dir, script)], check=True)

# Passo 1 - Reamostragem GPM para grade MPAS
run("regrid_gpm_to_mpas.py")

# Passo 2 - Suavizações (média móvel e gaussiana)
run("smooth_gpm.py")

# Passo 3 - Comparações visuais
run("compara.py")
run("compare_gpm_remap_mpas.py")

# Passo 4 - Análises espectrais
run("spectral_analysis.py")
run("spectral_power_comparison.py")
run("spectral_efficiency.py")

print("[INFO] Todos os passos foram concluídos com sucesso.")


