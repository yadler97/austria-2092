<h1>Welcome to SvelteKit</h1>
<p>Visit <a href="https://svelte.dev/docs/kit">svelte.dev/docs/kit</a> to read the documentation</p>


<script>
  import { onMount } from "svelte";
  import { scaleLinear } from "d3-scale";
  import { interpolateViridis } from "d3-scale-chromatic";
  import { base } from '$app/paths';

  let map;
  let geojsonLayer;
  let geojsonData;
  let currentMetric = "avg_age"; // default metric

  let selectedBundesland = "All";

  const bundeslandMap = {
    "1": "Burgenland",
    "2": "Kärnten",
    "3": "Niederösterreich",
    "4": "Oberösterreich",
    "5": "Salzburg",
    "6": "Steiermark",
    "7": "Tirol",
    "8": "Vorarlberg",
    "9": "Wien"
  };

  // Decode Umlaute properly
  function decodeUTF8(str) {
    return decodeURIComponent(escape(str));
  }

  function updateStyle(metric) {
    if (!geojsonData || !geojsonLayer) return;

    // Filter features based on selected Bundesland
    const filteredFeatures = geojsonData.features.filter(f => {
      const gId = f.properties?.g_id?.toString(); // force string
      const bl = gId ? bundeslandMap[gId[0]] : null;
      return selectedBundesland === "All" || bl === selectedBundesland;
    });

    console.log(filteredFeatures.length + " features after filtering for " + selectedBundesland);

    // Zoom to selected Bundesland
    if (filteredFeatures.length > 0) {
      const bounds = L.geoJSON(filteredFeatures).getBounds();
      map.fitBounds(bounds, { padding: [20, 20] });
    } else {
      map.setView([47.5, 14.5], 7);
    }

    // Use only filtered features to compute min/max
    const values = filteredFeatures
      .map(f => f.properties[metric])
      .filter(v => v !== null && v !== undefined);

    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);

    const colorScale = scaleLinear()
      .domain([minVal, maxVal])
      .range([0, 1]);

    // Apply styles
    geojsonLayer.setStyle(f => {
      const isVisible = filteredFeatures.includes(f);
      return {
        fillColor: isVisible ? interpolateViridis(colorScale(f.properties[metric])) : "#ccc",
        weight: 1,
        color: "white",
        dashArray: "2",
        fillOpacity: isVisible ? 0.8 : 0
      };
    });

    // Update legend
    const legendDiv = document.querySelector(".legend");
    if (legendDiv) {
      legendDiv.innerHTML = `<b>${metric === "avg_age" ? "Average Age" : "Population Change 2025"}</b><br>`;
      const gradient = document.createElement("div");
      gradient.style.height = "12px";
      gradient.style.width = "100px";
      gradient.style.background = `linear-gradient(to right, ${interpolateViridis(0)}, ${interpolateViridis(1)})`;
      gradient.style.margin = "5px 0";
      legendDiv.appendChild(gradient);
      legendDiv.innerHTML += `${minVal.toFixed(0)} &nbsp;&nbsp;&nbsp;&nbsp; ${maxVal.toFixed(0)}`;
    }

    // Update tooltips
    geojsonLayer.eachLayer(layer => {
        const f = layer.feature;
        const isActive = filteredFeatures.includes(f);

        // Set style
        layer.setStyle({
            fillColor: isActive ? interpolateViridis(colorScale(f.properties[metric])) : "#ccc",
            weight: 1,
            color: "white",
            dashArray: "2",
            fillOpacity: isActive ? 0.8 : 0.2
        });

        // Bind/unbind tooltip based on activity
        if (isActive) {
            const val = f.properties[metric];
            const formatted = val !== null && val !== undefined
            ? Number.isInteger(val) ? val.toLocaleString() : val.toFixed(1)
            : "n/a";

            layer.bindTooltip(`<b>${decodeUTF8(f.properties.g_name)}</b><br>${metric}: ${formatted}`);
        } else {
            layer.unbindTooltip();
        }
    });
  }


  onMount(async () => {
    const L = await import("leaflet");
    await import("leaflet/dist/leaflet.css");

    map = L.map("map").setView([47.5, 14.5], 7);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap &copy; CARTO'
    }).addTo(map);

    // Load GeoJSON as text to avoid encoding issues
    const geojsonText = await fetch(`${base}/municipalities.geojson`).then(r => r.text());
    geojsonData = JSON.parse(geojsonText);

    // normalize names
    geojsonData.features.forEach(f => {
      if (f.properties?.g_name) f.properties.g_name = f.properties.g_name.normalize("NFC");
    });

    // Add GeoJSON layer
    geojsonLayer = L.geoJSON(geojsonData, {
      style: f => ({ fillColor: "#fff", weight: 1, color: "white", fillOpacity: 0.8 }),
      onEachFeature: (f, layer) => {
        layer.bindTooltip(`<b>${decodeUTF8(f.properties.g_name)}</b><br>${currentMetric}: ${f.properties[currentMetric].toFixed(0)}`);
      }
    }).addTo(map);

    // Add legend
    const legend = L.control({ position: "bottomright" });
    legend.onAdd = () => {
      const div = L.DomUtil.create("div", "legend");
      return div;
    };
    legend.addTo(map);

    // initial style
    updateStyle(currentMetric);
  });

  function toggleMetric(metric) {
    currentMetric = metric;
    updateStyle(metric);
  }

  function selectBundesland(b) {
    selectedBundesland = b;
    updateStyle(currentMetric);
  }
</script>

<svelte:head>
  <meta charset="utf-8" />
</svelte:head>

<style>
  #map { height: 90vh; width: 100%; }
  .legend {
    line-height: 18px;
    color: #555;
    background: white;
    padding: 6px 8px;
    box-shadow: 0 0 5px rgba(0,0,0,0.3);
    font-size: 12px;
  }
  .toggle-buttons {
    margin: 10px;
  }
  .toggle-buttons button {
    margin-right: 10px;
    padding: 5px 10px;
    cursor: pointer;
  }
</style>

<div class="toggle-buttons">
  <button on:click={() => toggleMetric("avg_age")}>Average Age</button>
  <button on:click={() => toggleMetric("population_change_per_1000")}>Population Change 2025</button>
</div>

<select on:change={(e) => selectBundesland(e.target.value)}>
  <option value="All">All</option>
  <option value="Burgenland">Burgenland</option>
  <option value="Kärnten">Kärnten</option>
  <option value="Niederösterreich">Niederösterreich</option>
  <option value="Oberösterreich">Oberösterreich</option>
  <option value="Salzburg">Salzburg</option>
  <option value="Steiermark">Steiermark</option>
  <option value="Tirol">Tirol</option>
  <option value="Vorarlberg">Vorarlberg</option>
  <option value="Wien">Wien</option>
</select>

<div id="map"></div>
