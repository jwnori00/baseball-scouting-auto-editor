"""PyInstaller entry point. Self-test runs inside the frozen executable."""
import sys

if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--portable-self-test':
        from packaging_support.selftest import main
        raise SystemExit(main(sys.argv[2]))
    from gui.app import main
    raise SystemExit(main())
