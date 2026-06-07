#!/usr/bin/env python3
"""
Geolocalización de las inmatriculaciones de la CEE — cascada completa.

Niveles de precisión (de menor a mayor; SIEMPRE se intenta subir):
  1. Centroide municipal (padrón INE)        -> fuente: centroide_municipio_INE
  2. Punto de entidad sub-municipal           -> fuente: punto_entidad_poblacion
  3. EDIFICIO concreto vía OSM/Overpass        -> fuente: edificio_osm
     (place_of_worship dentro del recinto admin_level=8, casado por advocación)

La etapa 3 NO es opcional: se ejecuta siempre que haya red. Lo único graduado es
si una coincidencia se AUTO-ACEPTA o se deja como CANDIDATO a confirmar:
  - auto-acepta solo si el match depende de un token que es ÚNICO entre los
    templos de ese municipio (discriminante real, no un patrón compartido).
  - en otro caso se conserva la coord. previa y se anota el candidato OSM.

Nunca se inventa una coordenada: lo no resuelto se marca 'sin_resolver'.

Fuentes cacheadas en ./geo_cache/ (padrón) y ./overpass_cache/ (templos por muni).
En producción, sustituir el padrón Wikidata por el Nomenclátor INE.
"""
from __future__ import annotations
import argparse, glob, json, os, re, sys, time, math
from collections import defaultdict, Counter

WD = "https://query.wikidata.org/sparql"
OVERPASS = "https://overpass-api.de/api/interpreter"
UA = {"User-Agent": "sipi-geoloc/1.1 (research)"}

# ---------- normalización ----------
ARTS = ("A ", "O ", "EL ", "LA ", "LES ", "ELS ", "LOS ", "LAS ", "L ")
CONN = {"DE","DEL","DA","DO","DOS","DAS","LA","LAS","LOS","LES","ELS","EL","LO","I","Y","E"}
ABBR = [(r"\bGC\b","GRAN CANARIA"), (r"\bSTA\b","SANTA"), (r"\bSTO\b","SANTO")]
# palabras de "tipo de edificio" y genéricos que NO discriminan una advocación
BUILD = {"IGLESIA","IGREXA","IGREJA","ESGLESIA","ESGLÉSIA","CAPELA","CAPILLA","CAPELLA","TEMPLO",
 "ERMITA","ERMIDA","SANTUARIO","BASILICA","CATEDRAL","CONVENTO","MONASTERIO","PARROQUIA","PARROQUIAL",
 "PARROQUIAS","COMPLEJO","DE","DEL","DA","DO","DOS","DAS","LA","EL","LOS","LAS","Y","E","I","A","O",
 "NOSA","SENORA","SEÑORA","NUESTRA","SAN","SANTA","SANTO","SANT","SANTOS","NTRA","STA","STO","VIRGEN",
 "CRISTO","DEPENDENCIAS","COMPLEMENTARIAS"}
# 'Titular' que es PROPIETARIO institucional, no advocación
OWNER = ("ARZOBISPADO","OBISPADO","DIOCESIS","ARCHIDIOCESIS","CABILDO","ORDEN","CONGREGACION",
 "CARMELIT","FRANCISCAN","DOMINIC","COMPANIA","HERMANAS","HERMANOS","MISIONER","SALESIAN")

