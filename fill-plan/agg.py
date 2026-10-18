import pickle,glob,collections,json
out={}
for L in ['zh','yue','ko','en','classical']:
    df=collections.Counter(); tok=collections.Counter(); pages=0; nb=0; files=sorted(glob.glob(f'data/d_{L}*.pkl'))
    for f in files:
        d=pickle.load(open(f,'rb')); df+=d['df']; tok+=d['tok']; pages+=d['pages']; nb+=d['bytes']
    out[L]=dict(df={ord(k):v for k,v in df.items()},tok={ord(k):v for k,v in tok.items()},pages=pages,bytes=nb,files=len(files))
    print(L,len(files),'pages',pages,'MB',nb//10**6,'distinct uncovered',len(df))
pickle.dump(out,open('data/agg.pkl','wb'))
