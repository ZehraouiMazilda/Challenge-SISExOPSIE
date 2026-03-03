import streamlit as st
from groq import Groq
import pandas as pd
import numpy as np
import json, os, hashlib, logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from fpdf import FPDF
import unicodedata

logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

GROQ_MODEL = "llama-3.3-70b-versatile"
TOP_N      = 4

SYSTEM_PROMPT = """Tu es SENTINEL, analyste SOC senior specialise en logs firewall Iptables.
Reponds TOUJOURS en francais. Base tes reponses UNIQUEMENT sur le CONTEXTE RAG fourni.
REGLES DE FORMAT :
- Entre 200 et 350 mots maximum
- Commence DIRECTEMENT par les faits, zero introduction generique
- Utilise des chiffres precis issus des donnees
- Structure en 2-3 sections courtes avec titres ##
- Maximum 5 bullet points par section
- Termine par ## Recommandation avec 2-3 actions precises
INDICATEURS DE SEVERITE : critique | Eleve | Moyen | Info
STYLE SOC : Ton assertif, verbes d'action, cite IPs/ports exacts"""

REPORT_PROMPT = """Tu es SENTINEL. Genere un rapport de securite complet en francais.
Structure EXACTE :
# RAPPORT D'ANALYSE SECURITE - SENTINEL SOC
## Resume Executif
## 1. Statistiques Generales
## 2. Menaces Identifiees
## 3. Top IP Suspectes
## 4. Ports les Plus Cibles
## 5. Analyse Temporelle
## 6. Regles Firewall
## 7. Recommandations Prioritaires
## Conclusion
Rapport genere par SENTINEL - Projet SISE-OPSIE 2026"""

