import numpy as np, wave
sr=44100; D=26; n=sr*D; out=np.zeros(n)
bpm=120; beat=60/bpm
def note(f): return 440*2**((f-69)/12)
t_all=np.arange(n)/sr
# chords I-V-vi-IV in D major, 2 bars(4 beats) each
prog=[[62,66,69],[57,61,64],[59,62,66],[55,59,62]]
bass=[38,33,35,31]
for bar in range(int(D/(4*beat))+1):
    st=bar*4*beat; ch=prog[bar%4]
    i0=int(st*sr); L=int(4*beat*sr); i1=min(n,i0+L)
    if i0>=n: break
    tt=np.arange(i1-i0)/sr
    env=np.minimum(1,tt/0.08)*np.exp(-tt*0.35)
    pad=sum(np.sin(2*np.pi*note(m)*tt)+0.3*np.sin(2*np.pi*note(m)*2*tt) for m in ch)
    out[i0:i1]+=0.035*pad*env
    # pluck arpeggio 8ths
    for k in range(8):
        s0=int((st+k*beat/2)*sr); 
        if s0>=n: break
        m=ch[[0,1,2,1,0,2,1,2][k]]+12; l=min(n-s0,int(0.4*sr)); tt2=np.arange(l)/sr
        out[s0:s0+l]+=0.06*np.sign(np.sin(2*np.pi*note(m)*tt2))*0.3*np.exp(-tt2*12)+0.06*np.sin(2*np.pi*note(m)*tt2)*np.exp(-tt2*8)
    # bass on beats
    for k in range(4):
        s0=int((st+k*beat)*sr)
        if s0>=n: break
        l=min(n-s0,int(0.45*sr)); tt2=np.arange(l)/sr
        out[s0:s0+l]+=0.12*np.sin(2*np.pi*note(bass[bar%4])*tt2)*np.exp(-tt2*5)
for b in range(int(D/beat)):
    s0=int(b*beat*sr); l=min(n-s0,int(0.25*sr)); tt=np.arange(l)/sr
    f=50+90*np.exp(-tt*30); out[s0:s0+l]+=0.28*np.sin(2*np.pi*np.cumsum(f)/sr)*np.exp(-tt*14)
    s1=int((b+0.5)*beat*sr); l=min(n-s1,int(0.05*sr))
    if l>0: out[s1:s1+l]+=0.03*np.random.randn(l)*np.exp(-np.arange(l)/sr*80)
# whoosh + pop at scene changes
rng=np.random.default_rng(1)
for c in [3.6,7.9,12.1,16.9,20.6]:
    s0=int((c-0.3)*sr); l=int(0.5*sr); nz=rng.standard_normal(l); nz=np.convolve(nz,np.ones(30)/30,'same')
    env=np.sin(np.linspace(0,np.pi,l))**2; out[s0:s0+l]+=0.5*nz*env
for c in [2.3,13.3,18.3,24.0]:  # stamp hits
    s0=int(c*sr); l=int(0.2*sr); tt=np.arange(l)/sr
    out[s0:s0+l]+=0.3*np.sin(2*np.pi*(120+400*np.exp(-tt*40))*tt)*np.exp(-tt*20)
for c in [20.95,21.1,21.25,21.45,21.6,21.75]:  # digit pops
    s0=int(c*sr); l=int(0.12*sr); tt=np.arange(l)/sr
    out[s0:s0+l]+=0.12*np.sin(2*np.pi*(900+600*tt*8)*tt)*np.exp(-tt*35)
fade=np.ones(n); fl=int(1.2*sr); fade[-fl:]=np.linspace(1,0,fl); out*=fade
out=out/np.max(np.abs(out))*0.85
st=np.stack([out,out],1)
with wave.open('bgm.wav','wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((st*32767).astype(np.int16).tobytes())
