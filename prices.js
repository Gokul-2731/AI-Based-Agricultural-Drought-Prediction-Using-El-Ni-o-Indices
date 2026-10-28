
const prices = [
  { crop: "Rice", price: 2350 },
  { crop: "Groundnut", price: 6500 },
  { crop: "Millets", price: 3200 },
  { crop: "Maize", price: 2200 },
  { crop: "Cotton", price: 7200 },
  { crop: "Sugarcane", price: 350 },
  { crop: "Pulses", price: 7000 }
];

const table = document.getElementById("prices-list");
const searchInput = document.getElementById("crop-search");
const status = document.getElementById("price-status");

function displayPrices(searchText = "") {
  table.replaceChildren();

  const filteredPrices = prices.filter(function (item) {
    return item.crop.toLowerCase().includes(searchText.toLowerCase());
  });

  if (filteredPrices.length === 0) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");

    cell.colSpan = 2;
    cell.textContent = "No matching crops found.";

    row.appendChild(cell);
    table.appendChild(row);
  } else {
    filteredPrices.forEach(function (item) {
      const row = document.createElement("tr");
      const cropCell = document.createElement("td");
      const priceCell = document.createElement("td");

      cropCell.textContent = item.crop;
      priceCell.textContent =
        "₹" + item.price.toLocaleString("en-IN") + " / quintal";

      row.append(cropCell, priceCell);
      table.appendChild(row);
    });
  }

  status.textContent = "Showing " + filteredPrices.length + " crop(s).";
}

searchInput.addEventListener("input", function () {
  displayPrices(searchInput.value);
});

displayPrices();
