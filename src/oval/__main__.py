import argparse
from pathlib import Path
from .build import build, check_sources

parser=argparse.ArgumentParser(description='Explicitly regenerate the offline Oval Report; opening HTML never updates data.')
parser.add_argument('command',choices=['build','evaluate','regenerate','check-sources'])
parser.add_argument('--results',type=Path)
parser.add_argument('--fixtures',type=Path)
parser.add_argument('--provenance',type=Path)
parser.add_argument('--as-of')
parser.add_argument('--check-sources',action='store_true')
args=parser.parse_args()
if args.command=='check-sources' or args.check_sources:
    for row in check_sources(): print(row['url'],row['status'],row.get('reason',''))
if args.command!='check-sources':
    build(args.results,args.fixtures,args.as_of,args.provenance,reevaluate=args.command=='evaluate')
    print('Built The_Oval_Report.html and exports. Read reports/engineering-report.md for evidence and gaps.')
