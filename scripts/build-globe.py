"""Build the globe textures and region maps for src/globe from OpenYAMM renders.

Usage: python3 scripts/build-globe.py RENDERS_DIR src/globe
RENDERS_DIR holds maps/mm6, maps/mm7, maps/mm8 with *.odm.png (and *.blv.png) renders.
"""
import sys, json, os, glob, numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi
R=sys.argv[1]; OUT=sys.argv[2]
P=400; OV=0.16; S=int(round(P/(1-OV))); M=(S/P-1)/2; CELL=12.0
rng=np.random.default_rng(7)

def fbm2(h,w,scale,octv=5,seed=0,gain=0.5):
    r=np.random.default_rng(seed); out=np.zeros((h,w),np.float32); amp=1; tot=0; s=scale
    for o in range(octv):
        gh,gw=max(2,int(h/s)+3),max(2,int(w/s)+3)
        g=r.random((gh,gw),dtype=np.float32)
        big=cv2.resize(g,(int(gw*s),int(gh*s)),interpolation=cv2.INTER_CUBIC)
        oy,ox=int(r.integers(0,max(1,int(s)))),int(r.integers(0,max(1,int(s))))
        out+=amp*big[oy:oy+h,ox:ox+w]; tot+=amp; amp*=gain; s=max(1.5,s/2)
    return out/tot*2-1   # ~[-1,1]

def hash3(i,j,k,seed):
    n=(i*374761393+j*668265263+k*2147483647+seed*144665)&0xFFFFFFFF
    n=(n^(n>>13))*1274126177&0xFFFFFFFF
    n=n^(n>>16)
    return (n&0xFFFF).astype(np.float32)/65535.0
def vnoise3(x,y,z,seed):
    xi=np.floor(x).astype(np.int64); yi=np.floor(y).astype(np.int64); zi=np.floor(z).astype(np.int64)
    fx=(x-xi).astype(np.float32); fy=(y-yi).astype(np.float32); fz=(z-zi).astype(np.float32)
    fx=fx*fx*(3-2*fx); fy=fy*fy*(3-2*fy); fz=fz*fz*(3-2*fz)
    out=0
    for dx in (0,1):
        for dy in (0,1):
            for dz in (0,1):
                wgt=(fx if dx else 1-fx)*(fy if dy else 1-fy)*(fz if dz else 1-fz)
                out=out+wgt*hash3(xi+dx,yi+dy,zi+dz,seed)
    return out
def fbm3(x,y,z,freq,octv=5,seed=0):
    out=0;amp=1;tot=0
    for o in range(octv):
        out=out+amp*vnoise3(x*freq+17.3*o,y*freq+5.1*o,z*freq+9.7*o,seed+o); tot+=amp; amp*=0.5; freq*=2
    return out/tot*2-1

def sstep(x,a,b):
    t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)

