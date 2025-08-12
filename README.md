# Projeto de Comparação e Análise de Precipitação entre GPM e MONAN/MPAS

Este diretório contém os scripts, arquivos de dados e saídas gráficas para o estudo de comparação entre as estimativas de precipitação observadas pelo satélite GPM (IMERG) e a simulação do modelo MONAN/MPAS, utilizando diferentes abordagens de remapeamento e posterior análise espectral e de suavização.

## Objetivo
Avaliar a resolução efetiva da precipitação simulada pelo modelo MONAN/MPAS em relação aos dados observacionais do GPM, com foco em:
- Comparação direta dos campos de precipitação (mm/dia);
- Efeitos de remapeamento para grades comuns;
- Análise de suavização e espectral para caracterização da resolução efetiva.

---

## Estrutura de Diretórios
```
MPAS/
├── data_processed               # Arquivos NetCDF intermediários
├── figs                         # Figuras geradas
├── gpm.txt                      # Lista de arquivos GPM
├── mpas.txt                     # Lista de arquivos MPAS
├── README.md                    # Documentação detalhada
└── scripts                      # Scripts Python
    ├── compara.py                       # Comparação entre GPM bruto e MPAS
    ├── compare_gpm_remap_mpas.py        # Comparação entre GPM reamostrado e MPAS
    ├── environment.yml                  # Ambiente Conda
    ├── notebook_spectral.ipynb          # Notebook com análise espectral
    ├── regrid_gpm_to_mpas.py            # Reamostragem do GPM para grade do MPAS
    ├── run_all.py                       # Executa todo o pipeline
    ├── smooth_field.py                  # Suavização genérica de campos 2D
    ├── smooth_gpm.py                    # Suavização do campo GPM
    ├── spectral_analysis.py             # Análise espectral dos campos
    ├── spectral_efficiency.py           # Cálculo da eficiência espectral
    └── spectral_power_comparison.py     # Comparação da potência espectral
```

---

## Scripts Disponíveis

### `regrid_gpm_to_mpas.py`
- **Função**: Reamostra os dados GPM (grade lat-lon 0.1°) para a grade do modelo MPAS.
- **Entrada**: Dados GPM (`.nc4`) e um arquivo MPAS com as coordenadas alvo.
- **Saída**: `data_processed/gpm_remap_to_mpas.nc`, mantida com a dimensão temporal para posterior análise.
- **Notas**:
  - Utiliza `xesmf` com interpolação bilinear.
  - Armazena pesos em `data_processed/weights_gpm_to_mpas.nc` para reaproveitamento.

### `compare_gpm_remap_mpas.py`
- **Função**: Gera uma figura comparando GPM reamostrado e MPAS em média diária.
- **Entrada**: `data_processed/gpm_remap_to_mpas.nc` e `mpas10km.nc4`.
- **Saída**: Figura `figs/comparacao_gpm_remap_mpas_blackstyle.png`.
- **Notas**:
  - Aplicada a mesma escala de cores discreta em ambos os campos.
  - Visualização em painel duplo com fundo preto.

### `compara.py`
- **Função**: Primeira versão da comparação usando os dados originais sem remapeamento.
- **Status**: Substituído por `compare_gpm_remap_mpas.py` para maior consistência espacial.

### 🧼 `smooth_field.py`
- **Função:** Suaviza um campo arbitrário (`.nc`) via média móvel ou filtro gaussiano.
- **Argumentos via CLI:** caminho do arquivo, variável, método e parâmetros.
- **Uso genérico:** Pode ser reaproveitado para suavizar qualquer campo 2D.

---

### 🧼 `smooth_gpm.py`
- **Função:** Aplica suavização ao campo reamostrado do GPM.
- **Métodos usados:**
  - Média móvel 3x3: `uniform_filter`
  - Gaussiano σ=1: `gaussian_filter`
- **Saída:** Dois novos arquivos em `data_processed/` com os campos suavizados.

---

### 📈 `spectral_analysis.py`
- **Função:** Compara os espectros de potência 2D dos campos GPM, suavizados e MPAS.
- **Etapas:**
  1. Aplica FFT2 + `fftshift`
  2. Calcula média radial
  3. Plota todos os espectros
- **Saída:** `figs/espectros_potencia.png`

---

### 📊 `spectral_power_comparison.py`
- **Função:** Plota espectros absolutos lado a lado para avaliar qual campo tem mais energia em diferentes escalas.
- **Saída:** `figs/comparacao_potencia.png`

---

### 📊 `spectral_efficiency.py`
- **Função:** Calcula e plota a eficiência espectral:

\[
\text{Eficiência Espectral}(k) = \frac{E_{\text{GPM}}(k)}{E_{\text{MPAS}}(k)}
\]

Onde:
- \( E(k) \): Espectro de potência em função do número de onda radial \( k \)
- Compara:
  - GPM original
  - GPM média móvel
  - GPM gaussiano
- **Saída:** `figs/eficiencia_espectral.png`

---

### ▶️ `run_all.py`
- **Função:** Executa todos os passos na ordem correta:
  1. Regrid do GPM
  2. Suavizações
  3. Geração dos gráficos comparativos
  4. Análises espectrais
- **Uso:** Basta rodar `python scripts/run_all.py`

# 🧠 Interpretação Física

- **Alta frequência (k alto):** indica estruturas pequenas (chuvas localizadas)
- **Eficiência espectral > 1:** o GPM tem mais energia que o MPAS nessa escala → MPAS filtra estruturas pequenas
- **Eficiência espectral ≈ 1:** MPAS e GPM representam igualmente
- **Eficiência espectral < 1:** improvável, mas pode indicar sobreestimação do MPAS

---

## ✨ Resultados Esperados

- Determinar em que escalas o MPAS perde resolução comparado ao GPM.
- Identificar a resolução efetiva do modelo.
- Avaliar se suavizações aproximam o GPM da resposta espectral do MPAS.


---



## Próximas Etapas
1. **Remapeamento do GPM para a grade *nativa* do MPAS (Voronoi)** – ainda a ser implementado.
2. **Aplicação de suavização nos campos remapeados** – criação de script dedicado.
3. **Análise espectral bidimensional** – geração dos espectros de energia para comparação direta da resolução efetiva entre GPM e MPAS.
4. **Cálculo da razão espectral (eficiência)** – métrica para avaliar perda de informação.

---

## Requisitos
Ambiente Conda com:
```yaml
name: regrid_env
channels:
  - conda-forge
dependencies:
  - python>=3.12
  - xarray
  - netCDF4
  - xesmf
  - esmpy
  - matplotlib
  - cartopy
  - numpy
```

Instalação:
```bash
conda env create -f scripts/environment.yml
conda activate regrid_env
```

---

## 🔁 Execução do Projeto

### Pré-requisitos
Antes de tudo, ative o ambiente Conda:
```bash
conda activate regrid_env
```

### Execução automática
Para rodar todas as etapas de forma automática (reamostragem + geração de figuras), execute o script abaixo:
```bash
python scripts/run_all.py
```

---

### Estrutura Esperada
```
MPAS/
├── data_processed/
│   ├── gpm_remap_to_mpas.nc           ← saída do regrid
│   └── weights_gpm_to_mpas.nc         ← pesos do regrid
├── figs/
│   └── comparacao_gpm_remap_mpas_blackstyle.png
├── scripts/
│   ├── regrid_gpm_to_mpas.py
│   ├── compare_gpm_remap_mpas.py
│   ├── run_all.py
│   └── environment.yml
├── README.md
```

---

Dúvidas ou sugestões? Fale com [João Gerd Zell de Mattos](mailto:joaogerd@inpe.br)


