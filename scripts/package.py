"""Package only deliverable files with stable timestamps and no environment state."""
from pathlib import Path
import zipfile

root=Path(__file__).resolve().parents[1]
destination=root/'work/The_Oval_Report_bundle.zip'
destination.parent.mkdir(exist_ok=True)
directories=['baseline','data','exports','reports','scripts','src','tests','web','.github']
files=[root/p for p in ['README.md','requirements.txt','pyproject.toml','package.json','package-lock.json','The_Oval_Report.html']]
for directory in directories:files.extend(p for p in (root/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.pyc'))
with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
    for p in sorted(files):
        info=zipfile.ZipInfo(str(Path('The_Oval_Report')/p.relative_to(root)),date_time=(2026,11,9,0,0,0))
        info.compress_type=zipfile.ZIP_DEFLATED
        archive.writestr(info,p.read_bytes())
print(destination)