# ---------------- biomes: low, mid, high colours
B={
 'grass':   [(78,124,60),(126,146,88),(158,150,128)],
 'lush':    [(64,128,58),(112,150,84),(150,150,124)],
 'forest':  [(46,96,52),(84,122,72),(140,138,116)],
 'snow':    [(206,220,230),(232,240,246),(252,253,255)],
 'tundra':  [(150,170,150),(206,216,214),(246,248,250)],
 'desert':  [(218,190,124),(232,208,146),(196,156,104)],
 'redsand': [(206,132,66),(222,160,90),(156,88,52)],
 'swamp':   [(66,92,56),(98,108,66),(124,118,92)],
 'volcanic':[(118,96,80),(96,78,70),(66,56,58)],
 'eofol':   [(128,66,46),(104,54,42),(64,42,40)],
 'waste':   [(112,106,92),(134,124,108),(96,88,88)],
 'shadow':  [(92,88,104),(116,108,124),(74,68,84)],
 'savanna': [(138,150,84),(168,164,104),(154,138,108)],
 'tropic':  [(72,138,66),(128,160,92),(166,158,126)],
 'barren':  [(146,128,96),(166,148,112),(126,108,92)],
 'hills':   [(96,124,70),(138,146,98),(164,154,134)],
}
# ---------------- layout
CONT={
 'enroth':{'title':'Enroth','lon0':-100,'lat0':22,'xc':2.5,'yc':1.5,'ext':(-1,-1,6,4),
   'tiles':[('mm6/outa1',0,0,'Sweet Water','savanna'),('mm6/outb1',1,0,'Kriegspire','volcanic'),('mm6/outc1',2,0,'Frozen Highlands','snow'),('mm6/outd1',3,0,'Silver Cove','tundra'),('mm6/oute1',4,0,'Eel Infested Waters','tropic'),
            ('mm6/outa2',0,1,'Paradise Valley','lush'),('mm6/outb2',1,1,'Blackshire','hills'),('mm6/outc2',2,1,'Free Haven','grass'),('mm6/outd2',3,1,'Bootleg Bay','tropic'),('mm6/oute2',4,1,'Misty Islands','lush'),
            ('mm6/outa3',0,2,"Hermit's Isle",'barren'),('mm6/outb3',1,2,'Dragonsand','desert'),('mm6/outc3',2,2,'Mire of the Damned','swamp'),('mm6/outd3',3,2,'Castle Ironfist','grass'),('mm6/oute3',4,2,'New Sorpigal','lush')],
   'blobs':[]},
 'jadame':{'title':'Jadame','lon0':-8,'lat0':24,'xc':1.5,'yc':1.5,'ext':(-1,-1,4,5),
   'tiles':[('mm8/out07',0,0,'Murmurwoods','forest'),('mm8/out03',1,0,'Alvar','hills'),('mm8/out04',2,0,'Ironsand Desert','redsand'),
            ('mm8/out05',0,1,'Garrote Gorge','grass'),('mm8/out02',1,1,'Ravenshore','lush'),('mm8/out06',2,1,'Shadowspire','shadow'),
            ('mm8/out08',0,2,'Ravage Roaming','savanna'),('mm8/out01',2,2,'Dagger Wound Islands','tropic'),
            ('mm8/out13',1,2.85,'Regna Island','tropic')],
   'blobs':[(-0.15,3.55,0.16,'tropic'),(0.45,4.25,0.13,'tropic'),(2.45,3.6,0.17,'tropic'),(2.95,4.2,0.12,'volcanic'),(3.35,3.3,0.12,'tropic')]},
 'antagarich':{'title':'Antagarich','lon0':75,'lat0':-18,'xc':2.25,'yc':2.0,'ext':(-1.25,-1,6.1,5.3),
   'tiles':[('mm7/7out05',1,0,'Deyja','waste'),('mm7/7out04',2,0,'Tularean Forest','forest'),('mm7/out14',3,0,'Avlee','lush'),
            ('mm7/7out13',0,1,'Tatalia','swamp'),('mm7/7out03',1,1,'Erathia','grass'),('mm7/7out02',2,1,'Harmondale','hills'),
            ('mm7/7out06',1,2,'Bracada Desert','desert'),('mm7/out11',2,2,'Barrow Downs','hills'),('mm7/out12',3,2,'Land of the Giants','eofol'),
            ('mm7/7out01',4.6,0.15,'Emerald Island','lush'),('mm7/out09',1.3,3.35,'Evenmorn Island','forest'),('mm7/out10',3.55,3.5,'Mount Nighon','volcanic')],
   'blobs':[(-0.3,-0.05,0.5,'snow'),(0.5,2.45,0.62,'savanna'),(3.5,1.5,0.6,'hills')]},
}
ISLES=[ # lon,lat, blobs (dx,dy,r,biome) in cells
 (-52,-20,[(0,0,0.42,'grass'),(0.5,0.35,0.12,'grass')]),
 (132,30,[(0,0,0.5,'barren'),(0.45,0.75,0.3,'barren'),(-0.2,-0.7,0.22,'barren')]),
 (166,6,[(0,0,0.3,'volcanic'),(0.3,0.7,0.2,'volcanic'),(-0.3,-0.6,0.16,'volcanic')]),
 (-166,-22,[(0,0,0.28,'volcanic'),(0.5,-0.5,0.18,'volcanic'),(-0.35,0.6,0.15,'volcanic')]),
 (150,-34,[(0,0,0.22,'volcanic'),(0.6,0.2,0.14,'volcanic')]),
 (-150,58,[(0,0,0.3,'snow'),(0.6,0.1,0.18,'snow')]),
 (30,-50,[(0,0,0.25,'tundra'),(-0.5,0.2,0.14,'tundra')]),
 (-60,48,[(0,0,0.2,'tundra')]),
 (-128,-46,[(0,0,0.3,'tropic'),(0.55,0.3,0.15,'tropic')]),
]