SUGGESTED_QUESTIONS = {
    "Detection": [
        "Quelles IP montrent des patterns de scan de ports ?",
        "Y a-t-il des signes d'attaque brute force sur FTP ou SSH ?",
        "Identifie les comportements anormaux dans les logs",
        "Quels flux correspondent a un potentiel DDoS ?",
    ],
    "Statistiques": [
        "Quels sont les ports les plus cibles par les Deny ?",
        "Donne-moi le top 5 des IP sources les plus actives",
        "Repartition TCP/UDP sur les connexions rejetees ?",
        "Analyse les pics d'activite par plage horaire",
    ],
    "Securite": [
        "Quelles regles firewall semblent inutilisees ?",
        "IP hors plan d'adressage 159.84.x.x ?",
        "Recommandations pour durcir les regles Iptables",
        "Connexions suspectes vers ports sensibles (22, 21, 3306) ?",
    ],
    "Analytique": [
        "Compare le trafic TCP vs UDP en termes de risque",
        "Patterns temporels dans les attaques ?",
        "Synthese globale de la posture securite du SI",
    ],
}

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
:root {
    --bg-dark:#0a0e1a; --bg-card:#111827; --bg-card2:#1a2235;
    --accent:#00d4ff; --accent2:#ff4d6d; --accent3:#7b61ff;
    --text:#e2e8f0; --text-dim:#8892a4;
    --border:rgba(0,212,255,0.15); --success:#10b981; --warning:#f59e0b;
}
.stApp { background-color: var(--bg-dark) !important; }
section[data-testid="stSidebar"] { background-color: #080c16 !important; }
.block-container { padding-top:1.5rem !important; padding-bottom:3rem !important; }
html,body,[class*="css"] { font-family:'DM Sans',sans-serif !important; color:var(--text) !important; }
h1,h2,h3,h4 { font-family:'Space Mono',monospace !important; }
.ml-hero { background:linear-gradient(135deg,#0d1b2a 0%,#0a0e1a 50%,#1a0a2e 100%); border:1px solid var(--border); border-radius:16px; padding:2.5rem 3rem; margin-bottom:2rem; }
.ml-hero h1 { font-size:1.8rem; color:var(--accent) !important; margin:0 0 0.5rem 0; letter-spacing:-1px; }
.ml-hero p { color:var(--text-dim); font-size:0.95rem; margin:0; line-height:1.7; }
.section-header { display:flex; align-items:center; gap:0.75rem; margin-bottom:1.2rem; padding-bottom:0.8rem; border-bottom:1px solid var(--border); }
.section-icon { width:36px; height:36px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:1rem; flex-shrink:0; }
.icon-blue{background:rgba(0,212,255,0.12);} .icon-red{background:rgba(255,77,109,0.12);}
.icon-purple{background:rgba(123,97,255,0.12);} .icon-green{background:rgba(16,185,129,0.12);}
.section-title { font-family:'Space Mono',monospace !important; font-size:1rem; font-weight:700; color:var(--text) !important; margin:0; }
.section-subtitle { font-size:0.8rem; color:var(--text-dim); margin:0; }
.sbar { display:flex; gap:1.5rem; align-items:center; flex-wrap:wrap; background:var(--bg-card); border:1px solid var(--border); border-radius:10px; padding:0.7rem 1.2rem; margin-bottom:0.8rem; }
.sdot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:5px;}
.sg{background:#10b981;box-shadow:0 0 5px #10b981;} .sb{background:#00d4ff;box-shadow:0 0 5px #00d4ff;} .sr{background:#ff4d6d;box-shadow:0 0 5px #ff4d6d;}
.si{font-size:0.75rem;color:var(--text-dim);display:flex;align-items:center;} .sv{color:var(--text);font-weight:600;margin-left:4px;font-size:0.72rem;}
.pip{display:flex;align-items:center;gap:0.4rem;flex-wrap:wrap;font-size:0.68rem;color:var(--text-dim);margin-bottom:1rem;}
.ps{background:var(--bg-card2);border:1px solid var(--border);border-radius:5px;padding:0.18rem 0.5rem;color:var(--accent3);}
.src-chunk{background:rgba(123,97,255,0.05);border-left:3px solid var(--accent3);border-radius:0 8px 8px 0;padding:0.6rem 0.9rem;font-size:0.72rem;color:var(--text-dim);margin-top:0.4rem;font-family:monospace;line-height:1.6;}
div[data-baseweb="select"]>div{background-color:var(--bg-card2) !important;border-color:var(--border) !important;color:var(--text) !important;}
hr{border-color:var(--border) !important;margin:1.5rem 0 !important;}
[data-testid="stChatMessage"]{background:var(--bg-card) !important;border:1px solid var(--border) !important;border-radius:10px !important;padding:0.8rem 1rem !important;margin-bottom:0.5rem !important;}
</style>"""


def section_header(icon, title, subtitle, icon_class="icon-blue"):
    st.markdown(f"""<div class="section-header"><div class="section-icon {icon_class}">{icon}</div><div><p class="section-title">{title}</p><p class="section-subtitle">{subtitle}</p></div></div>""", unsafe_allow_html=True)


def embed(text):
    vec = np.zeros(512)
    for word in text.lower().split():
        idx = int(hashlib.md5(word.encode()).hexdigest(), 16) % 512
        vec[idx] += 1.0
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def build_index(chunks):
    return np.array([embed(c) for c in chunks])


def retrieve(query, chunks, index, top_n):
    q_vec = embed(query)
    scores = index @ q_vec
    top_idx = np.argsort(scores)[::-1][:top_n]
    return [chunks[i] for i in top_idx]


def build_chunks(df):
    chunks = []
    total   = len(df)
    permits = int((df["action"] == "Permit").sum()) if "action" in df.columns else 0
    denies  = int((df["action"] == "Deny").sum())   if "action" in df.columns else 0
    proto   = df["protocol"].value_counts().to_dict() if "protocol" in df.columns else {}
    chunks.append(f"RESUME GLOBAL LOGS FIREWALL\nTotal: {total:,} | Permit: {permits:,} ({permits/total*100:.1f}%) | Deny: {denies:,} ({denies/total*100:.1f}%)\nProtocoles: {proto}")
    if "ip_source" in df.columns:
        ti  = df["ip_source"].value_counts().head(20).to_dict()
        tid = df[df["action"]=="Deny"]["ip_source"].value_counts().head(20).to_dict() if "action" in df.columns else {}
        chunks.append(f"TOP IP SOURCES ACTIVES\n{ti}\n\nTOP IP SOURCES BLOQUEES\n{tid}")
    if "dest_port" in df.columns:
        pn = {21:"FTP",22:"SSH",23:"Telnet",53:"DNS",80:"HTTP",443:"HTTPS",3306:"MySQL",8080:"HTTP-Alt",3389:"RDP",445:"SMB"}
        tp  = df["dest_port"].value_counts().head(20)
        tpd = df[df["action"]=="Deny"]["dest_port"].value_counts().head(20) if "action" in df.columns else pd.Series()
        chunks.append("PORTS CIBLES\n"+("\n".join([f"Port {p}({pn.get(p,'?')}): {c}" for p,c in tp.items()]))+"\nPORTS BLOQUES\n"+("\n".join([f"Port {p}({pn.get(p,'?')}): {c}" for p,c in tpd.items()])))
    if "rule_id" in df.columns:
        r  = df["rule_id"].value_counts().head(15).to_dict()
        rd = df[df["action"]=="Deny"]["rule_id"].value_counts().head(10).to_dict() if "action" in df.columns else {}
        chunks.append(f"REGLES FIREWALL\n{r}\n\nREGLES DENY\n{rd}")
    if "date" in df.columns:
        try:
            dft = df.copy(); dft["date"]=pd.to_datetime(dft["date"]); dft["h"]=dft["date"].dt.hour
            bh  = dft.groupby("h").size()
            dh  = dft[dft["action"]=="Deny"].groupby("h").size() if "action" in dft.columns else pd.Series()
            chunks.append(f"ANALYSE TEMPORELLE\nPeriode: {dft['date'].min()} -> {dft['date'].max()}\nPic total: {int(bh.idxmax())}h | Pic deny: {int(dh.idxmax()) if not dh.empty else 'N/A'}h\n"+("\n".join([f"  {h}h: {c}" for h,c in bh.items()])))
        except Exception: pass
    if "ip_source" in df.columns and "action" in df.columns:
        hi  = df[df["action"]=="Deny"]["ip_source"].value_counts()
        hi  = hi[hi>hi.quantile(0.95)].head(20)
        ext = [ip for ip in df["ip_source"].unique() if not str(ip).startswith("159.84")][:20]
        chunks.append("IP SUSPECTES\n"+("\n".join([f"{ip}: {c} blocages" for ip,c in hi.items()]))+"\nIP HORS PLAN\n"+("\n".join(ext)))
    if all(c in df.columns for c in ["action","dest_port"]):
        s = df[(df["action"]=="Deny")&(df["dest_port"].isin([21,22,23,3306,3389,445,137]))].head(50)
        if not s.empty: chunks.append("CONNEXIONS SUSPECTES PORTS SENSIBLES\n"+s.to_string(index=False))
    sample = df.sample(min(300,len(df)),random_state=42)
    for i in range(0,len(sample),300):
        chunks.append(f"ECHANTILLON LOGS {i}:\n"+sample.iloc[i:i+300].to_string(index=False))
    return chunks


def init_rag(df):
    h = hashlib.md5(pd.util.hash_pandas_object(df.head(500)).values).hexdigest()
    if (st.session_state.get("rag_hash") == h and "rag_chunks" in st.session_state and "rag_index" in st.session_state):
        return st.session_state["rag_chunks"], st.session_state["rag_index"]
    chunks = build_chunks(df)
    index  = build_index(chunks)
    st.session_state["rag_chunks"] = chunks
    st.session_state["rag_index"]  = index
    st.session_state["rag_hash"]   = h
    st.session_state["rag_n"]      = len(chunks)
    return chunks, index


def call_groq(question, ctx_chunks, history):
    key = os.getenv("GROQ_API_KEY", "")
    if not key: return "Cle GROQ_API_KEY manquante dans .env"
    ctx  = "\n\n---\n\n".join([c[:800] for c in ctx_chunks])
    msgs = [{"role":"system","content":SYSTEM_PROMPT},{"role":"system","content":f"CONTEXTE RAG:\n\n{ctx}"}]
    for m in history[-6:]: msgs.append({"role":m["role"],"content":m["content"]})
    msgs.append({"role":"user","content":question})
    try:
        r = Groq(api_key=key).chat.completions.create(model=GROQ_MODEL,messages=msgs,max_tokens=1500,temperature=0.2)
        return r.choices[0].message.content
    except Exception as e:
        err=str(e)
        if "401" in err: return "Cle API invalide."
        if "429" in err: return "Limite de requetes atteinte."
        return f"Erreur Groq : {err}"


def generate_report_text(chunks, index, df):
    key = os.getenv("GROQ_API_KEY","")
    if not key: return "Cle GROQ_API_KEY manquante."
    queries = ["resume global statistiques logs","IP suspectes attaques","ports cibles blocages deny","regles firewall","analyse temporelle pics"]
    all_chunks = []
    for q in queries:
        for c in retrieve(q,chunks,index,top_n=3):
            if c not in all_chunks: all_chunks.append(c)
    ctx  = "\n\n---\n\n".join([c[:600] for c in all_chunks[:12]])
    msgs = [{"role":"system","content":REPORT_PROMPT},{"role":"system","content":f"CONTEXTE:\n\n{ctx}"},{"role":"user","content":"Genere le rapport complet."}]
    try:
        r = Groq(api_key=key).chat.completions.create(model=GROQ_MODEL,messages=msgs,max_tokens=3000,temperature=0.1)
        return r.choices[0].message.content
    except Exception as e: return f"Erreur rapport: {e}"


def build_pdf(report_text, df):
    def clean(text):
        rp = {"\U0001f534":"[CRIT]","\U0001f7e0":"[ELEVE]","\U0001f7e1":"[MOY]","\U0001f7e2":"[INFO]","\u2022":"-","\u2192":"->","\u2014":"-","\u2013":"-","\u2018":"'","\u2019":"'","\u201c":'"','\u201d':'"'}
        for k,v in rp.items(): text=text.replace(k,v)
        return unicodedata.normalize("NFKD",text).encode("ascii",errors="ignore").decode("ascii")
    c=clean(report_text); pdf=FPDF(); pdf.set_auto_page_break(auto=True,margin=20); pdf.add_page()
    pdf.set_fill_color(8,12,20); pdf.rect(0,0,210,40,"F")
    pdf.set_font("Helvetica","B",18); pdf.set_text_color(0,212,255); pdf.set_xy(15,10)
    pdf.cell(0,10,"SENTINEL - Rapport Analyse Securite",ln=True)
    pdf.set_font("Helvetica","",9); pdf.set_text_color(107,122,153); pdf.set_xy(15,22)
    pdf.cell(0,6,f"SISE-OPSIE 2026 - {datetime.now().strftime('%d/%m/%Y %H:%M')}",ln=True)
    total=len(df) if df is not None else 0; denies=int((df["action"]=="Deny").sum()) if df is not None and "action" in df.columns else 0
    pdf.set_xy(15,30); pdf.cell(0,6,f"Logs: {total:,} | Deny: {denies:,} ({denies/total*100:.1f}%)",ln=True)
    pdf.ln(18); pdf.set_text_color(30,30,30); W=180
    for line in c.split("\n"):
        line=line.strip()
        if not line: pdf.ln(3)
        elif line.startswith("# "): pdf.set_font("Helvetica","B",15); pdf.set_text_color(0,100,180); pdf.set_fill_color(230,240,255); pdf.set_x(15); pdf.multi_cell(W,9,line[2:],fill=True); pdf.ln(2)
        elif line.startswith("## "): pdf.set_font("Helvetica","B",12); pdf.set_text_color(0,80,150); pdf.ln(3); pdf.set_x(15); pdf.multi_cell(W,8,line[3:]); pdf.set_draw_color(0,150,200); pdf.set_line_width(0.4); pdf.line(15,pdf.get_y(),195,pdf.get_y()); pdf.ln(2)
        elif line.startswith("- ") or line.startswith("* "): pdf.set_font("Helvetica","",10); pdf.set_text_color(40,40,40); pdf.set_x(18); pdf.multi_cell(W-3,6,"- "+line[2:])
        else: pdf.set_font("Helvetica","",10); pdf.set_text_color(40,40,40); pdf.set_x(15); pdf.multi_cell(W,6,line)
    pdf.set_y(-20); pdf.set_font("Helvetica","I",8); pdf.set_text_color(150,150,150)
    pdf.cell(0,6,f"SENTINEL SOC - SISE-OPSIE 2026 - Page {pdf.page_no()}",align="C")
    return bytes(pdf.output())


def show():
    st.markdown(STYLE, unsafe_allow_html=True)
    st.markdown('''<div class="ml-hero"><h1>SENTINEL — Expert RAG Cybersecurite</h1><p>Analyse de vos logs pare-feu par IA augmentee par recuperation (RAG).<br>Recherche vectorielle en memoire + Llama 3.3 70B via Groq.</p></div>''', unsafe_allow_html=True)

    for k,v in [("llm_history",[]),("rag_hash",None),("rag_n",0),("show_src",False),("report_bytes",None)]:
        if k not in st.session_state: st.session_state[k]=v

    if "df" not in st.session_state or st.session_state["df"] is None:
        try:
            st.session_state["df"]=pd.read_csv(Path(__file__).resolve().parent.parent/"data"/"data_exm.csv")
        except FileNotFoundError:
            st.error("Fichier introuvable : data/data_exm.csv"); return

    df=st.session_state["df"]; rag_ready=False; chunks=[]; index=None

    try:
        if st.session_state.get("rag_hash") is None:
            with st.spinner("Initialisation RAG..."):
                chunks,index=init_rag(df)
        else:
            chunks,index=init_rag(df)
        rag_ready=True
    except Exception as e:
        st.error(f"Erreur RAG : {e}")

    n_chunks=st.session_state.get("rag_n",0); total=len(df)
    denies=int((df["action"]=="Deny").sum()) if "action" in df.columns else 0; permits=total-denies
    dot="sg" if rag_ready else "sr"

    st.markdown(f'''<div class="sbar">
        <div class="si"><span class="sdot {dot}"></span>RAG <span class="sv">{"Actif" if rag_ready else "Inactif"}</span></div>
        <div class="si"><span class="sdot sb"></span>Chunks <span class="sv">{n_chunks}</span></div>
        <div class="si"><span class="sdot sb"></span>Logs <span class="sv">{total:,}</span></div>
        <div class="si"><span class="sdot sg"></span>Permit <span class="sv">{permits:,}</span></div>
        <div class="si"><span class="sdot sr"></span>Deny <span class="sv">{denies:,}</span></div>
        <div class="si">Modele <span class="sv">Llama 3.3 70B Groq</span></div>
    </div>
    <div class="pip">
        <span class="ps">CSV</span><span>-></span><span class="ps">Chunking</span><span>-></span>
        <span class="ps">Embedding vectoriel</span><span>-></span><span class="ps">Top-N Retrieval</span><span>-></span>
        <span class="ps">Llama 3.3 70B</span><span>-></span><span class="ps">Reponse</span>
    </div>''', unsafe_allow_html=True)

    col_chat,col_side=st.columns([3,1],gap="medium")

    with col_side:
        section_header("💡","Questions Suggerees","Cliquez pour interroger SENTINEL","icon-purple")
        for cat,qs in SUGGESTED_QUESTIONS.items():
            with st.expander(cat,expanded=(cat=="Detection")):
                for q in qs:
                    if st.button(q,key=f"s_{abs(hash(q))}",use_container_width=True):
                        st.session_state["llm_pending"]=q
        st.markdown("---")
        section_header("⚙️","Parametres RAG","Ajustez le moteur","icon-blue")
        top_n=st.slider("Chunks Top-N",2,8,TOP_N)
        st.session_state.show_src=st.toggle("Afficher sources RAG",False)
        st.markdown("---")
        section_header("📄","Rapport PDF","Generer un rapport complet","icon-green")
        if rag_ready:
            if st.button("Generer le rapport",use_container_width=True,type="primary"):
                with st.spinner("Generation en cours..."):
                    rt=generate_report_text(chunks,index,df)
                    st.session_state["report_bytes"]=build_pdf(rt,df)
                st.success("Rapport genere !")
            if st.session_state.get("report_bytes"):
                st.download_button("Telecharger PDF",data=st.session_state["report_bytes"],file_name=f"SENTINEL_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",mime="application/pdf",use_container_width=True)
        st.markdown("---")
        if st.button("Effacer la conversation",use_container_width=True):
            st.session_state.llm_history=[]; st.rerun()
        if st.session_state.llm_history:
            st.download_button("Exporter chat JSON",data=json.dumps(st.session_state.llm_history,ensure_ascii=False,indent=2),file_name=f"sentinel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",mime="application/json",use_container_width=True)

    with col_chat:
        section_header("🤖","Interface de Conversation","Interrogez SENTINEL sur vos logs en langage naturel","icon-red")
        if not rag_ready:
            st.warning("Le moteur RAG est inactif. Verifiez les erreurs ci-dessus."); return
        if not st.session_state.llm_history:
            with st.chat_message("assistant"):
                st.markdown(f"Bonjour ! Je suis **SENTINEL**.\n\n**{n_chunks} chunks** indexes en memoire.\n\nMes reponses s'appuient sur vos donnees reelles (Top-{top_n} chunks).\n\nPosez une question ou choisissez une suggestion.")
        else:
            for i,msg in enumerate(st.session_state.llm_history):
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    if msg["role"]=="assistant" and st.session_state.show_src:
                        src=st.session_state.get(f"src_{i}",[])
                        if src:
                            with st.expander(f"{len(src)} sources RAG",expanded=False):
                                for j,c in enumerate(src):
                                    st.markdown(f'''<div class="src-chunk"><b>Chunk {j+1}/{len(src)}</b><br>{c[:350]}{"..." if len(c)>350 else ""}</div>''',unsafe_allow_html=True)

        pending=st.session_state.pop("llm_pending",None); user_input=st.chat_input("Interrogez SENTINEL..."); question=pending or user_input

        if question:
            with st.chat_message("user"): st.markdown(question)
            ctx=retrieve(question,chunks,index,top_n)
            ans_idx=len(st.session_state.llm_history)+1; st.session_state[f"src_{ans_idx}"]=ctx
            hist_before=st.session_state.llm_history.copy()
            st.session_state.llm_history.append({"role":"user","content":question})
            with st.chat_message("assistant"):
                with st.spinner("SENTINEL genere la reponse..."): answer=call_groq(question,ctx,hist_before)
                st.markdown(answer)
                if st.session_state.show_src and ctx:
                    with st.expander(f"{len(ctx)} sources",expanded=False):
                        for j,c in enumerate(ctx):
                            st.markdown(f'''<div class="src-chunk"><b>Chunk {j+1}</b><br>{c[:350]}</div>''',unsafe_allow_html=True)
            st.session_state.llm_history.append({"role":"assistant","content":answer})
            st.rerun()