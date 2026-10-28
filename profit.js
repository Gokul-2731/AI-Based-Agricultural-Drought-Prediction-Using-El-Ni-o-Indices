
const F = window.Fieldwatch;

const cropSelect = document.getElementById("profit-crop");
const areaInput = document.getElementById("profit-area");
const calculateButton = document.getElementById("calculate-profit");
const resultBox = document.getElementById("profit-result");
const statusBox = document.getElementById("profit-status");

const farm = F.getFarm();

if (farm.crop) cropSelect.value = farm.crop;
if (farm.area) areaInput.value = farm.area;

calculateButton.addEventListener("click", async function () {
  const location = F.getLocation();
  const crop = cropSelect.value;
  const area = Number(areaInput.value);

  if (!location) {
    F.notice(statusBox, "Complete the Forecast page first.", true,
      "forecast.html", "Open forecast");
    return;
  }

  if (!Number.isFinite(area) || area <= 0 || area > 1000) {
    F.notice(statusBox, "Enter an area between 0 and 1000 acres.", true);
    return;
  }

  F.saveFarm({ crop, area });
  calculateButton.disabled = true;
  resultBox.hidden = true;
  F.notice(statusBox, "Calculating estimate...", false);

  try {
    const data = await F.askServer("/api/profit", {
      lat: location.lat,
      lon: location.lon,
      crop,
      area
    });

    resultBox.replaceChildren();
    resultBox.append(F.make("h3", "", "Estimated farm result"));

    // Show the API result without assuming its exact field names.
    Object.entries(data.result).forEach(function ([key, value]) {
      const label = key.replaceAll("_", " ");
      const readableLabel = label.charAt(0).toUpperCase() + label.slice(1);
      const readableValue =
        typeof value === "number" ? value.toLocaleString("en-IN") : String(value);

      resultBox.append(
        F.make("p", "", readableLabel + ": " + readableValue)
      );
    });

    resultBox.append(F.make("p", "",
      data.note || "This is an estimate, not a guaranteed profit."));
    resultBox.hidden = false;
    F.notice(statusBox, "", false);
  } catch (error) {
    F.notice(statusBox, F.errorText(error), true);
  } finally {
    calculateButton.disabled = false;
  }
});
