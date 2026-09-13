# -*- coding: utf-8 -*-
import re

src = open(r"F:\AI产物\doubao\deskpet\pet_qt.py", encoding="utf-8").read()
for m in re.finditer(r'"stretch[^"]*"[^}]{0,200}', src):
    print(m.group(0))
    print("---")
for k in ["TRANSITION_PATHS", "REVERSE_PATHS", "SEQUENCES =", "FRAME_FILES = {"]:
    i = src.find(k)
    if i >= 0:
        print("===", k, "===")
        print(src[i:i+700])
        print()