def tile_fields(p):
    a=np.asarray(Image.open(f'{R}/maps/{p}.odm.png').convert('RGB').crop((24,24,1500,1500))).astype(np.float32)
    r,g,b=a[...,0],a[...,1],a[...,2]
    void=(np.abs(a-np.array([28,28,32],np.float32)).sum(-1)<16)
    water=(b>g+20)&(b>100)&(r<95)
    shore=np.abs(a-np.array([112,132,140],np.float32)).sum(-1)<22
    mx=a.max(-1); mn=a.min(-1)
    terr=~void&~water&~shore&(b<g+4)&(r-g<=24)&(mx-mn<100)&(g>40)
    road=terr&(np.abs(r-g)<=6)&(b<0.56*g)&(g>60)&(g<100)
    terr&=~road
    bld=~(void|water|shore|terr|road)
    L=np.where(water|void,-1.0,np.where(shore,0.0,1.0)).astype(np.float32)
    e=np.clip(1-((g-r)/np.maximum(g,1))/0.4,0,1.25)
    lum=0.3*r+0.59*g+0.11*b
    exp=np.interp(e,[0,.5,1,1.25],[86,116,178,200]).astype(np.float32)
    sh=lum/exp
    w=terr.astype(np.float32)
    def fill(f):
        num=cv2.GaussianBlur(f*w,(0,0),7); den=cv2.GaussianBlur(w,(0,0),7)
        ff=num/np.maximum(den,1e-3); ff[den<1e-3]=f[terr].mean() if terr.any() else 0
        return np.where(terr,f,ff)
    e=fill(e); sh=fill(sh)
    ds=lambda f: cv2.resize(f.astype(np.float32),(S,S),interpolation=cv2.INTER_AREA)
    return dict(L=ds(L),e=ds(e),sh=ds(sh),road=ds(road),bld=ds(bld),lava=ds(void))

