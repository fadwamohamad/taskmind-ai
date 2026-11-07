// TaskMind AI frontend (vanilla JS). No API keys here; same-origin calls only.

const TaskMindI18n = (() => {
  const STORAGE_KEY = "taskmind-lang";
  const SUPPORTED_LANGUAGES = ["ar", "en", "fr"];
  const DEFAULT_LANGUAGE = "en";

  const TRANSLATIONS = {
    en: {
      tagline: "Turn meeting notes into actionable tasks.",
      notesTitle: "Meeting notes",
      notesLabel: "Paste meeting notes or unstructured text",
      notesPlaceholder: "Paste your meeting notes here...",
      notesHelp: "Arabic, English, and French notes are supported. Task content keeps its original language.",
      extractBtn: "Extract Tasks",
      extracting: "Extracting...",
      draftsTitle: "Review extracted tasks",
      draftsEmpty: "No extracted tasks yet. Run extraction to review drafts before saving.",
      savedTitle: "Saved tasks",
      savedEmpty: "No saved tasks yet.",
      languageLabel: "Language",
      statusEmptyNotes: "Please enter meeting notes first.",
      statusExtracting: "Extracting tasks...",
      statusExtracted: "{count} task(s) extracted. Review before saving.",
      statusNoTasks: "No actionable tasks found in these notes.",
      statusTitleRequired: "Title is required before saving.",
      statusSaved: "Task saved.",
      statusRemoved: "Draft removed.",
      statusMarkedDone: "Task marked done.",
      statusDeleted: "Task deleted.",
      statusLoadFailed: "Could not load saved tasks.",
      errValidation: "Please check the notes or task fields and try again.",
      errNotConfigured: "AI service is not configured right now. Please try again later.",
      errExtractionFailed: "AI extraction failed. Please try again.",
      errNotFound: "That task no longer exists.",
      errGeneric: "Something went wrong. Please try again.",
      errSaveFailed: "Could not save task.",
      errUpdateFailed: "Could not update task.",
      errDeleteFailed: "Could not delete task.",
      errExtractFailed: "Extraction failed.",
      titleLabel: "Title",
      detailsLabel: "Details",
      assigneeLabel: "Assignee",
      priorityLabel: "Priority",
      dueDateLabel: "Due date",
      languageFieldLabel: "Language",
      saveBtn: "Save task",
      saving: "Saving...",
      removeBtn: "Remove",
      markDone: "Mark done",
      deleteBtn: "Delete",
      deleteConfirm: "Are you sure you want to delete this task? This action cannot be undone.",
      low: "Low",
      medium: "Medium",
      high: "High",
      todo: "Todo",
      done: "Done",
      assigneePrefix: "Assignee:",
      duePrefix: "Due:",
      heroKicker: "AI task extraction",
      heroTitle: "Turn meeting notes into done.",
      heroSubtitle: "Paste any meeting notes in Arabic, English, or French. Review what AI found, then save only what matters.",
      stepPaste: "Paste notes",
      stepExtract: "Extract tasks",
      stepSave: "Review & save",
      examplesTitle: "Try an example",
      example1: "Sprint planning: Alice will write the API documentation by 2026-11-20. Bob will review the pull request by 2026-11-22.",
      example2: "We need to update the budget before Friday. No owner was named, but please prepare the weekly status update.",
      example3: "Urgent: fix the login crash first. Medium priority: update onboarding. Low priority: rename dashboard labels.",
      draftsSub: "Edit each card, then save what you keep.",
      savedSub: "Your saved actions across sessions.",
      footNote: "Built for clarity — your notes stay on this device, tasks keep their original language.",
    },
    ar: {
      tagline: "حوّل ملاحظات الاجتماع إلى مهام قابلة للتنفيذ.",
      notesTitle: "ملاحظات الاجتماع",
      notesLabel: "الصق ملاحظات الاجتماع أو أي نص غير منظم",
      notesPlaceholder: "الصق ملاحظات الاجتماع هنا...",
      notesHelp: "يتم دعم الملاحظات بالعربية والإنجليزية والفرنسية. يبقى محتوى المهام بلغة المصدر الأصلية.",
      extractBtn: "استخراج المهام",
      extracting: "جارٍ الاستخراج...",
      draftsTitle: "مراجعة المهام المستخرجة",
      draftsEmpty: "لا توجد مهام مستخرجة بعد. نفّذ الاستخراج لمراجعة المسودات قبل الحفظ.",
      savedTitle: "المهام المحفوظة",
      savedEmpty: "لا توجد مهام محفوظة بعد.",
      languageLabel: "اللغة",
      statusEmptyNotes: "الرجاء إدخال ملاحظات الاجتماع أولاً.",
      statusExtracting: "جارٍ استخراج المهام...",
      statusExtracted: "تم استخراج {count} مهمة. راجع قبل الحفظ.",
      statusNoTasks: "لا توجد مهام قابلة للتنفيذ في هذه الملاحظات.",
      statusTitleRequired: "العنوان مطلوب قبل الحفظ.",
      statusSaved: "تم حفظ المهمة.",
      statusRemoved: "تمت إزالة المسودة.",
      statusMarkedDone: "تم تعليم المهمة كمنتهية.",
      statusDeleted: "تم حذف المهمة.",
      statusLoadFailed: "تعذر تحميل المهام المحفوظة.",
      errValidation: "الرجاء التحقق من الملاحظات أو حقول المهام ثم المحاولة مجدداً.",
      errNotConfigured: "خدمة الذكاء الاصطناعي غير مهيأة الآن. الرجاء المحاولة لاحقاً.",
      errExtractionFailed: "فشل استخراج المهام. الرجاء المحاولة مجدداً.",
      errNotFound: "تلك المهمة لم تعد موجودة.",
      errGeneric: "حدث خطأ ما. الرجاء المحاولة مجدداً.",
      errSaveFailed: "تعذر حفظ المهمة.",
      errUpdateFailed: "تعذر تحديث المهمة.",
      errDeleteFailed: "تعذر حذف المهمة.",
      errExtractFailed: "فشل الاستخراج.",
      titleLabel: "العنوان",
      detailsLabel: "التفاصيل",
      assigneeLabel: "المسؤول",
      priorityLabel: "الأولوية",
      dueDateLabel: "تاريخ الاستحقاق",
      languageFieldLabel: "اللغة",
      saveBtn: "حفظ المهمة",
      saving: "جارٍ الحفظ...",
      removeBtn: "إزالة",
      markDone: "تعليم كمنتهية",
      deleteBtn: "حذف",
      deleteConfirm: "هل أنت متأكد من حذف هذه المهمة؟ لا يمكن التراجع عن هذا الإجراء.",
      low: "منخفضة",
      medium: "متوسطة",
      high: "عالية",
      todo: "للتنفيذ",
      done: "منتهية",
      assigneePrefix: "المسؤول:",
      duePrefix: "الاستحقاق:",
      heroKicker: "استخراج المهام بالذكاء الاصطناعي",
      heroTitle: "حوّل ملاحظات الاجتماع إلى إنجاز.",
      heroSubtitle: "الصق أي ملاحظات اجتماع بالعربية أو الإنجليزية أو الفرنسية. راجع ما وجده الذكاء الاصطناعي ثم احفظ المهم فقط.",
      stepPaste: "لصق الملاحظات",
      stepExtract: "استخراج المهام",
      stepSave: "مراجعة وحفظ",
      examplesTitle: "جرّب مثالاً",
      example1: "تخطيط السبرنت: ستكتب أليس توثيق API بحلول 2026-11-20. سيراجع بوب طلب السحب بحلول 2026-11-22.",
      example2: "يجب تحديث الميزانية قبل الجمعة. لم يُسمَّ مسؤول، لكن جهّز تحديث الحالة الأسبوعي.",
      example3: "عاجل: أصلح تعطل تسجيل الدخول أولاً. أولوية متوسطة: حدّث الإعداد. أولوية منخفضة: أعد تسمية لوحة التحكم.",
      draftsSub: "حرّر كل بطاقة ثم احفظ ما تبقيه.",
      savedSub: "إجراءاتك المحفوظة عبر الجلسات.",
      footNote: "مصمم للوضوح — تبقى ملاحظاتك على هذا الجهاز، وتحتفظ المهام بلغتها الأصلية.",
    },
    fr: {
      tagline: "Transformez vos notes de réunion en tâches actionnables.",
      notesTitle: "Notes de réunion",
      notesLabel: "Collez vos notes de réunion ou tout texte non structuré",
      notesPlaceholder: "Collez vos notes de réunion ici...",
      notesHelp: "Notes en arabe, anglais et français prises en charge. Le contenu des tâches conserve sa langue d'origine.",
      extractBtn: "Extraire les tâches",
      extracting: "Extraction...",
      draftsTitle: "Vérifiez les tâches extraites",
      draftsEmpty: "Aucune tâche extraite pour le moment. Lancez l'extraction pour vérifier avant d'enregistrer.",
      savedTitle: "Tâches enregistrées",
      savedEmpty: "Aucune tâche enregistrée pour le moment.",
      languageLabel: "Langue",
      statusEmptyNotes: "Veuillez d'abord saisir vos notes de réunion.",
      statusExtracting: "Extraction des tâches...",
      statusExtracted: "{count} tâche(s) extraite(s). Vérifiez avant d'enregistrer.",
      statusNoTasks: "Aucune tâche actionnable trouvée dans ces notes.",
      statusTitleRequired: "Le titre est requis avant l'enregistrement.",
      statusSaved: "Tâche enregistrée.",
      statusRemoved: "Brouillon supprimé.",
      statusMarkedDone: "Tâche marquée comme terminée.",
      statusDeleted: "Tâche supprimée.",
      statusLoadFailed: "Impossible de charger les tâches enregistrées.",
      errValidation: "Veuillez vérifier les notes ou les champs puis réessayer.",
      errNotConfigured: "Le service IA n'est pas configuré pour le moment. Veuillez réessayer plus tard.",
      errExtractionFailed: "Échec de l'extraction. Veuillez réessayer.",
      errNotFound: "Cette tâche n'existe plus.",
      errGeneric: "Un problème est survenu. Veuillez réessayer.",
      errSaveFailed: "Impossible d'enregistrer la tâche.",
      errUpdateFailed: "Impossible de mettre à jour la tâche.",
      errDeleteFailed: "Impossible de supprimer la tâche.",
      errExtractFailed: "Échec de l'extraction.",
      titleLabel: "Titre",
      detailsLabel: "Détails",
      assigneeLabel: "Assigné à",
      priorityLabel: "Priorité",
      dueDateLabel: "Date d'échéance",
      languageFieldLabel: "Langue",
      saveBtn: "Enregistrer la tâche",
      saving: "Enregistrement...",
      removeBtn: "Retirer",
      markDone: "Marquer comme terminée",
      deleteBtn: "Supprimer",
      deleteConfirm: "Voulez-vous vraiment supprimer cette tâche ? Cette action est irréversible.",
      low: "Basse",
      medium: "Moyenne",
      high: "Haute",
      todo: "À faire",
      done: "Terminée",
      assigneePrefix: "Assigné :",
      duePrefix: "Échéance :",
      heroKicker: "Extraction de tâches IA",
      heroTitle: "Transformez vos notes en résultats.",
      heroSubtitle: "Collez vos notes en arabe, anglais ou français. Vérifiez les résultats puis enregistrez l'essentiel.",
      stepPaste: "Coller les notes",
      stepExtract: "Extraire les tâches",
      stepSave: "Vérifier et enregistrer",
      examplesTitle: "Essayer un exemple",
      example1: "Sprint : Alice rédigera la doc API d'ici 2026-11-20. Bob reliera la PR d'ici 2026-11-22.",
      example2: "Le budget doit être mis à jour avant vendredi. Aucun responsable, mais préparer le point hebdomadaire.",
      example3: "Urgent : corriger le bug de connexion. Priorité moyenne : onboarding. Priorité basse : renommer le tableau de bord.",
      draftsSub: "Modifiez chaque carte puis enregistrez l'essentiel.",
      savedSub: "Vos actions enregistrées.",
      footNote: "Conçu pour la clarté — vos notes restent sur cet appareil, les tâches gardent leur langue.",
    },
  };

  function isSupported(lang) {
    return SUPPORTED_LANGUAGES.includes(lang);
  }

  function resolveLanguage(stored) {
    return isSupported(stored) ? stored : DEFAULT_LANGUAGE;
  }

  function directionFor(lang) {
    return resolveLanguage(lang) === "ar" ? "rtl" : "ltr";
  }

  function readPreferredLanguage(storage) {
    try {
      return resolveLanguage(storage.getItem(STORAGE_KEY));
    } catch (err) {
      return DEFAULT_LANGUAGE;
    }
  }

  function persistLanguage(storage, lang) {
    const resolved = resolveLanguage(lang);
    try {
      storage.setItem(STORAGE_KEY, resolved);
    } catch (err) {}
    return resolved;
  }

  function applyDocumentLanguage(doc, lang) {
    const resolved = resolveLanguage(lang);
    doc.documentElement.lang = resolved;
    doc.documentElement.dir = directionFor(resolved);
    return resolved;
  }

  function translate(lang, key, params) {
    const resolved = resolveLanguage(lang);
    let text = (TRANSLATIONS[resolved] && TRANSLATIONS[resolved][key]) || TRANSLATIONS[DEFAULT_LANGUAGE][key] || key;
    if (params) {
      for (const name of Object.keys(params)) {
        text = text.replace(`{${name}}`, String(params[name]));
      }
    }
    return text;
  }

  return {
    STORAGE_KEY,
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
    TRANSLATIONS,
    isSupported,
    resolveLanguage,
    directionFor,
    readPreferredLanguage,
    persistLanguage,
    applyDocumentLanguage,
    translate,
  };
})();

