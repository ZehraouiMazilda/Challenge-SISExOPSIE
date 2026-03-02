import streamlit as st
from groq import Groq
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from chromadb.config import Settings
import pandas as pd
import json, os, hashlib
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

GROQ_MODEL      = "llama-3.3-70b-versatile"
EMBED_MODEL     = "paraphrase-multilingual-MiniLM-L12-v2"
CHROMA_PATH     = "./ChromaDB_firewall"
COLLECTION_NAME = "firewall_logs_rag"
TOP_N           = 4

SYSTEM_PROMPT = """Tu es SENTINEL, analyste SOC senior specialise en logs firewall Iptables.
Reponds TOUJOURS en francais. Base tes reponses UNIQUEMENT sur le CONTEXTE RAG fourni.

REGLES DE FORMAT (impression jury) :
- Entre 200 et 350 mots maximum
- Commence DIRECTEMENT par les faits, zero introduction generique
- Utilise des chiffres precis issus des donnees (ex: "720 blocages sur port 22")
- Structure en 2-3 sections courtes avec titres ##
- Maximum 5 bullet points par section, chaque point = 1 fait concret
- Termine par "## Recommandation" avec 2-3 actions precises et actionnables
- Jamais de phrases vagues comme "il est difficile de determiner" ou "en analysant les donnees"
- Si une info n'est pas dans le contexte RAG : une seule phrase courte pour le dire

INDICATEURS DE SEVERITE (1 seul par reponse, a la fin) :
🔴 Critique | 🟠 Eleve | 🟡 Moyen | 🟢 Info

STYLE SOC PROFESSIONNEL :
- Ton assertif et direct, comme un rapport d'incident
- Privilege les verbes d'action : "Bloquer", "Surveiller", "Isoler", "Investiguer"
- Cite les IPs, ports et rule_id exacts quand disponibles dans le contexte"""

SUGGESTED_QUESTIONS = {
    "🔍 Détection": [
        "Quelles IP montrent des patterns de scan de ports ?",
        "Y a-t-il des signes d'attaque brute force sur FTP ou SSH ?",
        "Identifie les comportements anormaux dans les logs",
        "Quels flux correspondent a un potentiel DDoS ?",
    ],
    "📊 Statistiques": [
        "Quels sont les ports les plus cibles par les Deny ?",
        "Donne-moi le top 5 des IP sources les plus actives",
        "Repartition TCP/UDP sur les connexions rejetees ?",
        "Analyse les pics d'activite par plage horaire",
    ],
    "🛡️ Sécurité": [
        "Quelles regles firewall semblent inutilisees ?",
        "IP hors plan d'adressage 159.84.x.x ?",
        "Recommandations pour durcir les regles Iptables",
        "Connexions suspectes vers ports sensibles (22, 21, 3306) ?",
    ],
    "🧠 Analytique": [
        "Compare le trafic TCP vs UDP en termes de risque",
        "Quels rule_id concentrent le plus de blocages ?",
        "Patterns temporels dans les attaques ?",
        "Synthese globale de la posture securite du SI",
    ],
}

CSS = """<style>
.rag-hero{background:linear-gradient(135deg,#080c14 0%,#0d1528 60%,#160a28 100%);
  border:1px solid rgba(0,212,255,0.12);border-radius:16px;padding:2rem 2.5rem;margin-bottom:1.5rem;}
.rag-hero h2{color:#00d4ff !important;font-size:1.5rem;margin:0 0 0.4rem 0;}
.rag-hero p{color:#6b7a99;font-size:0.88rem;margin:0;}
.sbar{display:flex;gap:1.5rem;align-items:center;flex-wrap:wrap;background:#0e1420;
  border:1px solid rgba(0,212,255,0.12);border-radius:10px;padding:0.7rem 1.2rem;margin-bottom:0.8rem;}
.sdot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:5px;}
.sg{background:#10b981;box-shadow:0 0 5px #10b981;}
.sb{background:#00d4ff;box-shadow:0 0 5px #00d4ff;}
.sr{background:#ff4d6d;box-shadow:0 0 5px #ff4d6d;}
.si{font-size:0.75rem;color:#6b7a99;display:flex;align-items:center;}
.sv{color:#e2e8f0;font-weight:600;margin-left:4px;font-size:0.72rem;}
.pip{display:flex;align-items:center;gap:0.4rem;flex-wrap:wrap;font-size:0.68rem;color:#6b7a99;margin-bottom:1rem;}
.ps{background:#141c2e;border:1px solid rgba(0,212,255,0.12);border-radius:5px;padding:0.18rem 0.5rem;color:#7b61ff;}
.src-chunk{background:rgba(123,97,255,0.05);border-left:3px solid #7b61ff;
  border-radius:0 8px 8px 0;padding:0.6rem 0.9rem;font-size:0.72rem;color:#6b7a99;
  margin-top:0.4rem;font-family:monospace;line-height:1.6;}
.mrow{display:flex;gap:0.5rem;flex-wrap:wrap;margin:0.8rem 0;}
.mbox{flex:1;min-width:60px;background:#141c2e;border:1px solid rgba(0,212,255,0.1);
  border-radius:8px;padding:0.5rem;text-align:center;}
.mv{font-size:1rem;font-weight:700;font-family:monospace;display:block;}
.ml{font-size:0.6rem;color:#6b7a99;text-transform:uppercase;letter-spacing:0.06em;}
</style>"""