def nblur(f,w,sig):
    k=4; h,wd=f.shape[:2]
    fs=cv2.resize(f*(w[...,None] if f.ndim==3 else w),(wd//k,h//k),interpolation=cv2.INTER_AREA)
    ws=cv2.resize(w,(wd//k,h//k),interpolation=cv2.INTER_AREA)
    num=cv2.GaussianBlur(fs,(0,0),sig/k); den=cv2.GaussianBlur(ws,(0,0),sig/k)
    # widen support far away
    num2=cv2.GaussianBlur(fs,(0,0),sig*3/k); den2=cv2.GaussianBlur(ws,(0,0),sig*3/k)
    t=np.clip(den/0.05,0,1)
    if f.ndim==3: t=t[...,None]; d1=den[...,None]; d2=den2[...,None]
    else: d1=den; d2=den2
    out=t*num/np.maximum(d1,1e-6)+(1-t)*num2/np.maximum(d2,1e-6)
    return cv2.resize(out,(wd,h),interpolation=cv2.INTER_LINEAR)

def build_fields(c, P=P, seed=1):
    """returns dict of fields on the patch canvas"""
    x0,y0,x1,y1=c['ext']; W=int(round((x1-x0)*P)); H=int(round((y1-y0)*P))
    acc={k:np.zeros((H,W),np.float32) for k in ['w','L','e','sh','road','bld','lava']}
    col=np.zeros((H,W,9),np.float32)
    Sx=int(round(S*P/400)); ov=Sx-P
    t=np.arange(Sx,dtype=np.float32)+0.5
    for ti,(p,cx,cy,name,bio) in enumerate(c.get('tiles',[])):
        f=tile_fields(p)
        isle=(cx!=int(cx)) or (cy!=int(cy))
        ramp=sstep(np.minimum(t,Sx-t)/(ov*(2.2 if isle else 1)),0,1)
        wn=fbm2(Sx,Sx,0.16*P,4,seed*100+ti)
        wt=np.outer(ramp,ramp)*np.exp(2.2*wn)+1e-5
        px=int(round((cx-M-x0)*P)); py=int(round((cy-M-y0)*P))
        sl=(slice(py,py+Sx),slice(px,px+Sx))
        if p=='mm8/out04': f['L']=np.where(f['lava']>0.5,-1,f['L'])
        else: f['lava']=f['lava']*0
        for k in ['L','e','sh','road','bld','lava']:
            ff=f[k] if Sx==S else cv2.resize(f[k],(Sx,Sx),interpolation=cv2.INTER_AREA)
            acc[k][sl]+=wt*ff
        acc['w'][sl]+=wt
        col[sl]+=wt[...,None]*np.array(B[bio],np.float32).reshape(9)
    w=acc['w']; has=w>1e-3
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32); cxs=xx/P+x0; cys=yy/P+y0
    n1=fbm2(H,W,0.55*P,6,seed); n2=fbm2(H,W,0.22*P,5,seed+50)
    ridge=1-np.abs(fbm2(H,W,0.4*P,5,seed+9)); ridge=np.clip((ridge-0.55)/0.45,0,1)**1.5
    if has.any():
        d=ndi.distance_transform_edt(~has).astype(np.float32)/P
        core=w>0.04
        _,idx=ndi.distance_transform_edt(~core,return_indices=True)
        wm=np.maximum(w,1e-5)
        Ls=cv2.GaussianBlur(acc['L']/wm,(0,0),0.05*P)
        Lb=cv2.GaussianBlur(Ls[idx[0],idx[1]],(0,0),0.03*P)
        eb=cv2.GaussianBlur((acc['e']/wm)[idx[0],idx[1]],(0,0),0.12*P)
        cb=(col/wm[...,None])[idx[0],idx[1]]
        cb=cv2.resize(cv2.GaussianBlur(cv2.resize(cb,(W//4,H//4),interpolation=cv2.INTER_AREA),(0,0),0.1*P/4),(W,H))
        Lbg=1.05*Lb+0.55*n1+0.3*n2-2.2*d-8*np.maximum(d-0.62,0)
    else:
        d=np.full((H,W),9,np.float32); Lbg=np.full((H,W),-3,np.float32); eb=np.zeros((H,W),np.float32); cb=np.zeros((H,W,9),np.float32)+np.array(B['grass'],np.float32).reshape(9)
    for (bx,by,br,bio) in c.get('blobs',[]):
        dd=np.hypot(cxs-bx,cys-by)/br
        nb=fbm2(H,W,max(8,br*0.9*P),5,seed+int(bx*100+by*10)%97+200)
        bl=1.05*(1-dd*dd)+1.0*nb+0.3*n2
        bl=bl-6*np.maximum(dd-1.25,0)
        m=sstep(bl-np.maximum(Lbg,-0.5),-0.3,0.3)*sstep(bl,-0.5,0.1)
        cb=cb*(1-m[...,None])+m[...,None]*np.array(B[bio],np.float32).reshape(9)
        Lbg=np.maximum(Lbg,bl)
    ebg=np.clip(0.55*eb+0.75*ridge*(0.4+0.6*eb)+0.12*n2+0.08,0,1.1)
    dx=np.roll(ebg,-3,1)-np.roll(ebg,3,1); dy=np.roll(ebg,-3,0)-np.roll(ebg,3,0)
    shbg=np.clip(1+2.2*(dx+dy),0.6,1.45)
    eps=0.03
    F={}
    den=w+eps
    F['L']=(acc['L']+eps*np.clip(Lbg,-1.2,1.2))/den
    F['e']=(acc['e']+eps*ebg)/den
    F['sh']=(acc['sh']+eps*shbg)/den
    for k in ['road','bld','lava']: F[k]=acc[k]/den
    cc=(col+eps*cb)/den[...,None]
    k4=4; small=cv2.resize(cc,(W//k4,H//k4),interpolation=cv2.INTER_AREA)
    small=cv2.GaussianBlur(small,(0,0),0.11*P/k4)
    cc=cv2.resize(small,(W,H),interpolation=cv2.INTER_CUBIC)
    wx=fbm2(H,W,0.3*P,5,seed+31)*0.2*P; wy=fbm2(H,W,0.3*P,5,seed+32)*0.2*P
    F['col']=cv2.remap(cc,(xx+wx).astype(np.float32),(yy+wy).astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
    F['L']=cv2.GaussianBlur(F['L'],(0,0),2.2*P/400)
    for k in ['e','sh']: F[k]=cv2.GaussianBlur(F[k],(0,0),1.5*P/400)
    F['road']=cv2.GaussianBlur(F['road'],(0,0),0.8*P/400); F['bld']=cv2.GaussianBlur(F['bld'],(0,0),0.9*P/400)
    F['lava']=cv2.GaussianBlur(F['lava'],(0,0),2.0*P/400)
    F['P']=P; F['seed']=seed
    return F

def style(F):
    P_=F['P']; k=P_/400
    L=F['L']; H,W=L.shape
    lava=sstep(F['lava'],0.4,0.6)
    land=sstep(L,-0.07,0.07)*(1-lava)
    e=np.clip(F['e'],0,1.2)
    c=F['col']; lo,mi,hi=c[...,0:3],c[...,3:6],c[...,6:9]
    t1=np.clip(e/0.5,0,1)[...,None]; t2=np.clip((e-0.5)/0.5,0,1)[...,None]
    col=lo*(1-t1)+mi*t1; col=col*(1-t2)+hi*t2
    sh=np.clip(F['sh'],0.5,1.6)**0.9
    grain=1+0.05*fbm2(H,W,6*k+2,3,F['seed']+3)+0.04*fbm2(H,W,40*k,3,F['seed']+4)
    col=col*(sh*grain)[...,None]
    rd=np.clip(F['road']*1.3,0,0.6)[...,None]; col=col*(1-rd)+rd*(col*0.55+np.array([40,28,14],np.float32))
    bd=np.clip(F['bld']*1.6,0,0.85)[...,None]
    bn=fbm2(H,W,5*k+1.5,2,F['seed']+8)[...,None]
    bcol=np.where(bn>0,np.array([232,220,196],np.float32),np.array([186,96,72],np.float32))
    col=col*(1-bd)+bd*bcol
    lm=land>0.5
    din=ndi.distance_transform_edt(lm).astype(np.float32)/k
    dout=ndi.distance_transform_edt(~lm).astype(np.float32)/k
    beach=(sstep(din,4.0,0.5)*0.5)[...,None]
    sand=0.45*lo+0.55*np.array([232,216,170],np.float32)
    col=col*(1-beach)+beach*sand
    # water
    tw=np.exp(-dout/9.0)[...,None]
    wcol=np.array([34,112,158],np.float32)*(1-tw)+np.array([120,208,204],np.float32)*tw
    foam=sstep(dout,2.2,0.3)[...,None]*0.5
    wcol=wcol*(1-foam)+foam*np.array([226,244,240],np.float32)
    walpha=np.clip(0.92*np.exp(-dout/26.0),0,1)
    # lava
    ln=fbm2(H,W,26*k,4,F['seed']+11); ln2=fbm2(H,W,7*k+2,3,F['seed']+12)
    lt=np.clip(0.42+0.8*ln+0.35*ln2,0,1)[...,None]
    lcol=np.array([60,20,16],np.float32)*(1-lt)+np.array([255,140,30],np.float32)*lt
    lcol=lcol+(np.array([255,220,120],np.float32)-lcol)*sstep(lt,0.82,1.0)
    lz=sstep(cv2.GaussianBlur(F['lava'],(0,0),5*k),0.03,0.25)[...,None]
    wcol=wcol*(1-lz)+lz*np.array([70,24,16],np.float32)
    rgb=wcol*(1-land[...,None])+col*land[...,None]
    rgb=rgb*(1-lava[...,None])+lcol*lava[...,None]
    alpha=np.maximum(np.maximum(land,lava),walpha*(1-lava))
    return np.clip(rgb,0,255), alpha.astype(np.float32)

# ---------------- projection helpers
def local_to_lonlat(c,x,y):
    lat=c['lat0']-(y-c['yc'])*CELL
    lon=c['lon0']+(x-c['xc'])*CELL/np.maximum(np.cos(np.radians(lat)),0.05)
    return lon,lat
def lonlat_to_local(c,lon,lat):
    dl=(lon-c['lon0']+180)%360-180
    x=c['xc']+dl*np.cos(np.radians(lat))/CELL; y=c['yc']+(c['lat0']-lat)/CELL
    return x,y,dl

# ---------------- base ocean
BW,BH=4096,2048
def base_ocean():
    lon=(np.arange(BW,dtype=np.float32)+0.5)/BW*360-180; lat=90-(np.arange(BH,dtype=np.float32)+0.5)/BH*180
    lo,la=np.meshgrid(np.radians(lon),np.radians(lat))
    x=np.cos(la)*np.sin(lo); y=np.sin(la); z=np.cos(la)*np.cos(lo)
    n=fbm3(x,y,z,2.2,6,3); n2=fbm3(x,y,z,9,4,40); n3=fbm3(x,y,z,40,3,77)
    t=np.clip(0.5+0.9*n+0.25*n2,0,1)[...,None]
    deep=np.array([13,38,84],np.float32); mid=np.array([27,74,128],np.float32)
    col=deep*(1-t)+mid*t
    col*= (1+0.05*n3)[...,None]
    al=np.abs(np.degrees(la))
    cold=sstep(al,40,75)[...,None]; col=col*(1-cold)+cold*(col*0.75+np.array([40,58,74],np.float32))
    edge=77-6*n-3*n2-1.5*n3
    ice=sstep(al-edge,-0.3,0.5)
    floe=sstep(al-edge,-6,-0.5)*sstep(n3+0.6*n2,0.25,0.4)*0.85
    halo=sstep(al-edge,-5,0)[...,None]*0.35
    col=col*(1-halo)+halo*np.array([110,170,200],np.float32)
    icec=np.array([236,243,250],np.float32)*(0.9+0.1*fbm3(x,y,z,25,4,91))[...,None]
    icec=icec-np.array([26,16,6],np.float32)*sstep(n2,0.0,0.6)[...,None]
    a=np.maximum(ice,floe)[...,None]
    return col*(1-a)+icec*a

def warp_into_base(base,c,rgb,alpha,P_):
    # downsample patch to base density
    tgt=BW/360*CELL  # px per cell in base at equator
    f=min(1.0,tgt*1.15/P_)
    if f<1:
        nw,nh=int(rgb.shape[1]*f),int(rgb.shape[0]*f)
        pm=cv2.resize(rgb*alpha[...,None],(nw,nh),interpolation=cv2.INTER_AREA); al=cv2.resize(alpha,(nw,nh),interpolation=cv2.INTER_AREA)
    else: pm=rgb*alpha[...,None]; al=alpha; f=1.0
    x0,y0,x1,y1=c['ext']
    lon=(np.arange(BW,dtype=np.float32)+0.5)/BW*360-180; lat=90-(np.arange(BH,dtype=np.float32)+0.5)/BH*180
    lo,la=np.meshgrid(lon,lat)
    x,y,dl=lonlat_to_local(c,lo,la)
    mx=((x-x0)*P_*f-0.5).astype(np.float32); my=((y-y0)*P_*f-0.5).astype(np.float32)
    bad=(np.abs(dl)>100)
    mx[bad]=-10
    wp=cv2.remap(pm,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    wa=cv2.remap(al,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    return base*(1-wa[...,None])+wp

def sample_base(base,c,P_):
    x0,y0,x1,y1=c['ext']; W=int(round((x1-x0)*P_)); H=int(round((y1-y0)*P_))
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    lon,lat=local_to_lonlat(c,(xx+0.5)/P_+x0,(yy+0.5)/P_+y0)
    mx=((lon+180)%360)/360*BW-0.5; my=(90-lat)/180*BH-0.5
    return cv2.remap(base,mx.astype(np.float32),my.astype(np.float32),cv2.INTER_CUBIC,borderMode=cv2.BORDER_WRAP)

if __name__=='__main__':
    os.makedirs(f'{OUT}/img',exist_ok=True); os.makedirs(f'{OUT}/maps',exist_ok=True)
    base=base_ocean(); print('ocean done')
    for i,(lon,lat,blobs) in enumerate(ISLES):
        c={'lon0':lon,'lat0':lat,'xc':0,'yc':0,'ext':(-1.6,-1.6,1.6,1.6),'blobs':blobs}
        F=build_fields(c,P=180,seed=100+i); rgb,al=style(F)
        base=warp_into_base(base,c,rgb,al,180)
    print('isles done')
    ocean_isles=base.copy()
    meta={'cell':CELL,'continents':[],'regions':[]}
    for ci,(key,c) in enumerate(CONT.items()):
        F=build_fields(c,seed=10+ci); rgb,al=style(F)
        base=warp_into_base(base,c,rgb,al,P)
        bg=sample_base(ocean_isles,c,P)
        fin=bg*(1-al[...,None])+rgb*al[...,None]
        Image.fromarray(np.clip(fin,0,255).astype(np.uint8)).save(f'{OUT}/img/{key}.webp',quality=90,method=5)
        meta['continents'].append({'key':key,'title':c['title'],'lon0':c['lon0'],'lat0':c['lat0'],'xc':c['xc'],'yc':c['yc'],'ext':c['ext'],'img':f'img/{key}.webp'})
        for (p,cx,cy,name,bio) in c['tiles']:
            meta['regions'].append({'id':p.replace('/','-'),'game':p[:3],'name':name,'c':ci,'rect':[cx,cy,cx+1,cy+1],'img':f'maps/{p.replace("/","-")}.webp'})
        print(key,'done',fin.shape)
    Image.fromarray(np.clip(base,0,255).astype(np.uint8)).save(f'{OUT}/img/world.webp',quality=88,method=5)
    for f in sorted(glob.glob(f'{R}/maps/*/*.png')):
        g=f.split('/')[-2]; nm=os.path.basename(f); stem=nm.split('.')[0]
        im=Image.open(f).convert('RGB')
        if nm.endswith('.odm.png'): im=im.crop((24,24,1500,1500))
        im.save(f'{OUT}/maps/{g}-{stem}.webp',lossless=True,method=6)
    # paste this into the META constant in index.html if the layout changed
    print(json.dumps(meta,separators=(',',':')))
