import sys

if __name__=='__main__':
    if '--cli' in sys.argv:
        from choops_recomp.cli import main
        raise SystemExit(main([arg for arg in sys.argv[1:] if arg!='--cli']))
    from choops_recomp.ui.app import main
    raise SystemExit(main())
