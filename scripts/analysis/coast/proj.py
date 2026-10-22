import math
def ll2mga(lon,lat,zone=56):
    a=6378137;f=1/298.257222101;k0=.9996;n=f/(2-f);A=a/(1+n)*(1+n*n/4+n**4/64);e=math.sqrt(f*(2-f))
    al=[n/2-2*n*n/3+5*n**3/16,13*n*n/48-3*n**3/5,61*n**3/240]
    phi=math.radians(lat);lam=math.radians(lon-(zone*6-183))
    t=math.sinh(math.atanh(math.sin(phi))-e*math.atanh(e*math.sin(phi)))
    xp=math.atan2(t,math.cos(lam));ep=math.atanh(math.sin(lam)/math.sqrt(1+t*t))
    x=xp+sum(al[j]*math.sin(2*(j+1)*xp)*math.cosh(2*(j+1)*ep) for j in range(3))
    y=ep+sum(al[j]*math.cos(2*(j+1)*xp)*math.sinh(2*(j+1)*ep) for j in range(3))
    return 5e5+k0*A*y,1e7+k0*A*x
if __name__=='__main__':
    print(ll2mga(152.92670365,-26.74517648))  # lot corner check ~ (492710.6, 7041791)
