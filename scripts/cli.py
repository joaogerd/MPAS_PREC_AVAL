from __future__ import annotations
import argparse
import subprocess
from pathlib import Path

def _run(modname: str, args: list[str]) -> None:
    # Executa "python -m scripts.<modname> <args>"
    cmd = ["python", "-m", f"scripts.{modname}", *args]
    print("[INFO] Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)

def main() -> None:
    p = argparse.ArgumentParser(prog="python -m scripts.cli", description="GPM×MPAS processing CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    # regrid
    p_regrid = sub.add_parser("regrid")
    p_regrid.add_argument("--gpm", required=True)
    p_regrid.add_argument("--mpas", required=True)
    p_regrid.add_argument("--weights", default="data_processed/weights_gpm_to_mpas.nc")
    p_regrid.add_argument("--root", default=None)

    # smooth
    p_smooth = sub.add_parser("smooth")
    p_smooth.add_argument("--sigma", type=float, default=1.0)
    p_smooth.add_argument("--root", default=None)

    # compare
    p_compare = sub.add_parser("compare")
    p_compare.add_argument("--mpas", required=True)
    p_compare.add_argument("--style", choices=["black","light"], default="black")
    p_compare.add_argument("--root", default=None)

    # spectral
    p_spec = sub.add_parser("spectral")
    p_spec.add_argument("mode", choices=["power","efficiency","all"])
    p_spec.add_argument("--mpas", required=True)
    p_spec.add_argument("--trim", type=int, default=10)
    p_spec.add_argument("--sigma", type=float, default=1.0)
    p_spec.add_argument("--root", default=None)

    # run-all
    p_all = sub.add_parser("run-all")
    p_all.add_argument("--gpm", required=True)
    p_all.add_argument("--mpas", required=True)
    p_all.add_argument("--weights", default="data_processed/weights_gpm_to_mpas.nc")
    p_all.add_argument("--root", default=None)

    args = p.parse_args()
    if args.cmd == "regrid":
        _run("regrid", ["--gpm", args.gpm, "--mpas", args.mpas, "--weights", args.weights] + (["--root", args.root] if args.root else []))
    elif args.cmd == "smooth":
        _run("smooth", ["--sigma", str(args.sigma)] + (["--root", args.root] if args.root else []))
    elif args.cmd == "compare":
        base = ["--mpas", args.mpas, "--style", args.style]
        if args.root: base += ["--root", args.root]
        _run("compare", base)
    elif args.cmd == "spectral":
        base = [args.mode, "--mpas", args.mpas, "--trim", str(args.trim), "--sigma", str(args.sigma)]
        if args.root: base += ["--root", args.root]
        _run("spectral", base)
    elif args.cmd == "run-all":
        _run("regrid", ["--gpm", args.gpm, "--mpas", args.mpas, "--weights", args.weights] + (["--root", args.root] if args.root else []))
        _run("smooth", (["--root", args.root] if args.root else []))
        _run("compare", ["--mpas", args.mpas] + (["--root", args.root] if args.root else []))
        _run("spectral", ["all", "--mpas", args.mpas] + (["--root", args.root] if args.root else []))

if __name__ == "__main__":
    main()

