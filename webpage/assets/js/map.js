const POINTS_URL =
  "https://penguin-b5dbf3c3.s3.eu-central-1.amazonaws.com/points.json";

(function ($) {
  let map = L.map("map", {
    scrollWheelZoom: false,
  });

  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map);

  $.ajax({
    dataType: "json",
    url: POINTS_URL,
    cache: false,
    success: function (data) {
      console.log(`fetched ${data.length} points`);
      if (data.length === 0) {
        return;
      }
      map.setView(data[data.length - 1].location, 13);

      for (const [i, p] of data.entries()) {
        const m = L.marker(p.location);
        if (i === data.length - 1) {
          // highlight last?
        }
        const popupContent = makePopupContent(p);
        m.bindPopup(popupContent).openPopup();
        m.addTo(map);
      }

      const path = extractPath(data);
      L.polyline(path, { color: "blue", opacity: 0.5 }).addTo(map);
    },
  });
})(jQuery);

function extractPath(points) {
  let path = [];
  for (const p of points) {
    path.push(p.location);
  }
  return path;
}

function makePopupContent(p) {
  return `<p>${p.timestamp.slice(0, 19)}</p>`;
}
