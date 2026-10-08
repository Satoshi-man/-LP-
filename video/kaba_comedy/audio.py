import numpy as np, wave, json
sr=44100; DUR=29.5; n=int(sr*DUR); FPS=30
CUES=[('h1',0.4),('n1',4.5),('h2',10.3),('h3',14.6),('n2',17.1),('h4',22.1),('n3',24.8)]
def rd(p):
    with wave.open(p) as w: a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float)/32768
    return a
voice=np.zeros(n); hip=np.zeros(n); cues={}
for k,t in CUES:
    a=rd(f'vt/{k}.wav'); a=a/np.max(np.abs(a))*0.9; i=int(t*sr); a=a[:n-i]
    voice[i:i+len(a)]+=a; cues[k]=[t,t+len(a)/sr]
    if k.startswith('h'): hip[i:i+len(a)]+=a
# mouth envelope per frame
nf=int(DUR*FPS); hop=sr//FPS; env=[]
for f in range(nf):
    seg=hip[f*hop:(f+1)*hop]; env.append(float(np.sqrt(np.mean(seg**2))) if len(seg) else 0)
env=np.array(env); env=np.clip(env/ (np.percentile(env[env>0.01],90) if (env>0.01).any() else 1),0,1)
env=np.convolve(env,[0.25,0.5,0.25],'same')
json.dump({'mouth':[round(x,3) for x in env],'cues':cues},open('env.json','w'))
open('env.js','w').write('window.ENV='+json.dumps({'mouth':[round(x,3) for x in env],'cues':cues})+';')
# --- BGM: bouncy comedic
def note(m): return 440*2**((m-69)/12)
bgm=np.zeros(n); bpm=128; beat=60/bpm
prog=[[60,64,67],[65,69,72],[67,71,74],[60,64,67]]; bass=[36,41,43,36]
rng=np.random.default_rng(3)
for bar in range(int(DUR/(4*beat))+1):
    st=bar*4*beat; ch=prog[bar%4]
    for k in range(4):
        # tuba-ish bass on 1,3 ; chord stabs on 2,4
        s0=int((st+k*beat)*sr)
        if s0>=n: break
        if k%2==0:
            m=bass[bar%4]+(0 if k==0 else 7); l=min(n-s0,int(0.32*sr)); tt=np.arange(l)/sr
            w=np.sin(2*np.pi*note(m)*tt)+0.5*np.sin(4*np.pi*note(m)*tt)+0.25*np.sin(6*np.pi*note(m)*tt)
            bgm[s0:s0+l]+=0.22*w*np.minimum(1,tt/0.01)*np.exp(-tt*6)
        else:
            l=min(n-s0,int(0.18*sr)); tt=np.arange(l)/sr
            bgm[s0:s0+l]+=0.07*sum(np.sin(2*np.pi*note(x+12)*tt) for x in ch)*np.exp(-tt*18)
    # pizzicato melody (random from chord tones)
    for k in range(8):
        if rng.random()<0.35: continue
        s0=int((st+k*beat/2)*sr)
        if s0>=n: break
        m=ch[rng.integers(3)]+24; l=min(n-s0,int(0.2*sr)); tt=np.arange(l)/sr
        bgm[s0:s0+l]+=0.08*np.sin(2*np.pi*note(m)*tt)*np.exp(-tt*22)
# sleep section: quieter
gain=np.ones(n)
def ramp(a,b,v0,v1):
    i0,i1=int(a*sr),int(b*sr); gain[i0:i1]=np.linspace(v0,v1,i1-i0)
ramp(11.6,12.0,1,0.15); gain[int(12.0*sr):int(14.2*sr)]=0.15; ramp(14.2,14.4,0.15,1)
bgm*=gain
# duck under voice
vabs=np.convolve(np.abs(voice),np.ones(4410)/4410,'same'); duck=1-0.55*np.clip(vabs*12,0,1)
bgm*=duck
sfx=np.zeros(n)
def put(t,a):
    i=int(t*sr); a=a[:n-i]; sfx[i:i+len(a)]+=a
def tone(f,d,dec,amp=0.3):
    tt=np.arange(int(d*sr))/sr; return amp*np.sin(2*np.pi*f*tt)*np.exp(-tt*dec)
# snoring Zzz (low noise swells)
for t in [12.1,13.0]:
    l=int(0.7*sr); tt=np.arange(l)/sr; nz=np.convolve(rng.standard_normal(l),np.ones(60)/60,'same')
    put(t,0.6*nz*np.sin(np.pi*tt/0.7)**2*(1+0.5*np.sin(2*np.pi*30*tt)))
# doorbell ピンポーン
put(13.4,tone(659.25*2,0.6,4,0.35)+0.0); put(13.85,tone(523.25*2,1.0,3,0.35))
# eye pop boing
tt=np.arange(int(0.4*sr))/sr; put(14.45,0.3*np.sin(2*np.pi*np.cumsum(200+300*np.sin(2*np.pi*12*tt)*np.exp(-tt*5))/sr)*np.exp(-tt*6))
# coin jingles
for i in range(28):
    put(14.5+i*0.09+rng.random()*0.05, tone(2000+rng.random()*2500,0.15,30,0.08))
# whooshes at scene changes
for c in [4.4,10.2,17.0,24.6]:
    l=int(0.45*sr); nz=np.convolve(rng.standard_normal(l),np.ones(25)/25,'same'); put(c-0.25,0.35*nz*np.sin(np.linspace(0,np.pi,l))**2)
# end jingle hits on digits
for i,c in enumerate([24.9,25.05,25.2,25.4,25.55,25.7]):
    put(c,tone(880*2**(i/12*2),0.15,25,0.1))
mix=0.32*bgm/np.max(np.abs(bgm))+voice*0.95+sfx
fade=np.ones(n); fl=int(1.0*sr); fade[-fl:]=np.linspace(1,0,fl); mix*=fade
mix=np.tanh(mix*1.1)/np.tanh(1.1)*0.92
st=np.stack([mix,mix],1)
with wave.open('mix.wav','wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(st,-1,1)*32767).astype(np.int16).tobytes())
print(cues)
