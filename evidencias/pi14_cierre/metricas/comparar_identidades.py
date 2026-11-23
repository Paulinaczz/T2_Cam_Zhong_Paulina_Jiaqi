"""Contrasta identidades candidatas con los CSV de referencia, sin reescribirlos."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
import numpy as np
from research import entrenamiento_defectos as research

data, _ = research.load_all(Path(sys.argv[1]))
writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(["proyecto","identidad","filas_comparables","filas_coinciden","filas_totales"])
for project,(x,_) in data.items():
    with np.errstate(divide="ignore",invalid="ignore"):
        identities = [
            ("n","n=total_Op+total_Opnd",x.total_Op+x.total_Opnd),
            ("v","v=n*log2(uniq_Op+uniq_Opnd)",x.n*np.log2(x.uniq_Op+x.uniq_Opnd)),
            ("d","d=(uniq_Op/2)*(total_Opnd/uniq_Opnd)",x.uniq_Op/2*x.total_Opnd/x.uniq_Opnd),
            ("l","l=1/d",1/x.d), ("i","i=l*v",x.l*x.v), ("i","i=v/d",x.v/x.d),
            ("e","e=d*v",x.d*x.v), ("t","t=e/18",x.e/18),
            ("b","b=v/3000",x.v/3000), ("b","b=e^(2/3)/3000",x.e**(2/3)/3000),
            ("branchCount","branchCount=2*v(g)-1",2*x["v(g)"]-1),
        ]
    for key, equation, expected in identities:
        comparable=np.isfinite(x[key]) & np.isfinite(expected)
        count=np.isclose(x[key][comparable],expected[comparable],atol=.005,rtol=.01).sum()
        writer.writerow([project,equation,int(comparable.sum()),int(count),len(x)])
    comparable=np.isfinite(x["loc"]) & np.isfinite(x.lOCode)
    writer.writerow([project,"loc=lOCode (exacta)",int(comparable.sum()),
                     int((x["loc"][comparable]==x.lOCode[comparable]).sum()),len(x)])
