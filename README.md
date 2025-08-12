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
├── data_processed/               # Arquivos intermediários e processados (NetCDF)
├── figs/                         # Figuras geradas pelos scripts
├── scripts/                      # Scripts Python utilizados nas análises
│   ├── regrid_gpm_to_mpas.py     # Remapeia GPM para grade do MPAS (lat/lon)
│   ├── compare_gpm_remap_mpas.py # Compara GPM remapeado com MPAS (visual)
│   ├── compara.py                # Versão inicial de comparação sem regrid
│   ├── run_all.py                # Executa toda a cadeia de scripts automaticamente
│   ├── weights_gpm_to_mpas.nc    # Arquivo de pesos do remapeamento
│   ├── gpm_remap_to_mpas.nc      # GPM reamostrado (output do regrid)
│   └── environment.yml           # Ambiente Conda com dependências
├── gpm.txt                       # Informações dos dados GPM utilizados
├── mpas.txt                      # Informações dos dados do modelo MPAS
└── README.md                     # Este arquivo
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

### `run_all.py`
- **Função**: Executa automaticamente o fluxo completo do projeto (reamostragem + figura).
- **Ordem de execução**:
  1. `regrid_gpm_to_mpas.py`
  2. `compare_gpm_remap_mpas.py`

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

Para dúvidas ou reprodutibilidade, contatar: **João Gerd Zell de Mattos**

