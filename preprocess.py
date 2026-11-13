import pandas as pd, numpy as np
rd=lambda f:pd.read_csv(f,encoding='cp949')
pop=rd('data_10775239.csv'); t=rd('data_10775475.csv'); s=rd('data_10775241.csv')
pop['구']=pop['행정구역'].str.extract(r'부산광역시\s+(\S+)\s*\(')
pop=pop.dropna(subset=['구'])
m='2026년10월_계_'
pop['총인구']=pop[m+'총인구수'].astype(str).str.replace(',','').astype(float)
old=['60~69세','70~79세','80~89세','90~99세','100세 이상']
pop['고령60+']=sum(pop[m+c].astype(str).str.replace(',','').astype(float) for c in old)
pop['고령비율']=pop['고령60+']/pop['총인구']*100
pop=pop[['구','총인구','고령60+','고령비율']]
s['구']=s['상세주소'].str.split().str[1]
sc=s.groupby('구').size().rename('쉼터수').reset_index()
t.columns=['지점','지점명','일시','기온']; t['기온']=pd.to_numeric(t['기온'],errors='coerce')
t=t[t.일시.str[5:7].isin(['06','07','08','09'])]
mp={'가덕도':'강서구','금정구':'금정구','기장':'기장군','동래':'동래구','부산(레)':'중구','부산남구':'남구','부산진':'부산진구','북구':'북구','사상':'사상구','사하':'사하구','영도':'영도구','해운대':'해운대구'}
sub={'서구':'중구','동구':'부산진구','연제구':'동래구','수영구':'남구'}  # 대체 관측소(가정)
st=t.groupby('지점명')['기온'].agg(최고기온='max',평균기온='mean',h33=lambda x:(x>=33).sum(),h30=lambda x:(x>=30).sum())
rows=[]
for g in pop['구']:
    name=next((k for k,v in mp.items() if v==g),None); est=False
    if name is None:
        name=next(k for k,v in mp.items() if v==sub[g]) ; est=True
    r=st.loc[name].to_dict(); r.update(구=g,기온관측소=name,대체관측=est); rows.append(r)
d=pop.merge(sc,on='구').merge(pd.DataFrame(rows),on='구')
d['쉼터_고령1천명당']=d['쉼터수']/d['고령60+']*1000
z=lambda x:(x-x.min())/(x.max()-x.min())
d['취약도']=(0.4*z(d.h33)+0.3*z(d['고령60+'])+0.3*(1-z(d['쉼터_고령1천명당'])))*100
d=d.sort_values('취약도',ascending=False).round(2)
d.to_csv('/home/user/output/district_summary.csv',index=False,encoding='utf-8-sig')
s[['쉼터명','구','x좌표','y좌표']].rename(columns={'x좌표':'경도','y좌표':'위도'}).to_csv('/home/user/output/shelters.csv',index=False,encoding='utf-8-sig')
print(d[['구','고령60+','고령비율','쉼터수','쉼터_고령1천명당','h33','대체관측','취약도']].to_string())