# ── ChromaDB ─────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def init_chroma():
    ef = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    client = chromadb.PersistentClient(
        path=CHROMA_PATH, settings=Settings(anonymized_telemetry=False)
    )
    return client.get_or_create_collection(
        name=COLLECTION_NAME, embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )

# ── Build chunks ──────────────────────────────────────────────────────────
def build_chunks(df: pd.DataFrame) -> list:
    chunks = []
    total   = len(df)
    permits = int((df["action"] == "Permit").sum()) if "action" in df.columns else 0
    denies  = int((df["action"] == "Deny").sum())   if "action" in df.columns else 0
    proto   = df["protocol"].value_counts().to_dict() if "protocol" in df.columns else {}

    chunks.append(
        f"RESUME GLOBAL LOGS FIREWALL\n"
        f"Total: {total:,} | Permit: {permits:,} ({permits/total*100:.1f}%) | "
        f"Deny: {denies:,} ({denies/total*100:.1f}%)\nProtocoles: {proto}"
    )
    if "ip_source" in df.columns:
        ti  = df["ip_source"].value_counts().head(20).to_dict()
        tid = df[df["action"]=="Deny"]["ip_source"].value_counts().head(20).to_dict() if "action" in df.columns else {}
        chunks.append(f"TOP IP SOURCES ACTIVES\n{ti}\n\nTOP IP SOURCES BLOQUEES\n{tid}")

    if "dest_port" in df.columns:
        pn = {21:"FTP",22:"SSH",23:"Telnet",53:"DNS",80:"HTTP",443:"HTTPS",
              3306:"MySQL",8080:"HTTP-Alt",3389:"RDP",445:"SMB",137:"NetBIOS"}
        tp  = df["dest_port"].value_counts().head(20)
        tpd = df[df["action"]=="Deny"]["dest_port"].value_counts().head(20) if "action" in df.columns else pd.Series()
        chunks.append(
            "PORTS CIBLES\n" +
            "\n".join([f"Port {p}({pn.get(p,'?')}): {c}" for p,c in tp.items()]) +
            "\nPORTS BLOQUES\n" +
            "\n".join([f"Port {p}({pn.get(p,'?')}): {c}" for p,c in tpd.items()])
        )

    if "rule_id" in df.columns:
        r  = df["rule_id"].value_counts().head(15).to_dict()
        rd = df[df["action"]=="Deny"]["rule_id"].value_counts().head(10).to_dict() if "action" in df.columns else {}
        chunks.append(f"REGLES FIREWALL\n{r}\n\nREGLES AVEC DENY\n{rd}")

    if "date" in df.columns:
        try:
            dft = df.copy()
            dft["date"] = pd.to_datetime(dft["date"])
            dft["h"] = dft["date"].dt.hour
            bh = dft.groupby("h").size()
            dh = dft[dft["action"]=="Deny"].groupby("h").size() if "action" in dft.columns else pd.Series()
            chunks.append(
                f"ANALYSE TEMPORELLE\nPeriode: {dft['date'].min()} -> {dft['date'].max()}\n"
                f"Heure pic total: {int(bh.idxmax())}h | Heure pic deny: {int(dh.idxmax()) if not dh.empty else 'N/A'}h\n"
                "Distribution horaire:\n" + "\n".join([f"  {h}h: {c}" for h,c in bh.items()])
            )
        except Exception:
            pass

    if "ip_source" in df.columns and "action" in df.columns:
        hi  = df[df["action"]=="Deny"]["ip_source"].value_counts()
        hi  = hi[hi > hi.quantile(0.95)].head(20)
        ext = [ip for ip in df["ip_source"].unique() if not str(ip).startswith("159.84")][:30]
        chunks.append(
            "IP SUSPECTES (deny eleve top 5%)\n" +
            "\n".join([f"{ip}: {c} blocages" for ip,c in hi.items()]) +
            "\nIP HORS PLAN ADRESSAGE (pas 159.84.x.x)\n" + "\n".join(ext[:20])
        )

    if all(c in df.columns for c in ["action","dest_port"]):
        s = df[(df["action"]=="Deny") & (df["dest_port"].isin([21,22,23,3306,3389,445,137]))].head(50)
        if not s.empty:
            chunks.append("CONNEXIONS SUSPECTES PORTS SENSIBLES\n" + s.to_string(index=False))

    sample = df.sample(min(500, len(df)), random_state=42)
    for i in range(0, len(sample), 500):
        chunks.append(f"ECHANTILLON LOGS {i}-{i+400}:\n" + sample.iloc[i:i+400].to_string(index=False))

    return chunks


