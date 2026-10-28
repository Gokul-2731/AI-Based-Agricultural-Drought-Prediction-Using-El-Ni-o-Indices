// layout.js - shared by EVERY page. It builds:
//   1. the header and footer
//   2. the progress bar and the Back / Next buttons of the 6-step journey
//   3. the crop drop-down lists
//   4. a small toolbox (window.Fieldwatch) used by the other scripts
// To change a step name or add a step, edit the STEPS list. Every page updates.

(function () {
  // ---------- 1. The 6 steps of the journey ----------
  const STEPS = [
    { file: "forecast.html", title: "Forecast" },
    { file: "crop.html",     title: "Crop" },
    { file: "profit.html",   title: "Profit or loss" },
    { file: "prices.html",   title: "Prices" },
    { file: "buyers.html",   title: "Buyers" },
    { file: "payment.html",  title: "Payment" },
  ];

  // The crops (same keys as profit.py). Change them here and every list updates.
  const CROPS = [
    ["rice", "Rice (paddy)"], ["groundnut", "Groundnut"],
    ["millets", "Millets (ragi, cholam, kambu)"], ["maize", "Maize"],
    ["cotton", "Cotton"], ["sugarcane", "Sugarcane"],
    ["pulses", "Pulses (black gram, green gram)"],
  ];

  // ---------- 2. The toolbox other scripts can use ----------
  const SERVER = "http://127.0.0.1:5000";
  const F = {
    SERVER: SERVER,
    // The location chosen in Step 1 (saved in the browser)
    getLocation: function () {
      try { return JSON.parse(localStorage.getItem("fieldwatch_location")); } catch (e) { return null; }
    },
    // The crop and land area chosen in Step 2
    getFarm: function () {
      try { return JSON.parse(localStorage.getItem("fieldwatch_farm")) || {}; } catch (e) { return {}; }
    },
    saveFarm: function (farm) {
      try { localStorage.setItem("fieldwatch_farm", JSON.stringify(farm)); } catch (e) {}
    },
    // 12000 -> "Rs 12,000"   -3000 -> "-Rs 3,000"
    money: function (n) { return (n < 0 ? "-" : "") + "Rs " + Math.abs(n).toLocaleString("en-IN"); },
    // Make an element with text (safe: text is never run as code)
    make: function (tag, className, text) {
      const el = document.createElement(tag);
      if (className) el.className = className;
      if (text !== undefined) el.textContent = text;
      return el;
    },
    // Show a message in a box, with an optional link at the end
    notice: function (box, text, isError, href, linkText) {
      box.replaceChildren(document.createTextNode(text));
      if (href) {
        const a = F.make("a", "", linkText);
        a.href = href;
        box.append(" ", a);
      }
      box.hidden = !text;
      box.classList.toggle("fc-error", Boolean(isError));
    },
    // Ask the Flask server (app.py) and return its answer
    askServer: async function (path, params) {
      const response = await fetch(SERVER + path + "?" + new URLSearchParams(params).toString());
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "The server could not answer.");
      return data;
    },
    errorText: function (error) {
      return error instanceof TypeError ? "Cannot reach the server. Start it with: python app.py" : error.message;
    },
  };
  window.Fieldwatch = F;

  // ---------- 3. Header and footer ----------
  const header = document.getElementById("site-header");
  if (header) {
    header.innerHTML =
      '<div class="header-inner">' +
        '<a class="brand" href="index.html" aria-label="Fieldwatch home">' +
          '<span class="brand-mark" aria-hidden="true">F</span><span>Fieldwatch</span></a>' +
        '<div class="header-tools">' +
          // FEATURE BUTTON: language chooser (to be connected later)
          '<label for="language-select" class="visually-hidden-label">Language</label>' +
          '<select class="field language-select" id="language-select" data-feature="language">' +
            '<option value="en">English</option><option value="ta">தமிழ்</option><option value="hi">हिन्दी</option>' +
          "</select>" +
        "</div>" +
      "</div>";
  }

  const footer = document.getElementById("site-footer");
  if (footer) {
    footer.innerHTML =
      '<div class="section-wrap footer-inner">' +
        '<a class="brand footer-brand" href="index.html"><span class="brand-mark" aria-hidden="true">F</span><span>Fieldwatch</span></a>' +
        "<p>A project concept for agricultural drought research.</p></div>";
  }

  // ---------- 4. Progress bar and Back / Next buttons (step pages only) ----------
  let current = window.location.pathname.split("/").pop() || "index.html";
  const index = STEPS.findIndex(function (s) { return s.file === current; });
  const main = document.querySelector("main");

  if (index >= 0 && main) {
    // Progress bar
    const bar = F.make("nav", "progress");
    bar.setAttribute("aria-label", "Progress");
    bar.append(F.make("p", "progress-text", "Step " + (index + 1) + " of " + STEPS.length + ": " + STEPS[index].title));
    const list = F.make("ol", "progress-list");
    STEPS.forEach(function (step, i) {
      const item = F.make("li", i < index ? "done" : i === index ? "current" : "");
      if (i === index) item.setAttribute("aria-current", "step");
      item.append(F.make("span", "progress-num", i < index ? "✓" : String(i + 1)));
      item.append(F.make("span", "progress-label", step.title));
      list.append(item);
    });
    bar.append(list);
    main.prepend(bar);

    // Back and Next buttons
    const nav = F.make("div", "step-nav");
    const back = F.make("a", "btn btn-outline", index === 0 ? "← Home" : "← Back: " + STEPS[index - 1].title);
    back.href = index === 0 ? "index.html" : STEPS[index - 1].file;
    const last = index === STEPS.length - 1;
    const next = F.make("a", "btn", last ? "Finish: back to home" : "Next: " + STEPS[index + 1].title + " →");
    next.href = last ? "index.html" : STEPS[index + 1].file;
    nav.append(back, next);
    (document.querySelector(".page-body") || main).append(nav);
  }

  // ---------- 5. Fill the crop drop-down lists ----------
  // <select data-crops data-first="All crops" data-remember> becomes a crop list.
  // data-remember = pre-select the crop the farmer chose in Step 2.
  document.querySelectorAll("select[data-crops]").forEach(function (select) {
    select.replaceChildren();
    const first = F.make("option", "", select.dataset.first || "Select a crop");
    first.value = "";
    select.append(first);
    CROPS.forEach(function (crop) {
      const option = F.make("option", "", crop[1]);
      option.value = crop[0];
      select.append(option);
    });
    if (select.hasAttribute("data-remember") && F.getFarm().crop) select.value = F.getFarm().crop;
  });
})();