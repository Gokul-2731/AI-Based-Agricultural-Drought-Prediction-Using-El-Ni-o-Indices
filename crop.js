
const F = window.Fieldwatch;

const cropSelect = document.getElementById("crop-select");
const areaInput = document.getElementById("land-area");
const suggestButton = document.getElementById("suggest-btn");
const resultBox = document.getElementById("suggest-result");
const statusBox = document.getElementById("crop-status");
const placeLine = document.getElementById("place-line");

// Restore the saved farm details when the page opens.
const farm = F.getFarm();
if (farm.crop) cropSelect.value = farm.crop;
if (farm.area) areaInput.value = farm.area;

const locationData = F.getLocation();

if (locationData) {
  placeLine.textContent = "Location: " + locationData.label;
  placeLine.hidden = false;
}

suggestButton.addEventListener("click", async function () {
  const crop = cropSelect.value;
  const area = Number(areaInput.value);
  const location = F.getLocation();

  if (!location) {
    F.notice(
      statusBox,
      "Please complete Step 1 (Forecast) first.",
      true,
      "forecast.html",
      "Open forecast"
    );
    return;
  }

  if (!Number.isFinite(area) || area <= 0 || area > 1000) {
    F.notice(statusBox, "Enter land area between 0 and 1000 acres.", true);
    return;
  }

  F.saveFarm({ crop: crop, area: area });
  suggestButton.disabled = true;
  F.notice(statusBox, "Finding suitable crop suggestions...", false);
  resultBox.hidden = true;

  try {
    const data = await F.askServer("/api/suggest", {
      lat: location.lat,
      lon: location.lon,
      area: area
    });

    resultBox.replaceChildren();

    const heading = F.make("h3", "", "Suggested crops");
    resultBox.append(heading);

    F.make("p", "", "District: " + data.forecast.district);
    resultBox.append(
      F.make("p", "", "Rainfall outlook: " +
        (data.forecast.percent_of_normal ?? "Unavailable") + "% of normal")
    );

    data.suggestions.forEach(function (item) {
      const card = F.make("div", "suggestion-card");
      card.append(F.make("h4", "", item.crop || item.name || "Crop option"));
      card.append(F.make("p", "", JSON.stringify(item)));
      resultBox.append(card);
    });

    resultBox.append(
      F.make("p", "", "These are estimates, not guaranteed farming advice.")
    );
    resultBox.hidden = false;
    F.notice(statusBox, "", false);

  } catch (error) {
    F.notice(statusBox, F.errorText(error), true);
  } finally {
    suggestButton.disabled = false;
  }
});
