import subprocess, re, sys, glob, json, cv2, numpy as np
from xml.etree import ElementTree as ET
BL=9; W=612; SAFE=27   # 0.375 in
urls=json.load(open('urls.json'))
for n,f in enumerate(sorted(glob.glob('/mnt/user-data/outputs/Robo-Learns-To-See-Book-*.pdf')),1):
    print('==',f.split('/')[-1])
    info=subprocess.run(['pdfinfo','-f','1','-l','24','-box',f],capture_output=True,text=True).stdout
    pages=int(re.search(r'Pages:\s+(\d+)',info).group(1)); sizes=set(re.findall(r'Page\s+\d+ size:\s+([\d.]+ x [\d.]+)',info))
    print(' pages',pages,'sizes',sizes)
    fonts=subprocess.run(['pdffonts',f],capture_output=True,text=True).stdout.splitlines()[2:]
    print(' fonts embedded:',all(l.split()[-5]=='yes' for l in fonts) if fonts else None,len(fonts),'fonts')
    raw=open(f,'rb').read()
    print(' transparency markers:',len(re.findall(rb'/ca\s|/CA\s|/SMask|/BM\s',raw)))
    # text bbox inside safe area
    xml=subprocess.run(['pdftotext','-bbox',f,'-'],capture_output=True,text=True).stdout
    xml=re.sub(r'<!DOCTYPE[^>]*>','',xml); xml=xml.replace('xmlns="http://www.w3.org/1999/xhtml"','')
    root=ET.fromstring(xml); bad=0; minfs=99
    for i,pg in enumerate(root.iter('page'),1):
        ox=0 if i%2 else BL
        for w in pg.iter('word'):
            x0,y0,x1,y1=[float(w.get(k)) for k in('xMin','yMin','xMax','yMax')]
            if x0<ox+SAFE-.5 or x1>ox+W-SAFE+.5 or y0<BL+SAFE-.5 or y1>BL+W-SAFE+.5:
                bad+=1; print('  OUT p%d %-12s x%.0f-%.0f y%.0f-%.0f'%(i,w.text[:12],x0-ox,x1-ox,y0-BL,y1-BL))
    print(' words outside 0.375in safe zone:',bad)
    # images effective dpi
    im=subprocess.run(['pdfimages','-list',f],capture_output=True,text=True).stdout.splitlines()[2:]
    dp=[(int(l.split()[0]),int(l.split()[12]),int(l.split()[13])) for l in im if len(l.split())>13 and l.split()[2]=='image']
    low=[d for d in dp if min(d[1],d[2])<290]
    print(' images',len(dp),'min ppi',min(min(d[1],d[2]) for d in dp) if dp else None,'low:',low[:6])
