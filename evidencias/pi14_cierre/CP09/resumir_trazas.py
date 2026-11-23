"""Compara hashes y métricas entre la traza local base y las variantes de CP09."""
import csv
import json
import sys
from pathlib import Path

traces=Path(__file__).with_name("trazas")
base=json.loads((traces/"base.json").read_text(encoding="utf-8"))
records=[]
for file in sorted(traces.glob("*.json")):
    variant=json.loads(file.read_text(encoding="utf-8"))
    if variant["variante"]=="base":
        continue
    for original,current in zip(base["casos"],variant["casos"],strict=True):
        assert original["proyecto"]==current["proyecto"] and original["algoritmo"]==current["algoritmo"]
        before,after=original["etapas"],current["etapas"]
        assert before.keys()==after.keys()
        differing=[name for name in before if before[name]!=after[name]]
        record={
            "variante":variant["variante"],"proyecto":current["proyecto"],"algoritmo":current["algoritmo"],
            "primera_etapa_distinta":differing[0] if differing else "",
            "etapas_distintas":"; ".join(differing),
            "globales_cambio_membresia":before["07_vecinos_globales"]["conjunto_por_fila"]!=after["07_vecinos_globales"]["conjunto_por_fila"],
            "minoritarios_cambio_membresia":before["08_vecinos_minoritarios"]["conjunto_por_fila"]!=after["08_vecinos_minoritarios"]["conjunto_por_fila"],
            "n_sinteticos_base":before["09_muestras_ADASYN"]["x"]["shape"][0],
            "n_sinteticos_variante":after["09_muestras_ADASYN"]["x"]["shape"][0],
        }
        for name,value in current["local"].items():
            record.update({f"{name}_variante":value,f"{name}_base":original["local"][name],
                           f"{name}_historico":original["historico_agregado"][name],
                           f"delta_{name}_vs_base":value-original["local"][name]})
        records.append(record)
writer=csv.DictWriter(sys.stdout,fieldnames=list(records[0]),lineterminator="\n")
writer.writeheader()
writer.writerows(records)
