import { useEffect, useMemo, useState } from "react";
import {
  Archive, ArrowDown, ArrowLeft, Check, ChevronLeft, ChevronRight,
  Inbox, LogOut, Mail, RefreshCw, Search, Send, Sparkles, Star, Tag,
  X, AlertCircle, Clock3
} from "lucide-react";
import { classifyEmail, getEmails, getEmail, getSummary, login, updateEmail } from "../lib/api";
import type { Email, Summary } from "../types/email";

const categories = ["client", "facture", "rendez-vous", "newsletter", "spam probable", "autre"];
const categoryLabels: Record<string, string> = {
  client: "Client", facture: "Facture", "rendez-vous": "Rendez-vous",
  newsletter: "Newsletter", "spam probable": "Spam probable", autre: "Autre"
};
const dateLabel = (value: string | null) => value
  ? new Date(value).toLocaleString("fr-FR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })
  : "Date inconnue";
const senderName = (value: string) => {
  const match = value.match(/^"?([^"<]+)"?\s*<?/);
  return match?.[1]?.trim() || value;
};
const initials = (value: string) => senderName(value).split(/[ @._-]/).filter(Boolean).slice(0, 2).map(x => x[0]).join("").toUpperCase();

export default function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem("usts_token") || "");
  const [emailAddress, setEmailAddress] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [emails, setEmails] = useState<Email[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selected, setSelected] = useState<Email | null>(null);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [priority, setPriority] = useState("");
  const [status, setStatus] = useState("");
  const [section, setSection] = useState("inbox");
  const [summary, setSummary] = useState<Summary | null>(null);
  const [reply, setReply] = useState("");
  const [replyTone, setReplyTone] = useState("neutral");
  const [notice, setNotice] = useState("");

  async function generateReplyAI() {
    if (!selected || !token) return;
    setLoading(true);
    setError("");
    try {
      const resp = await fetch("/api/emails/" + selected.id + "/draft?tone=" + replyTone, {
        method: "POST",
        headers: { Authorization: "Bearer " + token },
      });
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      const data = await resp.json();
      setReply(data.draft || "");
      setNotice("Brouillon IA genere. Relisez et modifiez avant envoi.");
    } catch (e: any) {
      setError("Generation impossible : " + (e.message || e));
    } finally {
      setLoading(false);
    }
  }

  async function load(currentToken = token, currentPage = page) {
    if (!currentToken) return;
    setLoading(true); setError("");
    try {
      const filters: Record<string, string> = {};
      if (search.trim()) filters.search = search.trim();
      if (category) filters.category = category;
      if (priority) filters.priority = priority;
      if (status) filters.status = status;
      if (section === "priority") filters.priority = "1";
      if (section === "review") filters.status = "à vérifier";
      const data = await getEmails(currentToken, filters, currentPage);
      setEmails(data.items); setTotal(data.total); setTotalPages(Math.max(1, data.total_pages));
      if (selected) {
        const updated = data.items.find(item => item.id === selected.id);
        if (updated) setSelected(updated);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Chargement impossible");
    } finally { setLoading(false); }
  }

  async function loadSummary() {
    try { setSummary(await getSummary(token)); } catch { /* summary is optional */ }
  }

  useEffect(() => { if (token) { void load(token, 1); void loadSummary(); } }, [token]);
  useEffect(() => {
    const timer = window.setTimeout(() => { setPage(1); void load(token, 1); }, 250);


  return () => window.clearTimeout(timer);
  }, [search, category, priority, status, section]);

  async function handleLogin(event: React.FormEvent) {
    event.preventDefault(); setLoginError("");
    try {
      const data = await login(emailAddress, password);
      sessionStorage.setItem("usts_token", data.access_token);
      setToken(data.access_token);
    } catch (e) { setLoginError(e instanceof Error ? e.message : "Connexion impossible"); }
  }

  async function openEmail(item: Email) {
    setSelected(item); setReply("");
    try { setSelected(await getEmail(token, item.id)); }
    catch { setSelected(item); }
  }

  async function refresh() { await load(); await loadSummary(); }

  async function archiveSelected() {
    if (!selected) return;
    try {
      const updated = await updateEmail(token, selected.id, { status: "archive" });
      setSelected(updated); setNotice("E-mail archivé"); await load();
    } catch (e) { setError(e instanceof Error ? e.message : "Échec de l’archivage"); }
  }

  async function markProcessed() {
    if (!selected) return;
    try {
      const updated = await updateEmail(token, selected.id, { status: "traite" });
      setSelected(updated); setNotice("E-mail marqué comme traité"); await load();
    } catch (e) { setError(e instanceof Error ? e.message : "Modification impossible"); }
  }

  async function generateReply() {
    if (!selected) return;
    setLoading(true); setNotice("");
    try {
      const updated = await classifyEmail(token, selected.id);
      setSelected(updated);
      const greeting = senderName(updated.sender).split("@")[0];
      const prefix = replyTone === "formal" ? `Bonjour ${greeting},\\n\\n` : replyTone === "short" ? "Bonjour,\\n\\n" : `Bonjour ${greeting},\\n\\n`;
      const body = updated.expected_action
        ? `Merci pour votre message.\\n\\nNous avons bien pris note de votre demande concernant : ${updated.expected_action}. Nous revenons vers vous dès que possible.`
        : "Merci pour votre message.\\n\\nNous en prenons bonne note et reviendrons vers vous si nécessaire.";
      setReply(`${prefix}${body}\\n\\n${replyTone === "formal" ? "Cordialement," : "Bien cordialement,"}`);
      setNotice("Proposition préparée : relis et modifie le texte avant tout envoi.");
    } catch (e) { setError(e instanceof Error ? e.message : "Génération impossible"); }
    finally { setLoading(false); }
  }

  const displayedCount = useMemo(() => `${emails.length} sur ${total}`, [emails.length, total]);

  if (!token) return (
    <main className="login-screen">
      <form className="login-card" onSubmit={handleLogin}>
        <div className="brand-mark"><Mail size={25}/></div>
        <p className="eyebrow">USTS · ASSISTANT MAIL</p>
        <h1>Votre messagerie,<br/>en toute simplicité.</h1>
        <p className="muted">Connectez-vous pour retrouver vos e-mails et leurs analyses IA.</p>
        <label>Adresse e-mail<input type="email" autoComplete="username" required value={emailAddress} onChange={e => setEmailAddress(e.target.value)} placeholder="vous@exemple.fr"/></label>
        <label>Mot de passe<input type="password" autoComplete="current-password" required value={password} onChange={e => setPassword(e.target.value)} placeholder="Votre mot de passe"/></label>
        {loginError && <div className="error-message"><AlertCircle size={16}/>{loginError}</div>}
        <button className="primary-button full" type="submit">Se connecter <ArrowDown size={16}/></button>
        <p className="login-foot">Connexion sécurisée à votre espace USTS</p>
      </form>
    </main>
  );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark"><Mail size={22}/></div><div><strong>USTS Mail</strong><small>Assistant intelligent</small></div></div>
        <button className={`nav-item ${section === "inbox" ? "active" : ""}`} onClick={() => { setSection("inbox"); setSelected(null); }}><Inbox size={18}/> Boîte de réception <span>{total}</span></button>
        <button className={`nav-item ${section === "priority" ? "active" : ""}`} onClick={() => { setSection("priority"); setSelected(null); }}><Star size={18}/> Prioritaires</button>
        <button className={`nav-item ${section === "review" ? "active" : ""}`} onClick={() => { setSection("review"); setSelected(null); }}><AlertCircle size={18}/> À vérifier</button>
        <div className="sidebar-label">VOTRE ESPACE</div>
        <button className="nav-item" onClick={() => { setCategory(""); setPriority(""); setStatus("traite"); setSection("inbox"); }}><Check size={18}/> Traités</button>
        <button className="nav-item" onClick={() => { setCategory(""); setPriority(""); setStatus("archive"); setSection("inbox"); }}><Archive size={18}/> Archivés</button>
        <div className="sidebar-bottom"><div className="user-avatar">{initials(emailAddress || "Utilisateur")}</div><div className="user-info"><strong>{emailAddress || "Compte connecté"}</strong><small>Compte connecté</small></div><button className="icon-button" title="Déconnexion" onClick={() => { sessionStorage.removeItem("usts_token"); setToken(""); setSelected(null); }}><LogOut size={17}/></button></div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumbs">Messagerie <span>/</span> <strong>{section === "priority" ? "Prioritaires" : section === "review" ? "À vérifier" : "Boîte de réception"}</strong></div>
          <div className="top-actions"><span className="connection-dot"/> Backend connecté <button className="icon-button" title="Actualiser" onClick={() => void refresh()}><RefreshCw size={17}/></button></div>
        </header>
        <div className={`workspace ${selected ? "with-detail" : ""}`}>
          <section className="inbox-panel">
            <div className="page-heading"><div><p className="eyebrow">VOTRE COURRIER</p><h1>{section === "priority" ? "Prioritaires" : section === "review" ? "À vérifier" : "Boîte de réception"}</h1><p className="muted">{total} message{total > 1 ? "s" : ""} dans votre boîte</p></div><button className="secondary-button" onClick={() => void refresh()}><RefreshCw size={15}/> Actualiser</button></div>
            {summary && <div className="summary-strip"><div className="summary-icon"><Sparkles size={18}/></div><div className="summary-copy"><strong>Votre résumé du jour</strong><p>{summary.overview || `${summary.total_emails} e-mails reçus aujourd’hui.`}</p></div><div className="summary-stat"><strong>{summary.total_emails}</strong><small>E-mails</small></div><div className="summary-stat priority-stat"><strong>{summary.high_priority_count}</strong><small>Prioritaires</small></div></div>}
            {summary && (summary as any).follow_ups && (summary as any).follow_ups.length > 0 && <div className="followups-box">
  <div className="followups-heading"><Clock3 size={16}/><strong>En attente de r?ponse</strong><span>{(summary as any).follow_ups.length}</span></div>
  {(summary as any).follow_ups.map((fu: any) => <button key={fu.id} className="followup-row" onClick={() => void openEmail(fu)}>
    <span className={"category-chip cat-" + (fu.category || "autre").replaceAll(" ", "-")}>{categoryLabels[fu.category] || fu.category}</span>
    <div className="followup-main"><strong>{fu.subject || "(Sans objet)"}</strong><small>{fu.sender}</small></div>
    <span className="followup-age">{fu.waiting_label}</span>
  </button>)}
</div>}
<div className="toolbar"><div className="search-box"><Search size={17}/><input aria-label="Rechercher" placeholder="Rechercher un e-mail…" value={search} onChange={e => setSearch(e.target.value)}/>{search && <button className="tiny-button" onClick={() => setSearch("")}><X size={14}/></button>}</div><select aria-label="Catégorie" value={category} onChange={e => setCategory(e.target.value)}><option value="">Toutes les catégories</option>{categories.map(c => <option key={c} value={c}>{categoryLabels[c]}</option>)}</select><select aria-label="Priorité" value={priority} onChange={e => setPriority(e.target.value)}><option value="">Toutes priorités</option><option value="1">Priorité haute</option><option value="2">Priorité normale</option><option value="3">Priorité basse</option></select><select aria-label="Statut" value={status} onChange={e => setStatus(e.target.value)}><option value="">Tous les statuts</option><option value="à traiter">À traiter</option><option value="à vérifier">À vérifier</option><option value="traite">Traités</option><option value="archive">Archivés</option></select></div>
            {error && <div className="error-banner"><AlertCircle size={16}/>{error}<button onClick={() => setError("")}><X size={14}/></button></div>}
            {notice && <div className="notice-banner"><Check size={16}/>{notice}<button onClick={() => setNotice("")}><X size={14}/></button></div>}
            <div className="list-heading"><span>MESSAGE</span><span>CATÉGORIE</span><span>DATE</span></div>
            <div className="email-list">
              {loading && <div className="empty-state"><RefreshCw className="spin" size={22}/> Chargement des e-mails…</div>}
              {!loading && emails.length === 0 && <div className="empty-state"><Inbox size={30}/><strong>Aucun e-mail trouvé</strong><span>Essayez de modifier les filtres.</span></div>}
              {!loading && emails.map(item => <button key={item.id} className={`email-row ${selected?.id === item.id ? "selected" : ""}`} onClick={() => void openEmail(item)}>
                <div className="sender-avatar">{initials(item.sender)}</div>
                <div className="email-main"><div className="email-meta"><strong>{senderName(item.sender)}</strong><span className={`priority-dot p${item.priority || 2}`} title={`Priorité ${item.priority || 2}`}/></div><strong className="email-subject">{item.subject || "(Sans objet)"}</strong><p>{item.summary || item.body?.slice(0, 110) || "Aucun aperçu disponible"}</p><div className="mobile-meta"><span className="category-chip">{categoryLabels[item.category || "autre"] || item.category}</span><span>{dateLabel(item.received_at)}</span></div></div>
                <div className="row-category"><span className={`category-chip cat-${(item.category || "autre").replaceAll(" ", "-")}`}>{categoryLabels[item.category || "autre"] || item.category}</span><small>{item.status || "nouveau"}</small></div><time>{dateLabel(item.received_at)}</time>
              </button>)}
            </div>
            <footer className="list-footer"><span>{displayedCount} e-mails</span><div><button className="icon-button" disabled={page <= 1} onClick={() => { setPage(page - 1); void load(token, page - 1); }}><ChevronLeft size={17}/></button><span>Page {page} / {totalPages}</span><button className="icon-button" disabled={page >= totalPages} onClick={() => { setPage(page + 1); void load(token, page + 1); }}><ChevronRight size={17}/></button></div></footer>
          </section>

          {selected && <section className="detail-panel">
            <div className="detail-toolbar"><button className="icon-button back-button" onClick={() => setSelected(null)}><ArrowLeft size={18}/></button><span>Lecture du message</span><div className="spacer"/><button className="icon-button" title="Marquer comme traité" onClick={() => void markProcessed()}><Check size={17}/></button><button className="icon-button" title="Archiver" onClick={() => void archiveSelected()}><Archive size={17}/></button></div>
            <div className="detail-content"><div className="detail-category"><span className="category-chip">{categoryLabels[selected.category || "autre"] || selected.category}</span><span className={`priority-label p${selected.priority || 2}`}>Priorité {selected.priority || 2}</span></div><h2>{selected.subject || "(Sans objet)"}</h2>
              <div className="sender-card"><div className="sender-avatar large">{initials(selected.sender)}</div><div><strong>{senderName(selected.sender)}</strong><p>{selected.sender}</p></div><time>{dateLabel(selected.received_at)}</time></div>
              <div className="detail-field"><label>Résumé IA</label><p>{selected.summary || "Aucun résumé disponible."}</p></div>
              {selected.expected_action && <div className="action-callout"><Clock3 size={17}/><div><strong>Action attendue</strong><p>{selected.expected_action}</p></div></div>}
              <div className="body-content"><label>Contenu du message</label><div className="message-body">{selected.body || "Le contenu de cet e-mail n’a pas été extrait."}</div></div>
              <div className="reply-box"><div className="reply-heading"><div className="reply-title"><Sparkles size={17}/><strong>Réponse assistée par IA</strong></div><span className="draft-badge">Brouillon</span></div><p className="muted">Générez une proposition, puis relisez et modifiez-la avant de l’utiliser.</p><label className="tone-label">Ton de la réponse<select value={replyTone} onChange={e => setReplyTone(e.target.value)}><option value="neutral">Neutre et professionnel</option><option value="formal">Formel</option><option value="short">Court et direct</option></select></label><textarea value={reply} onChange={e => setReply(e.target.value)} placeholder="Votre réponse apparaîtra ici. Vous pourrez la modifier…" rows={7}/><div className="reply-actions"><button className="secondary-button" onClick={() => void generateReplyAI()} disabled={loading}><Sparkles size={15}/>{loading ? "Préparation…" : "Générer une réponse"}</button><button className="primary-button" disabled={!reply.trim()} onClick={() => setNotice("Brouillon prêt à copier. Aucun e-mail n’a été envoyé.")} title="L’envoi Gmail sera activé après l’implémentation sécurisée de la route de réponse."><Send size={15}/> Préparer l’envoi</button></div></div>
            </div>
          </section>}
        </div>
      </main>
    </div>
  );
}
