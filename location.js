// location.js - the "Your location" bar used on the Crops and Buyers pages.
// It remembers the chosen location in the browser (localStorage), so the
// location you set on one page is still there on the next page.

(function () {
  const KEY = "fieldwatch_location";

  const DISTRICT_POINTS = {
    Chennai: [13.08, 80.27],
    Madurai: [9.92, 78.12],
    Thanjavur: [10.79, 79.14],
    Coimbatore: [11.0, 76.96],
    Ramanathapuram: [9.37, 78.83],
  };

  const gpsButton = document.getElementById("loc-gps");
  const districtSelect = document.getElementById("loc-district");
  const districtButton = document.getElementById("loc-district-go");
  const currentText = document.getElementById("loc-current");
  const message = document.getElementById("loc-status");
  if (!gpsButton || !districtSelect || !districtButton || !currentText) return;

  function readSaved() {
    try { return JSON.parse(localStorage.getItem(KEY)); } catch (error) { return null; }
  }

  function showMessage(text, isError) {
    message.textContent = text;
    message.hidden = !text;
    message.classList.toggle("fc-error", Boolean(isError));
  }

  function showCurrent() {
    const saved = readSaved();
    currentText.textContent = saved ? "Your location: " + saved.label : "No location chosen yet.";
  }

  function save(lat, lon, label) {
    try { localStorage.setItem(KEY, JSON.stringify({ lat: lat, lon: lon, label: label })); } catch (error) {}
    showMessage("");
    showCurrent();
  }

  gpsButton.addEventListener("click", function () {
    if (!navigator.geolocation) {
      showMessage("Your device does not support GPS here. Please choose a district.", true);
      return;
    }
    showMessage("Finding your location...");
    navigator.geolocation.getCurrentPosition(
      function (position) {
        const lat = position.coords.latitude.toFixed(4);
        const lon = position.coords.longitude.toFixed(4);
        save(lat, lon, "GPS (" + lat + ", " + lon + ")");
      },
      function () {
        showMessage("We could not get your location. Please allow location access, or choose a district.", true);
      },
      { enableHighAccuracy: false, timeout: 15000 }
    );
  });

  districtButton.addEventListener("click", function () {
    const name = districtSelect.value;
    save(DISTRICT_POINTS[name][0], DISTRICT_POINTS[name][1], name + " district");
  });

  showCurrent();   // when the page opens, show the location saved earlier
})();