def norm(s):
    s = "".join(c for c in __import__("unicodedata").normalize("NFD", str(s))
                if __import__("unicodedata").category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip().upper()
def deart(s):
    for a in ARTS:
        if s.startswith(a): return s[len(a):].strip()
    return s
def skel(s): return " ".join(t for t in s.split() if t not in CONN)
def expand(s):
    for p, r in ABBR: s = re.sub(p, r, s)
    return re.sub(r"\s+", " ", s).strip()
def adv_tokens(*txts, stop=frozenset()):
    out = set()
    for t in txts:
        for w in norm(t).split():
            if len(w) > 2 and w not in BUILD and w not in stop: out.add(w)
    return out
def clean_layers(raw):
    a = expand(norm(raw))
    b = re.sub(r"\(.*?\)", " ", a); b = re.sub(r",\s*\d+.*$", "", b)
    b = re.sub(r"\s+\d+\b", "", b); b = re.sub(r"\s+", " ", b).strip()
    d = re.split(r"\s*[-;]\s*", b)[0].strip()
    c = b
    mt = re.search(r"(?:T\.?\s*M\.?\s+DE|AYUNTAMIENTO DE)\s+([A-ZÑ ]+)$", a)
    if mt: c = re.sub(r"\s+", " ", mt.group(1)).strip()
    return [a, b, c, d]
def haversine_m(a, b, c, d):
    R = 6371000; p = math.radians
    x = math.sin(p(c-a)/2)**2 + math.cos(p(a))*math.cos(p(c))*math.sin(p(d-b)/2)**2
    return 2*R*math.asin(math.sqrt(x))

PROV = {'01':['ARABA','ALAVA'],'02':['ALBACETE'],'03':['ALICANTE','ALACANT'],'04':['ALMERIA'],'05':['AVILA'],'06':['BADAJOZ'],'07':['BALEARES','ILLES BALEARS'],'08':['BARCELONA'],'09':['BURGOS'],'10':['CACERES'],'11':['CADIZ'],'12':['CASTELLON','CASTELLO'],'13':['CIUDAD REAL'],'14':['CORDOBA'],'15':['A CORUNA','LA CORUNA','CORUNA'],'16':['CUENCA'],'17':['GIRONA','GERONA'],'18':['GRANADA'],'19':['GUADALAJARA'],'20':['GIPUZKOA','GUIPUZCOA'],'21':['HUELVA'],'22':['HUESCA'],'23':['JAEN'],'24':['LEON'],'25':['LLEIDA','LERIDA'],'26':['LA RIOJA','RIOJA'],'27':['LUGO'],'28':['MADRID'],'29':['MALAGA'],'30':['MURCIA'],'31':['NAVARRA','NAFARROA'],'32':['OURENSE','ORENSE'],'33':['ASTURIAS'],'34':['PALENCIA'],'35':['LAS PALMAS','CANARIAS-LAS PALMAS'],'36':['PONTEVEDRA'],'37':['SALAMANCA'],'38':['SANTA CRUZ DE TENERIFE','TENERIFE','CANARIAS-TENERIFE'],'39':['CANTABRIA'],'40':['SEGOVIA'],'41':['SEVILLA'],'42':['SORIA'],'43':['TARRAGONA'],'44':['TERUEL'],'45':['TOLEDO'],'46':['VALENCIA'],'47':['VALLADOLID'],'48':['BIZKAIA','VIZCAYA'],'49':['ZAMORA'],'50':['ZARAGOZA'],'51':['CEUTA'],'52':['MELILLA']}
PROV2CODE = {norm(n): c for c, ns in PROV.items() for n in ns}
TIPO_IGL = ("TEMPLO","IGLESIA","PARROQUIAL","ERMITA","SANTUARIO","CAPILLA","CATEDRAL","BASILICA","CONVENTO","MONASTERIO")

# ---------- fuentes con caché (idéntico a v1; recortado por brevedad) ----------
def _sparql(q, timeout=240):
    import requests
    r = requests.get(WD, params={"query": q, "format": "json"}, headers=UA, timeout=timeout)
    r.raise_for_status(); return r.json()["results"]["bindings"]
def cargar_padron(cache="geo_cache"):
    os.makedirs(cache, exist_ok=True)
    fm, fn, fe = (os.path.join(cache, x) for x in ("munis.json","names.json","entidades.json"))
    if not os.path.exists(fm):
        b=_sparql('SELECT ?ine ?name ?lat ?lon WHERE { ?m wdt:P31/wdt:P279* wd:Q2074737. ?m wdt:P772 ?ine. ?m p:P625/psv:P625 ?c. ?c wikibase:geoLatitude ?lat; wikibase:geoLongitude ?lon. OPTIONAL{?m rdfs:label ?name FILTER(LANG(?name)="es")} }')
        s={}; [s.setdefault(x["ine"]["value"],{"ine":x["ine"]["value"],"name":x.get("name",{}).get("value",""),"lat":float(x["lat"]["value"]),"lon":float(x["lon"]["value"])}) for x in b]
        json.dump(list(s.values()),open(fm,"w"),ensure_ascii=False)
    if not os.path.exists(fn):
        b=_sparql('SELECT ?ine ?label WHERE { ?m wdt:P772 ?ine. {?m rdfs:label ?label} UNION {?m skos:altLabel ?label} FILTER(LANG(?label) IN("es","gl","ca","eu","oc","an","ast")) }')
        nm=defaultdict(set); [nm[x["ine"]["value"]].add(x["label"]["value"]) for x in b]
        json.dump({k:sorted(v) for k,v in nm.items()},open(fn,"w"),ensure_ascii=False)
    if not os.path.exists(fe):
        b=_sparql('SELECT ?xname ?lat ?lon ?ine WHERE { ?x wdt:P31/wdt:P279* wd:Q486972. ?x wdt:P17 wd:Q29. ?x p:P625/psv:P625 ?c. ?c wikibase:geoLatitude ?lat; wikibase:geoLongitude ?lon. ?x wdt:P131 ?mu. ?mu wdt:P772 ?ine. ?x rdfs:label ?xname FILTER(LANG(?xname) IN("es","gl","ca","eu","ast","an")) }')
        json.dump([{"name":x["xname"]["value"],"lat":float(x["lat"]["value"]),"lon":float(x["lon"]["value"]),"ine":x["ine"]["value"]} for x in b],open(fe,"w"),ensure_ascii=False)
    return json.load(open(fm)), json.load(open(fn)), json.load(open(fe))

# ---------- etapas 1-2: padrón ----------
class Matcher:
    def __init__(self, munis, names, ents):
        self.coords={m["ine"]:m for m in munis}
        self.m_pc={}; self.m_pcsk=defaultdict(set); self.m_name=defaultdict(set); self.m_pn=defaultdict(set)
        for ine,m in self.coords.items():
            pc=ine[:2]
            for v in set(names.get(ine,[]))|{m["name"]}:
                for k in {norm(v),deart(norm(v))}:
                    if k: self.m_pc[(pc,k)]=m; self.m_name[k].add(ine); self.m_pcsk[(pc,skel(k))].add(ine); self.m_pn[pc].add(k)
        self.e_pc=defaultdict(list); self.e_name=defaultdict(list)
        for e in ents:
            for k in {norm(e["name"]),deart(norm(e["name"]))}:
                if k: self.e_pc[(e["ine"][:2],k)].append(e); self.e_name[k].append(e)
    def _muni(self,nm,pc):
        for k in (nm,deart(nm)):
            if pc and (pc,k) in self.m_pc: return self.m_pc[(pc,k)],"exacto","alta"
        for k in (nm,deart(nm)):
            if len(self.m_name.get(k,()))==1: return self.coords[next(iter(self.m_name[k]))],"nombre_unico","alta"
        sk=skel(deart(nm))
        if pc and len(self.m_pcsk.get((pc,sk),()))==1: return self.coords[next(iter(self.m_pcsk[(pc,sk)]))],"sin_particulas","media"
        if pc and len(nm)>=5:
            c={i for k in self.m_pn[pc] if k.startswith(nm+" ") for i in self.m_name[k]}
            if len(c)==1: return self.coords[next(iter(c))],"prefijo_prov","media"
        return None,None,None
    def _ent(self,nm,pc):
        for k in (nm,deart(nm)):
            if pc and self.e_pc.get((pc,k)): return self.e_pc[(pc,k)][0],"ent_prov","alta"
        for k in (nm,deart(nm)):
            if self.e_name.get(k): return self.e_name[k][0],"ent_nombre","media"
        return None,None,None
    def match(self,municipio,pc):
        for nm in clean_layers(municipio):
            if not nm: continue
            m,met,cf=self._muni(nm,pc)
            if m: return dict(ine=m["ine"],lat=m["lat"],lon=m["lon"],fuente_coordenadas="centroide_municipio_INE",metodo=met,confianza=cf)
        for nm in clean_layers(municipio):
            if not nm: continue
            e,met,cf=self._ent(nm,pc)
            if e: return dict(ine=e["ine"],lat=e["lat"],lon=e["lon"],fuente_coordenadas="punto_entidad_poblacion",metodo=met,confianza=cf)
        return dict(ine=None,lat=None,lon=None,fuente_coordenadas=None,metodo="sin_resolver",confianza=None)

# ---------- etapa 3: edificio OSM (obligatoria) ----------
def overpass_municipio(ine, nombre, endpoint=OVERPASS, sleep=1.0, cache="overpass_cache"):
    import requests
    os.makedirs(cache, exist_ok=True)
    fp = os.path.join(cache, f"{ine}.json")
    if os.path.exists(fp): return json.load(open(fp))
    Q=f'[out:json][timeout:60];area["admin_level"="8"]["name"="{nombre}"]->.a;(nwr["amenity"="place_of_worship"](area.a););out center tags;'
    try:
        r=requests.post(endpoint,data={"data":Q},headers=UA,timeout=120); r.raise_for_status()
        els=[]
        for e in r.json().get("elements",[]):
            t=e.get("tags",{}); lat=e.get("lat") or e.get("center",{}).get("lat"); lon=e.get("lon") or e.get("center",{}).get("lon")
            if t.get("name") and lat is not None:
                els.append({"name":t["name"],"ded":t.get("church:dedication") or t.get("dedication") or "",
                            "lat":lat,"lon":lon,"osm":f'{e["type"]}/{e["id"]}'})
        json.dump(els,open(fp,"w"),ensure_ascii=False)
        if sleep: time.sleep(sleep)
        return els
    except Exception as ex:
        print(f"  ! Overpass falló en {nombre} ({ine}): {ex}", file=sys.stderr); return None

def upgrade_osm(df, coords, endpoint=OVERPASS, sleep=1.0, only_ine=None):
    """Sube a precisión de edificio. Devuelve df con columnas osm_*."""
    for col in ("osm_id","osm_lat","osm_lon","osm_score","dist_centroide_m","osm_estado"):
        df[col]=None
    # solo inmuebles tipo-iglesia ya anclados a municipio
    mask=df["Tipo"].fillna("").map(norm).str.contains("|".join(TIPO_IGL)) & df["lat"].notna()
    inelist=sorted(df.loc[mask,"ine"].dropna().unique())
    if only_ine: inelist=[i for i in inelist if i in set(only_ine)]
    for ine in inelist:
        nombre=coords.get(ine,{}).get("name")
        if not nombre: continue
        templos=overpass_municipio(ine, nombre, endpoint=endpoint, sleep=sleep)
        if not templos: continue
        stop=adv_tokens(nombre)  # excluir el nombre del municipio como token
        for g in templos: g["toks"]=adv_tokens(g["name"],g["ded"],stop=stop)
        # frecuencia de token en el municipio -> discriminancia
        freq=Counter(t for g in templos for t in g["toks"])
        idx=df.index[mask & df["ine"].eq(ine)]
        for i in idx:
            r=df.loc[i]
            tit=str(r.get("Titular") or "")
            usa_tit = not any(o in norm(tit) for o in OWNER)
            key=adv_tokens(r.get("descripcion","")) | (adv_tokens(tit) if usa_tit else set())
            key-=stop
            best=None; bscore=0; bshared=set()
            for g in templos:
                shared=key & g["toks"]
                if not shared: continue
                score=sum(1.0/freq[t] for t in shared)  # tokens raros pesan más
                if score>bscore: bscore=score; best=g; bshared=shared
            if not best: continue
            d=haversine_m(coords[ine]["lat"],coords[ine]["lon"],best["lat"],best["lon"])
            df.at[i,"osm_id"]=best["osm"]; df.at[i,"osm_lat"]=best["lat"]; df.at[i,"osm_lon"]=best["lon"]
            df.at[i,"osm_score"]=round(bscore,3); df.at[i,"dist_centroide_m"]=round(d)
            # AUTO-ACEPTA solo si hay un token discriminante único en el municipio
            unico = any(freq[t]==1 for t in bshared)
            if unico:
                df.at[i,"lat"]=best["lat"]; df.at[i,"lon"]=best["lon"]
                df.at[i,"fuente_coordenadas"]="edificio_osm"; df.at[i,"confianza"]="alta"
                df.at[i,"metodo"]="osm_token_unico"; df.at[i,"osm_estado"]="auto_aceptado"
            else:
                df.at[i,"osm_estado"]="candidato_confirmar"  # conserva coord previa
    return df

# ---------- carga CSV ----------
def cargar(input_dir):
    import pandas as pd
    files=[f for f in glob.glob(os.path.join(input_dir,"*.csv")) if "estadistica" not in f]
    fr=[]
    for f in files:
        d=pd.read_csv(f); d.columns=[c.replace("ecleSIástica","eclesiástica") for c in d.columns]
        for a in ("Título","Titulo","Descripción"):
            if a in d.columns: d=d.rename(columns={a:"descripcion"}); break
        fr.append(d)
    return pd.concat(fr,ignore_index=True)

def main():
    import pandas as pd
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",default="data/output"); ap.add_argument("--out",default="salida")
    ap.add_argument("--cache",default="geo_cache")
    ap.add_argument("--osm",choices=["on","off"],default="on")
    ap.add_argument("--overpass",default=OVERPASS,help="endpoint Overpass (p.ej. tu contenedor: http://localhost:12345/api/interpreter)")
    ap.add_argument("--osm-sleep",type=float,default=1.0,help="pausa entre municipios; 0 contra instancia local")
    ap.add_argument("--osm-only-ine",default=None,help="coma-separado: limitar etapa OSM a estos INE (validación)")
    a=ap.parse_args(); os.makedirs(a.out,exist_ok=True)
    munis,names,ents=cargar_padron(a.cache); M=Matcher(munis,names,ents)
    df=cargar(a.input); df=df[df["Municipio"].notna()].copy()
    df["prov_code"]=df["Provincia"].map(norm).map(PROV2CODE)
    res=df.apply(lambda r:M.match(r["Municipio"],r["prov_code"]),axis=1,result_type="expand")
    df=pd.concat([df,res],axis=1)
    if a.osm=="on":
        only=a.osm_only_ine.split(",") if a.osm_only_ine else None
        df=upgrade_osm(df,M.coords,endpoint=a.overpass,sleep=a.osm_sleep,only_ine=only)
    df[df["lat"].notna()].to_csv(os.path.join(a.out,"inmatriculaciones_geolocalizadas.csv"),index=False)
    df[df["lat"].isna()].to_csv(os.path.join(a.out,"residual_sin_geolocalizar.csv"),index=False)
    n=len(df); g=df[df["lat"].notna()]
    print(f"Total {n} | geolocalizado {len(g)} ({len(g)*100/n:.1f}%) | sin resolver {n-len(g)}")
    print("  fuente:",dict(Counter(g['fuente_coordenadas'])))
    if a.osm=="on":
        print("  OSM estado:",dict(Counter(df['osm_estado'].dropna())))

if __name__=="__main__":
    main()
