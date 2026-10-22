// profit.js - makes the "Check profit or loss" and "Suggest better crops" buttons work.
// It uses the location of your last forecast, so the farmer gets a forecast first.
// Everything is inside (function () { ... })(); so its names never clash with
// the names in script.js and forecast.js.

(function () {
  const SERVER = "http://127.0.0.1:5000";

  // 1. Find the things on the page we need
  const cropSelect = document.getElementById("crop-select");
  const areaInput = document.getElementById("land-area");
  const profitButton = document.getElementById("profit-btn");
  const suggestButton = document.getElementById("suggest-btn");
  const message = document.getElementById("profit-status");
  const profitBox = document.getElementById("profit-result");
  const suggestBox = document.getElementById("suggest-result");

  // 2. Small helper functions
  function showMessage(text, isError) {
    message.textContent = text;
    message.hidden = !text;
    message.classList.toggle("fc-error", Boolean(isError));
  }

  // 12000 -> "Rs 12,000"   and   -3000 -> "-Rs 3,000"
  function money(amount) {
    const sign = amount < 0 ? "-" : "";
    return sign + "Rs " + Math.abs(amount).toLocaleString("en-IN");
  }

  // Make an HTML element with some text in it (safe: text is never run as code)
  function make(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function setBusy(busy) {
    profitButton.disabled = busy;
    suggestButton.disabled = busy;
  }

  // 3. Read and check what the farmer typed
  function readInputs(needCrop) {
    if (!window.lastLocation) {
      showMessage("Please get your forecast first: use your location or pick a district in the forecast section above.", true);
      document.getElementById("forecast").scrollIntoView({ behavior: "smooth" });
      return null;
    }
    const area = parseFloat(areaInput.value);
    if (!(area > 0)) {
      showMessage("Please enter your land area in acres (for example 2).", true);
      return null;
    }
    if (needCrop && !cropSelect.value) {
      showMessage("Please choose a crop first.", true);
      return null;
    }
    return { area: area, lat: window.lastLocation.lat, lon: window.lastLocation.lon };
  }

  // 4. Ask the Flask server and return its answer
  async function askServer(path, params) {
    const address = SERVER + path + "?" + new URLSearchParams(params).toString();
    const response = await fetch(address);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "The server could not answer.");
    return data;
  }

  function handleError(error) {
    const serverDown = error instanceof TypeError;
    showMessage(serverDown ? "Cannot reach the server. Start it with: python app.py" : error.message, true);
  }

  // 5. Show the profit or loss result
  function showProfit(data) {
    const r = data.result;
    profitBox.replaceChildren();

    profitBox.append(make("h4", "", r.crop_name + " on " + r.area_acres + " acre(s)"));

    // The big number: chance of profit, with a word so colour is not the only clue
    let level = "pr-poor";
    let word = "Likely loss";
    if (r.chance_of_profit_percent >= 70) { level = "pr-good"; word = "Likely profit"; }
    else if (r.chance_of_profit_percent >= 40) { level = "pr-mixed"; word = "Uncertain"; }
    profitBox.append(make("p", "pr-chance " + level, r.chance_of_profit_percent + "% chance of profit: " + word));

    profitBox.append(make("p", "", "Expected profit: " + money(r.expected_profit) +
      " (most likely between " + money(r.likely_range[0]) + " and " + money(r.likely_range[1]) + ")"));

    // A small table of the numbers behind it
    const table = make("table", "pr-table");
    const rows = [
      ["Cost", money(r.cost)],
      ["Expected income", money(r.expected_income)],
      ["Expected harvest", r.expected_harvest_q + " quintals"],
      ["Time to harvest", r.growing_days + " days"],
    ];
    rows.forEach(function (row) {
      const tr = make("tr");
      tr.append(make("th", "", row[0]), make("td", "", row[1]));
      table.append(tr);
    });
    profitBox.append(table);

    // Explain how the rain forecast affected the answer
    const change = r.yield_change_from_rain_percent;
    let rainText = "The rain forecast for " + data.forecast.district + " is " +
      data.forecast.percent_of_normal + "% of normal. ";
    rainText += change < 0
      ? "This crop is affected by low rain, so the harvest may drop by about " + Math.abs(change) + "%."
      : "This should not reduce the harvest of this crop.";
    profitBox.append(make("p", "pr-note", rainText));
    profitBox.append(make("p", "pr-note", data.note));
    profitBox.hidden = false;
  }

  // 6. Show the crop suggestions
  function showSuggestions(data) {
    suggestBox.replaceChildren();
    suggestBox.append(make("h4", "", "Crops that suit the forecast for " + data.forecast.district));

    const list = make("ol", "pr-list");
    data.suggestions.forEach(function (s) {
      const item = make("li");
      item.append(make("strong", "", s.crop_name));
      item.append(make("span", "", " : " + s.chance_of_profit_percent + "% chance of profit, expected profit " +
        money(s.expected_profit) + ", about " + s.growing_days + " days to harvest."));
      list.append(item);
    });
    suggestBox.append(list);
    suggestBox.append(make("p", "pr-note", "Ranked by expected profit for each month of growing. " + data.note));
    suggestBox.hidden = false;
  }

  // 7. Connect the buttons
  profitButton.addEventListener("click", async function () {
    const input = readInputs(true);
    if (!input) return;
    profitBox.hidden = true;
    setBusy(true);
    showMessage("Calculating...");
    try {
      const data = await askServer("/api/profit", {
        lat: input.lat, lon: input.lon, crop: cropSelect.value, area: input.area,
      });
      showProfit(data);
      showMessage("");
    } catch (error) {
      handleError(error);
    } finally {
      setBusy(false);
    }
  });

  suggestButton.addEventListener("click", async function () {
    const input = readInputs(false);
    if (!input) return;
    suggestBox.hidden = true;
    setBusy(true);
    showMessage("Finding the best crops...");
    try {
      const data = await askServer("/api/suggest", { lat: input.lat, lon: input.lon, area: input.area });
      showSuggestions(data);
      showMessage("");
    } catch (error) {
      handleError(error);
    } finally {
      setBusy(false);
    }
  });
})();