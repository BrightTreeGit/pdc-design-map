exec(open('tmatch.py').read().split('mov,tgt=sys.argv')[0])
import itertools
targets=['wide_1979_421488','wide_1981_496095','wide_1988_576368','wide_1997_369968','ref_1994']
movs=['wide_1953_275096','wide_1954_297574','wide_1958_164570','wide_1961_340260','wide_1967_154507','wide_1971_162878','wide_1975_637834','wide_1977_824352','wide_1986_379496','wide_1995_719593','wide_1992_133369']
for m in movs:
    out=[]
    for t in targets:
        Hf,mx,s,a=find(m,t); c=Hf@np.array([2000,2000,1.]); out.append((round(mx,3),t[5:9],s,a,tuple(np.round((c[:2]/c[2]-2000)*1.25))))
    print(m[5:9],sorted(out,reverse=True)[:3])
