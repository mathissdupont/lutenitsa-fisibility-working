"""Command-line entry point; offline reproducibility is the default."""
import argparse
from .common import ROOT, write_json

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['collect','import','validate','regress','optimize','finance','report','all','demo'])
    parser.add_argument('--online',action='store_true',help='Download only registered public files')
    parser.add_argument('--file',help='Manual agricultural observation CSV to preserve/import')
    args=parser.parse_args(argv)
    from .collection import collect,import_observations
    from .data import process,extract_distances
    from .statistics import regress
    from .materials import run_materials
    from .optimization import optimize
    from .finance import run_finance
    from .decision import decision
    if args.command=='import':
        if not args.file:
            parser.error('--file is required for import')
        print(import_observations(args.file))
        return
    if args.command in ['collect','all']:
        print('collect:',len(collect(args.online)),'source attempts')
    if args.command in ['validate','all']:
        print('validate:',process())
        # Distance extraction is deterministic and cached against raw source SHA-256.
        from .common import sha256
        import json
        source=ROOT/'data/raw/official/ilcemesafe.xlsx'
        stamp=ROOT/'reports/distance_source_hash.json'
        expected=sha256(source) if source.exists() else None
        previous=json.loads(stamp.read_text()) if stamp.exists() else None
        if not (ROOT/'data/processed/distance_matrix.csv').exists() or previous!=expected:
            extract_distances()
            write_json(expected,'reports/distance_source_hash.json')
    if args.command in ['regress','all']:
        print('regress:',{k:len(v) for k,v in regress().items()})
    if args.command in ['optimize','all']:
        print('materials:',run_materials()[1])
        print('optimize:',optimize())
        print('screening:',decision())
    if args.command in ['finance','all']:
        print('finance:',run_finance())
    if args.command in ['report','all']:
        from .reporting import report
        print('report:',report())
    if args.command=='demo':
        print('ASSUMED LEGACY DEMO ONLY:',optimize(demo=True))
        from .scenarios import legacy_financial_demo
        legacy_financial_demo()

if __name__=='__main__':
    main()
