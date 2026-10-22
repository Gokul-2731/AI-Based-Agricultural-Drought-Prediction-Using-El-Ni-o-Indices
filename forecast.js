// forecast.js - talks to your Flask backend (app.py) and shows the 3-month forecast.
// Make sure `python app.py` is running before you click the buttons.

const API_BASE = "http://127.0.0.1:5000";

// Centre points of the 5 starter districts (same as app.py), used if GPS is not available
const DISTRICT_POINTS = {
  Chennai: [13.08, 80.27],
  Madurai: [9.92, 78.12],
  Thanjavur: [10.79, 79.14],
  Coimbatore: [11.0, 76.96],
  Ramanathapuram: [9.37, 78.83],
};

const gpsButton = document.getElementById("fc-gps");
const districtSelect = document.getElementById("fc-district");
const districtButton = document.getElementById("fc-district-go");
const statusBox = document.getElementById("fc-status");
const resultBox = document.getElementById("fc-result");

function setStatus(message, isError) {
  statusBox.textContent = message;
  statusBox.hidden = !message;
  statusBox.classList.toggle("fc-error", Boolean(isError));
}

function setBusy(busy) {
  gpsButton.disabled = busy;
  districtButton.disabled = busy;
}

async function loadForecast(lat, lon) {
  window.lastLocation = { lat: lat, lon: lon };   // profit.js uses this
  resultBox.hidden = true;
  setBusy(true);
  setStatus("Getting the latest satellite weather data and running the forecast. This can take up to 20 seconds...");
  try {
    const response = await fetch(`${API_BASE}/api/forecast?lat=${lat}&lon=${lon}`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "The server could not make a forecast.");
    }
    showResult(data);
    setStatus("");
  } catch (error) {
    const serverDown = error instanceof TypeError;
    setStatus(
      serverDown
        ? "Cannot reach the forecast server. Start it with: python app.py"
        : error.message,
      true
    );
  } finally {
    setBusy(false);
  }
}

function riskLevel(percent) {
  if (percent === null || percent === undefined) return "unknown";
  if (percent < 60) return "high";
  if (percent < 80) return "moderate";
  if (percent <= 120) return "normal";
  return "wet";
}

function showResult(data) {
  const percent = data.percent_of_normal;
  const level = riskLevel(percent);
  const biggest = Math.max(data.predicted_rain_mm, data.normal_rain_mm, 1);

  document.getElementById("fc-place").textContent = data.district + " district";
  document.getElementById("fc-months").textContent = data.forecast_months.join(", ");
  document.getElementById("fc-pred-value").textContent = data.predicted_rain_mm + " mm";
  document.getElementById("fc-norm-value").textContent = data.normal_rain_mm + " mm";
  document.getElementById("fc-pred-bar").style.width = (100 * data.predicted_rain_mm / biggest) + "%";
  document.getElementById("fc-norm-bar").style.width = (100 * data.normal_rain_mm / biggest) + "%";
  document.getElementById("fc-percent").textContent =
    percent === null ? "n/a" : percent + "% of normal";

  const risk = document.getElementById("fc-risk");
  risk.textContent = data.risk;
  risk.className = "fc-risk fc-risk-" + level;

  document.getElementById("fc-basis").textContent =
    "Based on weather up to " + data.based_on.latest_complete_month +
    " and the El Nino index (" + data.based_on.el_nino_index + ").";
  document.getElementById("fc-note").textContent = data.note;
  resultBox.hidden = false;
  resultBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

gpsButton.addEventListener("click", () => {
  if (!navigator.geolocation) {
    setStatus("Your device does not support GPS here. Please choose a district below.", true);
    return;
  }
  setStatus("Finding your location...");
  setBusy(true);
  navigator.geolocation.getCurrentPosition(
    (position) => {
      loadForecast(position.coords.latitude.toFixed(4), position.coords.longitude.toFixed(4));
    },
    () => {
      setBusy(false);
      setStatus("We could not get your location. Please allow location access, or choose a district below.", true);
    },
    { enableHighAccuracy: false, timeout: 15000 }
  );
});

districtButton.addEventListener("click", () => {
  const point = DISTRICT_POINTS[districtSelect.value];
  loadForecast(point[0], point[1]);
});