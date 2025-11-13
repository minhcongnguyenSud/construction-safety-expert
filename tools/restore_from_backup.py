#!/usr/bin/env python3
"""Legacy shim for restore-from-backup tool.

Use tools/kb_pipeline.py --restore (or --all) instead.
"""
import sys


def main():
    print('Please use tools/kb_pipeline.py --restore (or --all).')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
