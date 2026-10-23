import base64
b64=lambda f,m:f'data:{m};base64,'+base64.b64encode(open(f,'rb').read()).decode()
h=open('template.html').read().replace('__DATA__',open('data.json').read())
for k,f,m in [('__REL__','relief.jpg','image/jpeg'),('__HILL__','hill.jpg','image/jpeg'),('__CON__','con_a.png','image/png'),('__PACK__','pack.png','image/png')]: h=h.replace(k,b64(f,m))
open('/tmp/claude-0/-home-claude/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/scratchpad/bright-tree-water.html','w').write(h);print(len(h)//1024,'KB')
