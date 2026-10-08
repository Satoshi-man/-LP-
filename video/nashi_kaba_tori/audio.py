import numpy as np, wave, json
sr=44100; FPS=30
# (id, file, speaker, gap_before)
SEQ=[('n1','n1','n',0.3),('n2','n2','n',0.15),('h1a','h1a','h',0.2),('h1b','h1b','h',0.03),('h1c','h1c','h',0.03),('h1d','h1d','h',0.1),
     ('h2','h2f','h',0.15),('n3','n3f','n',0.2),('n4','n4f','n',0.12),('n5','n5','n',0.15),
     ('b1a','b1a','b',0.35),('b1b','b1b','b',0.05),('b1c','b1c','b',0.03),('all','ALL','x',0.3)]
def rd(p):
    with wave.open(p) as w: return np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float)/32768
tr={}; t=0; cues={}
for cid,f,spk,gap in SEQ:
    t+=gap
    if f=='ALL':
        parts={k:rd(f'vt/all_{k}s.wav') for k in 'nhb'}; L=max(len(a) for a in parts.values())
        for k,a in parts.items(): tr.setdefault(k,[]).append((t,a/np.max(np.abs(a))*0.75))
    else:
        a=rd(f'vt/{f}.wav'); a=a/np.max(np.abs(a))*0.9; L=len(a); tr.setdefault(spk,[]).append((t,a))
    cues[cid]=[round(t,3),round(t+L/sr,3)]; t+=L/sr
END=t; DUR=round(END+3.2,1); n=int(DUR*sr); nf=int(DUR*FPS); hop=sr//FPS
voice=np.zeros(n); mouth={}
for k,lst in tr.items():
    x=np.zeros(n)
    for st,a in lst: i=int(st*sr); x[i:i+len(a)]+=a[:n-i]
    voice+=x
    env=np.array([np.sqrt(np.mean(x[f*hop:(f+1)*hop]**2)) for f in range(nf)])
    ref=np.percentile(env[env>0.01],90) if (env>0.01).any() else 1
    env=np.convolve(np.clip(env/ref,0,1),[0.25,0.5,0.25],'same'); mouth[k]=[round(float(v),3) for v in env]
open('env.js','w').write('window.ENV='+json.dumps({'mouth':mouth,'cues':cues,'dur':DUR})+';')
print(json.dumps(cues),DUR)
# BGM: bouncy comedic, key F
def note(m): return 440*2**((m-69)/12)
bgm=np.zeros(n); beat=60/132
prog=[[65,69,72],[70,74,77],[72,76,79],[65,69,72]]; bass=[41,46,48,41]
rng=np.random.default_rng(5)
for bar in range(int(DUR/(4*beat))+1):
    st=bar*4*beat; ch=prog[bar%4]
    for k in range(4):
        s0=int((st+k*beat)*sr)
        if s0>=n: break
        if k%2==0:
            m=bass[bar%4]+(0 if k==0 else 7); l=min(n-s0,int(0.3*sr)); tt=np.arange(l)/sr
            bgm[s0:s0+l]+=0.22*(np.sin(2*np.pi*note(m)*tt)+0.5*np.sin(4*np.pi*note(m)*tt)+0.25*np.sin(6*np.pi*note(m)*tt))*np.minimum(1,tt/0.01)*np.exp(-tt*6)
        else:
            l=min(n-s0,int(0.18*sr)); tt=np.arange(l)/sr
            bgm[s0:s0+l]+=0.07*sum(np.sin(2*np.pi*note(x+12)*tt) for x in ch)*np.exp(-tt*18)
    for k in range(8):
        if rng.random()<0.35: continue
        s0=int((st+k*beat/2)*sr)
        if s0>=n: break
        m=ch[rng.integers(3)]+24; l=min(n-s0,int(0.2*sr)); tt=np.arange(l)/sr
        bgm[s0:s0+l]+=0.08*np.sin(2*np.pi*note(m)*tt)*np.exp(-tt*22)
vabs=np.convolve(np.abs(voice),np.ones(4410)/4410,'same'); bgm*=1-0.6*np.clip(vabs*12,0,1)
sfx=np.zeros(n)
def put(t,a):
    i=int(t*sr); a=a[:max(0,n-i)]; sfx[i:i+len(a)]+=a
def tone(f,d,dec,amp=0.3):
    tt=np.arange(int(d*sr))/sr; return amp*np.sin(2*np.pi*f*tt)*np.exp(-tt*dec)
# sparkle on nashi entrance
for i in range(14): put(0.0+i*0.05,tone(1800+i*120,0.25,14,0.07))
# boing at kaba emphasis + tori emphasis
for c in [cues['h1b'][0],cues['b1b'][0]]:
    tt=np.arange(int(0.45*sr))/sr; put(c,0.25*np.sin(2*np.pi*np.cumsum(180+260*np.sin(2*np.pi*11*tt)*np.exp(-tt*5))/sr)*np.exp(-tt*6))
# flap / whoosh as bird enters
for k in range(6):
    l=int(0.12*sr); nz=np.convolve(rng.standard_normal(l),np.ones(15)/15,'same'); put(cues['n5'][1]-0.6+k*0.13,0.3*nz*np.sin(np.linspace(0,np.pi,l)))
# coins return
for i in range(18): put(cues['b1c'][0]+i*0.06+rng.random()*0.04,tone(2200+rng.random()*2200,0.15,30,0.07))
# chord hit at chorus + end
for c in [cues['all'][0],cues['all'][1]+0.3]:
    put(c,sum(tone(note(m),1.2,2.5,0.12) for m in [65,69,72,77]))
mix=0.3*bgm/np.max(np.abs(bgm))+voice*0.95+sfx
fl=int(1.0*sr); mix[-fl:]*=np.linspace(1,0,fl)
mix=np.tanh(mix*1.1)/np.tanh(1.1)*0.92
with wave.open('mix.wav','wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(np.stack([mix,mix],1),-1,1)*32767).astype(np.int16).tobytes())
