from __future__ import annotations
import argparse
import subprocess
from pathlib import Path


def _run(modname: str, args: list[str]) -> None:
    """
    Execute a script from the `scripts` package as a Python module.

    This function constructs and runs a command of the form:
    `python -m scripts.<modname> <args>`.

    Parameters
    ----------
    modname : str
        The name of the script (without `.py` extension) inside the `scripts` package.
    args : list of str
        List of additional arguments to pass to the script.
    """
    cmd = ["python", "-m", f"scripts.{modname}", *args]
    print("[INFO] Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    """
    Command-line interface (CLI) entry point for GPM×MPAS processing workflows.

    Provides subcommands to execute individual or full workflows including:
    regridding, smoothing, comparison, spectral analysis, and complete runs.

    Subcommands
    -----------
    regrid
        Regrid GPM data to MPAS grid.
    smooth
        Apply smoothing filters to the regridded GPM data.
    compare
        Compare MPAS and processed GPM precipitation.
    spectral
        Perform spectral analysis (power, efficiency, or both).
    run-all
        Execute the full pipeline: regrid → smooth → compare → spectral.

    Notes
    -----
    Each subcommand internally calls the corresponding Python script
    from the `scripts` package using the `_run()` helper function.
    """
    p = argparse.ArgumentParser(
        prog="python -m scripts.cli",
        description="GPM×MPAS processing CLI"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # regrid
    p_regrid = sub.add_parser("regrid", help="Regrid GPM data to MPAS grid.")
    p_regrid.add_argument("--gpm", required=True, help="Path to GPM dataset.")
    p_regrid.add_argument("--mpas", required=True, help="Path to MPAS dataset.")
    p_regrid.add_argument("--weights", default="data_processed/weights_gpm_to_mpas.nc",
                          help="Path to weight file for regridding.")
    p_regrid.add_argument("--root", default=None, help="Custom project root directory.")

    # smooth
    p_smooth = sub.add_parser("smooth", help="Apply smoothing to regridded data.")
    p_smooth.add_argument("--sigma", type=float, default=1.0,
                          help="Standard deviation for Gaussian smoothing.")
    p_smooth.add_argument("--root", default=None, help="Custom project root directory.")

    # compare
    p_compare = sub.add_parser("compare", help="Compare MPAS and GPM precipitation fields.")
    p_compare.add_argument("--mpas", required=True, help="Path to MPAS dataset.")
    p_compare.add_argument("--style", choices=["black", "light"], default="black",
                           help="Plot style for comparison.")
    p_compare.add_argument("--root", default=None, help="Custom project root directory.")

    # spectral
    p_spec = sub.add_parser("spectral", help="Perform spectral analysis.")
    p_spec.add_argument("mode", choices=["power", "efficiency", "all"],
                        help="Type of spectral analysis to perform.")
    p_spec.add_argument("--mpas", required=True, help="Path to MPAS dataset.")
    p_spec.add_argument("--trim", type=int, default=10,
                        help="Number of grid points to trim from boundaries.")
    p_spec.add_argument("--sigma", type=float, default=1.0,
                        help="Standard deviation for Gaussian smoothing.")
    p_spec.add_argument("--root", default=None, help="Custom project root directory.")

    # run-all
    p_all = sub.add_parser("run-all", help="Run the full GPM×MPAS workflow.")
    p_all.add_argument("--gpm", required=True, help="Path to GPM dataset.")
    p_all.add_argument("--mpas", required=True, help="Path to MPAS dataset.")
    p_all.add_argument("--weights", default="data_processed/weights_gpm_to_mpas.nc",
                       help="Path to weight file for regridding.")
    p_all.add_argument("--root", default=None, help="Custom project root directory.")

    args = p.parse_args()

    if args.cmd == "regrid":
        _run("regrid", [
            "--gpm", args.gpm,
            "--mpas", args.mpas,
            "--weights", args.weights
        ] + (["--root", args.root] if args.root else []))

    elif args.cmd == "smooth":
        _run("smooth", [
            "--sigma", str(args.sigma)
        ] + (["--root", args.root] if args.root else []))

    elif args.cmd == "compare":
        base = ["--mpas", args.mpas, "--style", args.style]
        if args.root:
            base += ["--root", args.root]
        _run("compare", base)

    elif args.cmd == "spectral":
        base = [
            args.mode,
            "--mpas", args.mpas,
            "--trim", str(args.trim),
            "--sigma", str(args.sigma)
        ]
        if args.root:
            base += ["--root", args.root]
        _run("spectral", base)

    elif args.cmd == "run-all":
        _run("regrid", [
            "--gpm", args.gpm,
            "--mpas", args.mpas,
            "--weights", args.weights
        ] + (["--root", args.root] if args.root else []))

        _run("smooth", (["--root", args.root] if args.root else []))

        _run("compare", [
            "--mpas", args.mpas
        ] + (["--root", args.root] if args.root else []))

        _run("spectral", [
            "all",
            "--mpas", args.mpas
        ] + (["--root", args.root] if args.root else []))


if __name__ == "__main__":
    main()

