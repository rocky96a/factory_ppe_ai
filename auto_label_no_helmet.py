from pathlib import Path
from ultralytics import YOLO
from PIL import Image
import shutil

BASE=Path("/home/souvik/bakup/factory_ppe_ai")
SRC=BASE/"datasets/factory_raw/no_helmet"
OUT=BASE/"datasets/factory_annotated"
for s in ("train","val","test"):
    (OUT/"images"/s).mkdir(parents=True,exist_ok=True)
    (OUT/"labels"/s).mkdir(parents=True,exist_ok=True)
imgs=sorted([p for p in SRC.iterdir() if p.suffix.lower() in (".jpg",".jpeg",".png")])
n=len(imgs); a=int(n*.7); b=int(n*.9)
splits={"train":imgs[:a],"val":imgs[a:b],"test":imgs[b:]}
print("Found",n,"images", {k:len(v) for k,v in splits.items()})
print("Loading model...")
model=YOLO(str(BASE/"yolo11n.pt"))
print("Model loaded")
for split,files in splits.items():
    for i,src in enumerate(files,1):
        shutil.copy2(src,OUT/"images"/split/src.name)
        with Image.open(src) as im: W,H=im.size
        r=model.predict(source=str(src),classes=[0],conf=.25,imgsz=640,verbose=False)[0]
        lines=[]
        if r.boxes is not None:
            for x1,y1,x2,y2 in r.boxes.xyxy.cpu().tolist():
                pw,ph=x2-x1,y2-y1
                if pw<10 or ph<20: continue
                hw,hh=pw*.55,ph*.30; cx=(x1+x2)/2; cy=y1+ph*.16
                hx1=max(0,cx-hw/2); hx2=min(W,cx+hw/2)
                hy1=max(0,cy-hh/2); hy2=min(H,cy+hh/2)
                lines.append(f"1 {((hx1+hx2)/2)/W:.6f} {((hy1+hy2)/2)/H:.6f} {(hx2-hx1)/W:.6f} {(hy2-hy1)/H:.6f}")
        (OUT/"labels"/split/f"{src.stem}.txt").write_text("\n".join(lines)+("\n" if lines else ""))
        if i%10==0 or i==len(files): print(f"{split}: {i}/{len(files)}")
print("DONE")
