
const cropSelect = document.getElementById("buyer-crop");
const findButton = document.getElementById("find-buyers");
const results = document.getElementById("buyer-results");

findButton.addEventListener("click", function () {
  const crop = cropSelect.value;
  results.replaceChildren();

  const heading = document.createElement("h2");
  heading.textContent = "Selling options for " + crop;
  results.appendChild(heading);

  const options = [
    {
      name: "Tamil Nadu Uzhavar Sandhai",
      description:
        "Check local farmers' markets and ask about suitable selling facilities.",
      url: "https://www.tnagrisnet.tn.gov.in/"
    },
    {
      name: "e-NAM National Agriculture Market",
      description:
        "Explore participating agricultural markets and available trading services.",
      url: "https://www.enam.gov.in/"
    },
    {
      name: "Local regulated market",
      description:
        "Contact your nearest regulated market to ask about crop sales and current requirements.",
      url: "https://www.tn.gov.in/"
    }
  ];

  options.forEach(function (option) {
    const card = document.createElement("div");
    const title = document.createElement("h3");
    const description = document.createElement("p");
    const link = document.createElement("a");

    title.textContent = option.name;
    description.textContent = option.description;
    link.textContent = "Visit website";
    link.href = option.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";

    card.append(title, description, link);
    results.appendChild(card);
  });

  const note = document.createElement("p");
  note.textContent =
    "These are market information channels, not confirmed individual buyers. Availability and crop acceptance may vary.";
  results.appendChild(note);
});