def ingest(df: pd.DataFrame, collection) -> int:
    h = hashlib.md5(pd.util.hash_pandas_object(df.head(500)).values).hexdigest()
    if st.session_state.get("rag_hash") == h:
        return st.session_state.get("rag_n", 0)
    try:
        ids = collection.get()["ids"]
        if ids:
            collection.delete(ids=ids)
    except Exception:
        pass
    chunks = build_chunks(df)
    for i in range(0, len(chunks), 50):
        b = chunks[i:i+50]
        collection.add(documents=b, ids=[f"c{i+j}" for j in range(len(b))])
    st.session_state["rag_hash"] = h
    st.session_state["rag_n"] = len(chunks)
    return len(chunks)


def retrieve(query: str, collection, top_n: int) -> list:
    r = collection.query(query_texts=[query], n_results=top_n)
    return r["documents"][0] if r["documents"] else []


def call_groq(question: str, ctx_chunks: list, history: list) -> str:
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        return "Cle GROQ_API_KEY manquante dans .env"
    ctx = "\n\n---\n\n".join([c[:800] for c in ctx_chunks])  # max 800 chars par chunk
    msgs = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"CONTEXTE RAG (donnees reelles):\n\n{ctx}"},
    ]
    for m in history[-6:]:
        msgs.append({"role": m["role"], "content": m["content"]})
    msgs.append({"role": "user", "content": question})
    try:
        r = Groq(api_key=key).chat.completions.create(
            model=GROQ_MODEL, messages=msgs, max_tokens=1500, temperature=0.2
        )
        return r.choices[0].message.content
    except Exception as e:
        err = str(e)
        if "401" in err: return "Cle API invalide. Verifiez GROQ_API_KEY."
        if "429" in err: return "Limite de requetes atteinte. Attendez quelques secondes."
        return f"Erreur Groq: {err}"


