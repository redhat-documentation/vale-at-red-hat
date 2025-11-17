/* Clean copied code like Antora:
  */
(function () {
  // Fixed regex to remove trailing spaces before callouts
  const CALLOUT_TAIL = /[ \t]*(\(\d+\)|<\d+>)[ \t]*(?=\n|$)/gm;

  const PROMPTS = [
    /^\s*\$+\s+/,                 // $ echo hi
    /^\s*#\s+/,                   // # apt install
    /^\s*>\s+/,                   // > node -v
    /^\s*PS [^>]*>\s+/,           // PS C:\> Get-Item
    /^\s*[A-Za-z]:\\[^>]*>\s+/,   // C:\> dir
  ];

  function isConsoleLike(lang) {
    if (!lang) return false;
    lang = String(lang).toLowerCase();
    return (
      lang.includes("console") ||
      lang.includes("shell") ||
      lang.includes("shell-session") ||
      lang.includes("terminal") ||
      lang.includes("powershell") ||
      lang.includes("dos")
    );
  }

  function languageOf(code) {
    const c = code.getAttribute("class") || "";
    const w = (code.parentElement?.className || "") + " " + (code.closest(".highlight")?.className || "");
    const m = (c + " " + w).match(/language-([A-Za-z0-9_-]+)/);
    return m ? m[1] : "";
  }

  function stripPromptOnce(line) {
    for (const rx of PROMPTS) {
      if (rx.test(line)) return line.replace(rx, "");
    }
    return null;
  }

  function cleanFromCodeNode(code) {
    const clone = code.cloneNode(true);
    clone.querySelectorAll(".conum").forEach((n) => n.remove());
    let text = clone.innerText;

    const lang = languageOf(code);
    if (isConsoleLike(lang)) {
      const lines = text.split(/\r?\n/);
      const commands = [];
      for (let line of lines) {
        const stripped = stripPromptOnce(line);
        if (stripped != null && stripped.trim().length) commands.push(stripped);
      }
      text = commands.join("\n");
    }

    // Remove callouts and any trailing whitespace on each line
    return text.replace(CALLOUT_TAIL, "").replace(/[ \t]+$/gm, "");
  }

  function codeForButton(btn) {
    const pre =
      btn.closest("pre") ||
      btn.closest(".highlight")?.querySelector("pre") ||
      btn.parentElement?.querySelector("pre") ||
      null;
    return pre ? pre.querySelector("code") || pre : null;
  }

  function install(root) {
    root.querySelectorAll(".md-clipboard").forEach((btn) => {
      if (btn.dataset.antoraCopyPatched) return;
      btn.dataset.antoraCopyPatched = "1";

      btn.addEventListener("click", () => {
        const code = codeForButton(btn);
        if (!code) return;
        const clean = cleanFromCodeNode(code);

        // ClipboardJS path
        const origText = btn.getAttribute("data-clipboard-text");
        const origTarget = btn.getAttribute("data-clipboard-target");
        btn.setAttribute("data-clipboard-text", clean);
        if (origTarget != null) btn.removeAttribute("data-clipboard-target");
        setTimeout(() => {
          if (origText == null) btn.removeAttribute("data-clipboard-text");
          else btn.setAttribute("data-clipboard-text", origText);
          if (origTarget != null) btn.setAttribute("data-clipboard-target", origTarget);
        }, 600);

        // Clipboard API path: intercept exactly one write
        if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
          const origWrite = navigator.clipboard.writeText.bind(navigator.clipboard);
          let used = false;
          navigator.clipboard.writeText = (text) => {
            used = true;
            const p = origWrite(clean);
            p.finally(() => { navigator.clipboard.writeText = origWrite; });
            return p;
          };
          setTimeout(() => { if (!used) navigator.clipboard.writeText = origWrite; }, 1000);
        }

        // execCommand fallback: one-shot filter
        const onCopy = (ev) => {
          try {
            if (ev.clipboardData) {
              ev.clipboardData.setData("text/plain", clean);
              ev.preventDefault();
            }
          } catch (_) {}
        };
        document.addEventListener("copy", onCopy, { once: true, capture: true });
      }, true); // don't cancel; keep Material's feedback
    });
  }

  if (window.document$?.subscribe) {
    window.document$.subscribe(() => install(document));
  } else {
    document.addEventListener("DOMContentLoaded", () => install(document));
  }
})();