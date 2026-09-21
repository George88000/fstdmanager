(function () {
  function getRoot() {
    return document.getElementById("modal-root");
  }

  function closeModal() {
    const root = getRoot();
    if (root) root.innerHTML = "";
    document.body.classList.remove("overflow-hidden");
  }

  function openModal(html, options) {
    const opts = options || {};
    const root = getRoot();
    if (!root) return;

    const wideClass = opts.wide ? " max-w-3xl" : " max-w-xl";
    root.innerHTML =
      '<div class="modal-overlay fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-navy-950/50 p-4 pt-[5vh]" id="modal-overlay">' +
      '<div class="modal-panel w-full rounded-xl bg-white shadow-2xl' +
      wideClass +
      '">' +
      html +
      "</div></div>";

    document.body.classList.add("overflow-hidden");

    const overlay = document.getElementById("modal-overlay");
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) closeModal();
    });

    root.querySelectorAll("[data-modal-close]").forEach(function (btn) {
      btn.addEventListener("click", closeModal);
    });
  }

  async function openModalFromUrl(url, options) {
    const response = await fetch(url, {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    if (!response.ok) return;
    openModal(await response.text(), options);
  }

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeModal();
  });

  document.addEventListener("click", function (e) {
    const trigger = e.target.closest("[data-modal-url]");
    if (!trigger) return;
    e.preventDefault();
    openModalFromUrl(trigger.dataset.modalUrl, {
      wide: trigger.dataset.modalWide === "true",
    });
  });

  window.FSTDModal = { openModal, closeModal, openModalFromUrl };
})();