# ── Main view ─────────────────────────────────────────────────────────────
def show():
    st.markdown(CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="rag-hero">
        <h2>🛡️ SENTINEL — Expert RAG Cybersécurité</h2>
        <p>Analyse de vos logs firewall Iptables par RAG · ChromaDB + Embeddings MiniLM-L12 + Llama 3.3 70B via Groq<br>
        Les réponses sont ancrées dans vos données réelles grâce à la recherche vectorielle sémantique.</p>
    </div>
    """, unsafe_allow_html=True)

    for k, v in [("llm_history",[]),("rag_hash",None),("rag_n",0),("show_src",False)]:
        if k not in st.session_state:
            st.session_state[k] = v

    df         = st.session_state.get("df", None)
    rag_ready  = False
    collection = None

    # ── Clé : ne spinner QUE si pas encore indexé ──────────────────
    if df is not None and not df.empty:
        already_indexed = st.session_state.get("rag_hash") is not None

        if already_indexed:
            # Navigation fluide — silencieux et instantané
            try:
                collection = init_chroma()
                rag_ready  = True
            except Exception as e:
                st.error(f"Erreur RAG : {e}")
        else:
            # Premier chargement uniquement
            with st.spinner("⚙️ Initialisation RAG "):
                try:
                    collection = init_chroma()
                    ingest(df, collection)
                    rag_ready  = True
                except Exception as e:
                    st.error(f"Erreur RAG : {e}")

    n_chunks = st.session_state.get("rag_n", 0)
    total    = len(df) if df is not None else 0
    denies   = int((df["action"]=="Deny").sum())   if df is not None and "action" in df.columns else 0
    permits  = total - denies
    n_ips    = df["ip_source"].nunique() if df is not None and "ip_source" in df.columns else 0
    dr       = denies/total*100 if total else 0
    dot      = "sg" if rag_ready else "sr"

    st.markdown(f"""
    <div class="sbar">
        <div class="si"><span class="sdot {dot}"></span>RAG <span class="sv">{'Actif' if rag_ready else 'Inactif'}</span></div>
        <div class="si"><span class="sdot sb"></span>Chunks <span class="sv">{n_chunks}</span></div>
        <div class="si"><span class="sdot sb"></span>Logs <span class="sv">{total:,}</span></div>
        <div class="si"><span class="sdot sg"></span>Permit <span class="sv">{permits:,}</span></div>
        <div class="si"><span class="sdot sr"></span>Deny <span class="sv">{denies:,}</span></div>
        <div class="si">Modèle <span class="sv">Llama 3.3 70B · Groq</span></div>
    </div>
    <div class="pip">
        <span class="ps">📄 CSV</span><span>→</span>
        <span class="ps">✂️ Chunking</span><span>→</span>
        <span class="ps">🧬 MiniLM Embeddings</span><span>→</span>
        <span class="ps">🗄️ ChromaDB</span><span>→</span>
        <span class="ps">🔍 Top-N Retrieval</span><span>→</span>
        <span class="ps">🤖 Llama 3.3 70B</span><span>→</span>
        <span class="ps">💬 Réponse</span>
    </div>
    """, unsafe_allow_html=True)

    col_chat, col_side = st.columns([3, 1], gap="medium")

    # ── Panneau droit ────────────────────────────────────────────────
    with col_side:
        st.markdown("#### 💡 Questions suggérées")
        for cat, qs in SUGGESTED_QUESTIONS.items():
            with st.expander(cat, expanded=(cat == "🔍 Détection")):
                for q in qs:
                    if st.button(q, key=f"s_{abs(hash(q))}", use_container_width=True):
                        st.session_state["llm_pending"] = q

        st.markdown("#### ⚙️ Paramètres RAG")
        top_n = st.slider("Chunks Top-N", 2, 8, TOP_N,
                          help="Nombre de chunks envoyés au LLM comme contexte")
        st.session_state.show_src = st.toggle("Afficher sources RAG", False)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Effacer la conversation", use_container_width=True):
            st.session_state.llm_history = []
            st.rerun()
        if st.session_state.llm_history:
            st.download_button(
                "📥 Exporter (JSON)",
                data=json.dumps(st.session_state.llm_history, ensure_ascii=False, indent=2),
                file_name=f"sentinel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json", use_container_width=True
            )

    # ── Zone de chat ─────────────────────────────────────────────────
    with col_chat:
        if not rag_ready:
            st.warning("⚠️ Aucune donnée chargée. Vérifiez que `df` est dans `st.session_state`.")
            return

        if not st.session_state.llm_history:
            with st.chat_message("assistant"):
                st.markdown(
                    f"👋 Bonjour ! Je suis **SENTINEL**, votre analyste SOC IA.\n\n"
                    f"✅ **{n_chunks} chunks** indexés dans ChromaDB depuis vos logs firewall.\n\n"
                    f"🔍 Mes réponses s'appuient sur vos **données réelles** "
                    f"via recherche vectorielle sémantique (Top-{top_n} chunks).\n\n"
                    "Posez une question ou choisissez une suggestion →"
                )
        else:
            for i, msg in enumerate(st.session_state.llm_history):
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    if msg["role"] == "assistant" and st.session_state.show_src:
                        src = st.session_state.get(f"src_{i}", [])
                        if src:
                            with st.expander(f"🔍 {len(src)} sources RAG", expanded=False):
                                for j, c in enumerate(src):
                                    st.markdown(
                                        f'<div class="src-chunk"><b>📄 Chunk {j+1}/{len(src)}</b><br>'
                                        f'{c[:350]}{"..." if len(c)>350 else ""}</div>',
                                        unsafe_allow_html=True
                                    )

        pending    = st.session_state.pop("llm_pending", None)
        user_input = st.chat_input("Interrogez SENTINEL sur vos logs firewall…")
        question   = pending or user_input

        if question:
            with st.chat_message("user"):
                st.markdown(question)

            with st.spinner("🔍 Recherche vectorielle dans ChromaDB…"):
                ctx = retrieve(question, collection, top_n)

            ans_idx     = len(st.session_state.llm_history) + 1
            st.session_state[f"src_{ans_idx}"] = ctx
            hist_before = st.session_state.llm_history.copy()
            st.session_state.llm_history.append({"role": "user", "content": question})

            with st.chat_message("assistant"):
                with st.spinner("🤖 SENTINEL génère la réponse…"):
                    answer = call_groq(question, ctx, hist_before)
                st.markdown(answer)
                if st.session_state.show_src and ctx:
                    with st.expander(f"🔍 {len(ctx)} sources utilisées", expanded=False):
                        for j, c in enumerate(ctx):
                            st.markdown(
                                f'<div class="src-chunk"><b>📄 Chunk {j+1}/{len(ctx)}</b><br>'
                                f'{c[:350]}{"..." if len(c)>350 else ""}</div>',
                                unsafe_allow_html=True
                            )

            st.session_state.llm_history.append({"role": "assistant", "content": answer})
            st.rerun()