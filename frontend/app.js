/* Chat local servido por python -m agente.web. */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const messages = $("messages");
  const welcome = $("welcome");
  const form = $("composer");
  const input = $("input");
  const sendBtn = $("sendBtn");
  const newChatBtn = $("newChatBtn");
  const SESSION_KEY = "factory_method_sessao";
  let thread = null;
  let busy = true;
  let sessaoId = recuperarSessao();

  function novaSessao() {
    const id = globalThis.crypto?.randomUUID?.() || `${Date.now()}_${Math.random().toString(36).slice(2)}`;
    return `web_${id}`;
  }

  function guardarSessao(id) {
    try { sessionStorage.setItem(SESSION_KEY, id); } catch { /* A conversa segue em memoria nesta aba. */ }
  }

  function recuperarSessao() {
    let id;
    try { id = sessionStorage.getItem(SESSION_KEY); } catch { /* Armazenamento pode estar indisponivel. */ }
    if (!id || !/^web_[A-Za-z0-9_-]{1,60}$/.test(id)) id = novaSessao();
    guardarSessao(id);
    return id;
  }

  function status(texto, falha = false) {
    $("connectionStatus").textContent = texto;
    $("statusDot").classList.toggle("is-error", falha);
  }

  function controles() {
    sendBtn.disabled = busy || input.value.trim().length === 0;
    newChatBtn.disabled = busy;
    form.setAttribute("aria-busy", String(busy));
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
  }

  input.addEventListener("input", controles);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      if (!busy) form.requestSubmit();
    }
  });

  function garantirThread() {
    if (!thread) {
      welcome.hidden = true;
      thread = document.createElement("div");
      thread.className = "thread";
      messages.appendChild(thread);
    }
    return thread;
  }

  function rolar() { messages.scrollTo({ top: messages.scrollHeight, behavior: "smooth" }); }

  // Renderiza uma parte simples de Markdown usando somente nos de texto.
  // HTML vindo do estudante ou do modelo nunca e inserido como HTML executavel.
  function textoInline(elemento, texto) {
    const padrao = /\*\*([^*]+)\*\*|`([^`]+)`/g;
    let inicio = 0;
    for (const trecho of texto.matchAll(padrao)) {
      elemento.appendChild(document.createTextNode(texto.slice(inicio, trecho.index)));
      const no = document.createElement(trecho[1] ? "strong" : "code");
      no.textContent = trecho[1] || trecho[2];
      elemento.appendChild(no);
      inicio = trecho.index + trecho[0].length;
    }
    elemento.appendChild(document.createTextNode(texto.slice(inicio)));
  }

  function renderizarResposta(elemento, texto) {
    const linhas = texto.split("\n");
    let i = 0;
    while (i < linhas.length) {
      const linha = linhas[i];
      const cerca = linha.trim().match(/^```(.*)$/);
      if (cerca) {
        const codigo = [];
        i++;
        while (i < linhas.length && !/^```\s*$/.test(linhas[i].trim())) codigo.push(linhas[i++]);
        if (i < linhas.length) i++;
        const bloco = document.createElement("div");
        bloco.className = "code-block";
        const legenda = document.createElement("div");
        legenda.className = "code-label";
        legenda.textContent = cerca[1].trim().slice(0, 40) || "Código";
        const pre = document.createElement("pre");
        const code = document.createElement("code");
        code.textContent = codigo.join("\n");
        pre.appendChild(code);
        bloco.append(legenda, pre);
        elemento.appendChild(bloco);
        continue;
      }
      if (!linha.trim()) { i++; continue; }
      const titulo = linha.match(/^#{1,6}\s+(.+)$/);
      if (titulo) {
        const h = document.createElement("h3");
        textoInline(h, titulo[1]);
        elemento.appendChild(h);
        i++;
        continue;
      }
      const item = linha.match(/^\s*(?:([-*])|\d+\.)\s+(.+)$/);
      if (item) {
        const lista = document.createElement(item[1] ? "ul" : "ol");
        const padrao = item[1] ? /^\s*[-*]\s+(.+)$/ : /^\s*\d+\.\s+(.+)$/;
        while (i < linhas.length) {
          const proximo = linhas[i].match(padrao);
          if (!proximo) break;
          const li = document.createElement("li");
          textoInline(li, proximo[1]);
          lista.appendChild(li);
          i++;
        }
        elemento.appendChild(lista);
        continue;
      }
      const paragrafo = [linhas[i++]];
      while (i < linhas.length && linhas[i].trim() &&
             !/^\s*(?:```|#{1,6}\s|[-*]\s|\d+\.\s)/.test(linhas[i])) paragrafo.push(linhas[i++]);
      const p = document.createElement("p");
      textoInline(p, paragrafo.join("\n"));
      elemento.appendChild(p);
    }
  }

  function mensagem(texto, usuario = false, falha = false) {
    const row = document.createElement("div");
    row.className = `msg ${usuario ? "msg-user" : "msg-ai"}${falha ? " msg-error" : ""}`;
    const avatar = document.createElement("span");
    avatar.className = `avatar ${usuario ? "avatar-user" : "avatar-ai"}`;
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = usuario ? "Você" : "IA";
    const corpo = document.createElement("div");
    corpo.className = "msg-body";
    if (!usuario) {
      const nome = document.createElement("div");
      nome.className = "msg-name";
      nome.textContent = falha ? "Não foi possível concluir" : "Factory IA · Equipe pedagógica";
      corpo.appendChild(nome);
    }
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    if (usuario || falha) bubble.textContent = texto;
    else renderizarResposta(bubble, texto);
    corpo.appendChild(bubble);
    row.append(avatar, corpo);
    garantirThread().appendChild(row);
    rolar();
  }

  function indicador() {
    const row = document.createElement("div");
    row.className = "msg msg-ai";
    row.id = "typingRow";
    row.innerHTML = '<span class="avatar avatar-ai" aria-hidden="true">IA</span>' +
      '<div class="msg-body"><div class="msg-name">Preparando sua resposta…</div>' +
      '<div class="typing" role="status" aria-label="A IA está respondendo"><span></span><span></span><span></span></div></div>';
    garantirThread().appendChild(row);
    rolar();
  }

  async function api(caminho, opcoes = {}) {
    let resposta;
    try {
      resposta = await fetch(caminho, { ...opcoes, headers: { "Content-Type": "application/json" } });
    } catch {
      throw new Error("Não foi possível conectar ao chat local. Verifique se o servidor está ativo e abra a interface pelo endereço dele.");
    }
    const dados = await resposta.json().catch(() => ({}));
    if (!resposta.ok) throw new Error(dados.erro || "Não foi possível concluir a solicitação. Tente novamente.");
    return dados;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const pergunta = input.value.trim();
    if (!pergunta || busy) return;
    busy = true;
    mensagem(pergunta, true);
    input.value = "";
    controles();
    status("A IA está respondendo. O modelo local pode levar alguns instantes.");
    indicador();
    try {
      const dados = await api("/api/chat", { method: "POST", body: JSON.stringify({ pergunta, sessao_id: sessaoId }) });
      if (typeof dados.resposta !== "string" || !dados.resposta.trim()) throw new Error("O servidor retornou uma resposta vazia. Tente novamente.");
      $("typingRow")?.remove();
      mensagem(dados.resposta);
      status("Modelo local · As respostas podem conter imprecisões; confira o material da disciplina.");
    } catch (erro) {
      $("typingRow")?.remove();
      mensagem(erro.message, false, true);
      if (!input.value.trim()) input.value = pergunta;
      status("Não foi possível concluir o envio. Sua pergunta está disponível para tentar novamente.", true);
    } finally {
      busy = false;
      controles();
      input.focus();
    }
  });

  function limparTela() {
    thread?.remove();
    thread = null;
    welcome.hidden = false;
    input.value = "";
    messages.scrollTo({ top: 0 });
  }

  const newChatDialog = $("newChatDialog");
  newChatBtn.addEventListener("click", () => {
    if (busy || newChatDialog.open) return;
    newChatDialog.returnValue = "cancel";
    newChatDialog.showModal();
  });

  newChatDialog.addEventListener("close", async () => {
    if (newChatDialog.returnValue !== "confirm" || busy) return;
    busy = true;
    controles();
    try {
      await api(`/api/sessoes/${encodeURIComponent(sessaoId)}`, { method: "DELETE" });
      sessaoId = novaSessao();
      guardarSessao(sessaoId);
      limparTela();
      status("Novo chat · O contexto anterior foi apagado.");
      input.focus();
    } catch (erro) {
      status(`Não foi possível iniciar um novo chat: ${erro.message}`, true);
    } finally {
      busy = false;
      controles();
    }
  });

  async function iniciar() {
    controles();
    try {
      if (location.protocol === "file:") throw new Error("Abra esta interface em http://127.0.0.1:8000 após iniciar python -m agente.web.");
      const [info, historico] = await Promise.all([
        api("/api/info"), api(`/api/sessoes/${encodeURIComponent(sessaoId)}`),
      ]);
      $("topbarAgentName").textContent = info.padrao;
      $("topbarAgentName").title = `Modelo local: ${info.modelo}`;
      for (const turno of historico.turnos || []) {
        if (typeof turno.pergunta === "string" && typeof turno.resposta === "string") {
          mensagem(turno.pergunta, true);
          mensagem(turno.resposta);
        }
      }
      status("Modelo local · As respostas podem conter imprecisões; confira o material da disciplina.");
    } catch (erro) {
      status(erro.message, true);
    } finally {
      busy = false;
      controles();
    }
  }

  iniciar();
})();
