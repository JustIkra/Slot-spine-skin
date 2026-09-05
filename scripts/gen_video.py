#!/usr/bin/env python3
"""Compatibility CLI; video generation is owned by slot-gen."""
if __name__ == "__main__":
    try:
        from slotgen_provider.video import run_cli
    except ImportError:
        raise SystemExit("Install slotgen-provider in this Python environment: pip install -e ../slot-gen")
    try:
        run_cli()
    except (ValueError, RuntimeError, OSError) as error:
        raise SystemExit(str(error))