if (typeof window !== "undefined") {
  window.TaskMindI18n = TaskMindI18n;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = TaskMindI18n;
}

if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", () => {
    const notesInput = document.getElementById("notesInput");
    const extractBtn = document.getElementById("extractBtn");
    const statusMsg = document.getElementById("statusMsg");
    const draftsEl = document.getElementById("drafts");
    const draftsEmpty = document.getElementById("draftsEmpty");
    const savedEl = document.getElementById("savedTasks");
    const savedEmpty = document.getElementById("savedEmpty");
    const languageSelect = document.getElementById("languageSelect");
    const examplesRow = document.getElementById("examplesRow");

    let drafts = [];
    let currentLanguage = TaskMindI18n.readPreferredLanguage(localStorage);

    function t(key, params) {
      return TaskMindI18n.translate(currentLanguage, key, params);
    }

    function setStatus(message, kind) {
      statusMsg.textContent = message || "";
      statusMsg.className = kind ? `status-msg ${kind}` : "status-msg";
    }

    function el(tag, props) {
      const node = document.createElement(tag);
      if (props) {
        for (const key of Object.keys(props)) {
          if (key === "label" || key === "id") {
            node.setAttribute(key, props[key]);
          } else {
            node[key] = props[key];
          }
        }
      }
      return node;
    }

    function textEl(tag, text) {
      const node = el(tag, {});
      node.textContent = text;
      return node;
    }

    async function apiFetch(url, options) {
      let response;
      try {
        response = await fetch(url, options);
      } catch {
        throw new Error(t("errGeneric"));
      }
      if (response.status === 422) {
        throw new Error(t("errValidation"));
      }
      if (response.status === 503) {
        throw new Error(t("errNotConfigured"));
      }
      if (response.status === 502) {
        throw new Error(t("errExtractionFailed"));
      }
      if (response.status === 404) {
        throw new Error(t("errNotFound"));
      }
      if (!response.ok) {
        throw new Error(t("errGeneric"));
      }
      if (response.status === 204) return null;
      return response.json();
    }

    function prioritySelect(value) {
      const select = el("select", {});
      const options = ["low", "medium", "high"];
      const current = value || "medium";
      for (const opt of options) {
        const option = el("option", { value: opt });
        option.textContent = t(opt);
        if (opt === current) option.selected = true;
        select.append(option);
      }
      return select;
    }

    function draftCard(draft, index) {
      const card = el("article", { className: "task-card" });

      const titleLabel = textEl("label", t("titleLabel"));
      titleLabel.setAttribute("for", `draft-title-${index}`);
      const titleInput = el("input", { type: "text", id: `draft-title-${index}` });
      titleInput.value = draft.title || "";
      titleInput.addEventListener("input", () => { draft.title = titleInput.value; });
      card.append(titleLabel, titleInput);

      const detailsLabel = textEl("label", t("detailsLabel"));
      detailsLabel.setAttribute("for", `draft-details-${index}`);
      const detailsInput = el("textarea", { id: `draft-details-${index}`, rows: "3" });
      detailsInput.value = draft.details || "";
      detailsInput.addEventListener("input", () => { draft.details = detailsInput.value; });
      card.append(detailsLabel, detailsInput);

      const row2 = el("div", { className: "row two" });
      const assigneeLabel = textEl("label", t("assigneeLabel"));
      assigneeLabel.setAttribute("for", `draft-assignee-${index}`);
      const assigneeInput = el("input", { type: "text", id: `draft-assignee-${index}` });
      assigneeInput.value = draft.assignee || "";
      assigneeInput.addEventListener("input", () => { draft.assignee = assigneeInput.value || null; });
      const assigneeWrap = el("div", {});
      assigneeWrap.append(assigneeLabel, assigneeInput);

      const priorityLabel = textEl("label", t("priorityLabel"));
      priorityLabel.setAttribute("for", `draft-priority-${index}`);
      const priorityInput = prioritySelect(draft.priority || "medium");
      priorityInput.id = `draft-priority-${index}`;
      priorityInput.addEventListener("change", () => { draft.priority = priorityInput.value; });
      const priorityWrap = el("div", {});
      priorityWrap.append(priorityLabel, priorityInput);
      row2.append(assigneeWrap, priorityWrap);

      const row3 = el("div", { className: "row two" });
      const dateLabel = textEl("label", t("dueDateLabel"));
      dateLabel.setAttribute("for", `draft-date-${index}`);
      const dateInput = el("input", { type: "date", id: `draft-date-${index}` });
      dateInput.value = draft.due_date || "";
      dateInput.addEventListener("input", () => { draft.due_date = dateInput.value || null; });
      const dateWrap = el("div", {});
      dateWrap.append(dateLabel, dateInput);

      const langWrap = el("div", {});
      const langLabel = textEl("label", t("languageFieldLabel"));
      const langValue = textEl("span", draft.language || "unknown");
      langValue.className = "badge";
      langWrap.append(langLabel, langValue);
      row3.append(dateWrap, langWrap);
      card.append(row2, row3);

      const actions = el("div", { className: "card-actions" });
      const saveBtn = el("button", { type: "button" });
      saveBtn.textContent = t("saveBtn");
      const removeBtn = el("button", { type: "button", className: "secondary" });
      removeBtn.textContent = t("removeBtn");
      actions.append(saveBtn, removeBtn);
      card.append(actions);

      saveBtn.addEventListener("click", async () => {
        const title = titleInput.value.trim();
        if (!title) {
          setStatus(t("statusTitleRequired"), "error");
          draft.title = titleInput.value;
          return;
        }
        const assignee = assigneeInput.value.trim() || null;
        const dueDate = dateInput.value || null;
        const priority = priorityInput.value || "medium";
        saveBtn.disabled = true;
        saveBtn.textContent = t("saving");
        try {
          await apiFetch("/api/tasks", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              title,
              details: detailsInput.value,
              assignee,
              priority,
              due_date: dueDate,
              language: draft.language || "unknown",
            }),
          });
          drafts = drafts.filter((_, i) => i !== index);
          setStatus(t("statusSaved"), "success");
          renderDrafts();
          await loadSaved();
        } catch (err) {
          setStatus(err.message || t("errSaveFailed"), "error");
          saveBtn.disabled = false;
          saveBtn.textContent = t("saveBtn");
        }
      });

      removeBtn.addEventListener("click", () => {
        drafts = drafts.filter((_, i) => i !== index);
        renderDrafts();
        setStatus(t("statusRemoved"), "");
      });

      return card;
    }

    function renderDrafts() {
      draftsEl.replaceChildren();
      draftsEmpty.textContent = drafts.length ? "" : t("draftsEmpty");
      drafts.forEach((draft, index) => {
        draftsEl.append(draftCard(draft, index));
      });
    }

    function savedCard(task) {
      const card = el("article", { className: task.status === "done" ? "task-card done" : "task-card" });
      const title = textEl("div", task.title || "");
      title.className = "task-title";

      const details = textEl("p", task.details || "");
      details.className = "help-text";

      const meta = el("div", { className: "meta" });
      const priorityBadge = textEl("span", t(task.priority || "medium"));
      priorityBadge.className = `badge badge-${task.priority || "medium"}`;
      const statusBadge = textEl("span", t(task.status || "todo"));
      statusBadge.className = `badge badge-${task.status || "todo"}`;
      const languageBadge = textEl("span", task.language || "unknown");
      languageBadge.className = "badge";
      meta.append(priorityBadge, statusBadge, languageBadge);
      if (task.assignee) meta.append(textEl("span", `${t("assigneePrefix")} ${task.assignee}`));
      if (task.due_date) meta.append(textEl("span", `${t("duePrefix")} ${task.due_date}`));

      card.append(title, details, meta);

      const actions = el("div", { className: "card-actions" });
      if (task.status !== "done") {
        const doneBtn = el("button", { type: "button" });
        doneBtn.textContent = t("markDone");
        doneBtn.addEventListener("click", async () => {
          doneBtn.disabled = true;
          try {
            await apiFetch(`/api/tasks/${task.id}`, {
              method: "PATCH",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ status: "done" }),
            });
            setStatus(t("statusMarkedDone"), "success");
            await loadSaved();
          } catch (err) {
            setStatus(err.message || t("errUpdateFailed"), "error");
            doneBtn.disabled = false;
          }
        });
        actions.append(doneBtn);
      }

      const deleteBtn = el("button", { type: "button", className: "danger" });
      deleteBtn.textContent = t("deleteBtn");
      deleteBtn.addEventListener("click", async () => {
        if (!window.confirm(t("deleteConfirm"))) return;
        deleteBtn.disabled = true;
        try {
          await apiFetch(`/api/tasks/${task.id}`, { method: "DELETE" });
          setStatus(t("statusDeleted"), "success");
          await loadSaved();
        } catch (err) {
          setStatus(err.message || t("errDeleteFailed"), "error");
          deleteBtn.disabled = false;
        }
      });
      actions.append(deleteBtn);
      card.append(actions);
      return card;
    }

    async function loadSaved() {
      const tasks = await apiFetch("/api/tasks", { method: "GET" });
      savedEl.replaceChildren();
      savedEmpty.textContent = tasks?.length ? "" : t("savedEmpty");
      if (Array.isArray(tasks)) {
        tasks.forEach((task) => savedEl.append(savedCard(task)));
      }
    }

    function applyStaticTranslations() {
      document.querySelectorAll("[data-i18n]").forEach((node) => {
        const key = node.getAttribute("data-i18n");
        if (key) node.textContent = t(key);
      });
      document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
        const key = node.getAttribute("data-i18n-placeholder");
        if (key) node.setAttribute("placeholder", t(key));
      });
      if (extractBtn && !extractBtn.disabled) {
        extractBtn.textContent = t("extractBtn");
      }
      renderExamples();
    }

    function renderExamples() {
      if (!examplesRow) return;
      const keys = ["example1", "example2", "example3"];
      const buttons = examplesRow.querySelectorAll("[data-example]");
      buttons.forEach((btn, idx) => {
        const key = btn.getAttribute("data-example") || keys[idx];
        btn.textContent = t(key);
        btn.onclick = () => {
          notesInput.value = t(key);
          notesInput.focus();
          setStatus("", "");
        };
      });
    }

    function setLanguage(lang) {
      currentLanguage = TaskMindI18n.applyDocumentLanguage(document, lang);
      TaskMindI18n.persistLanguage(localStorage, currentLanguage);
      if (languageSelect) languageSelect.value = currentLanguage;
      applyStaticTranslations();
      renderDrafts();
      loadSaved().catch(() => {
        setStatus(t("statusLoadFailed"), "error");
      });
    }

    languageSelect.addEventListener("change", () => {
      setLanguage(languageSelect.value);
    });

    extractBtn.addEventListener("click", async () => {
      const text = notesInput.value.trim();
      if (!text) {
        setStatus(t("statusEmptyNotes"), "error");
        return;
      }
      extractBtn.disabled = true;
      extractBtn.textContent = t("extracting");
      setStatus(t("statusExtracting"), "loading");
      try {
        const data = await apiFetch("/api/extract", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text }),
        });
        drafts = Array.isArray(data.tasks) ? data.tasks : [];
        renderDrafts();
        if (!drafts.length) {
          setStatus(t("statusNoTasks"), "");
        } else {
          setStatus(t("statusExtracted", { count: drafts.length }), "success");
        }
      } catch (err) {
        setStatus(err.message || t("errExtractFailed"), "error");
      } finally {
        extractBtn.disabled = false;
        extractBtn.textContent = t("extractBtn");
      }
    });

    setLanguage(currentLanguage);
  });
}
