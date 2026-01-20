<script>
  import { onMount } from "svelte";
  import { scaleLinear } from "d3-scale";
  import { interpolateViridis, interpolateRdBu } from "d3-scale-chromatic";
  import { base } from '$app/paths';

  let map;
  let geojsonLayer;
  let geojsonData;
  let currentMetric = "avg_age"; 
  let selectedBundesland = "All";
  let searchQuery = "";
  let searchResults = [];
  let selectedGemeindeFeature = null;

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

  function decodeUTF8(str) {
    return decodeURIComponent(escape(str));
  }

  function updateStyle(metric) {
    if (!geojsonData || !geojsonLayer) return;

    // Filter features based on selected Bundesland
    const filteredFeatures = geojsonData.features.filter(f => {
      const gId = f.properties?.g_id?.toString();
      const bl = gId ? bundeslandMap[gId[0]] : null;
      return selectedBundesland === "All" || bl === selectedBundesland;
    });

    // Zoom to selection
    if (selectedGemeindeFeature) {
      // Keep zoom on selected Gemeinde
      const layer = geojsonLayer.getLayers().find(l => l.feature === selectedGemeindeFeature);
      if (layer) {
        const bounds = layer.getBounds ? layer.getBounds() : layer.getLatLng().toBounds(1000);
        map.fitBounds(bounds, { padding: [20, 20] });
      }
    } else if (filteredFeatures.length > 0) {
      // Default zoom to Bundesland or all features
      const bounds = L.geoJSON(filteredFeatures).getBounds();
      map.fitBounds(bounds, { padding: [20, 20] });
    } else {
      map.setView([47.5, 14.5], 7);
    }

    // Get values
    const values = filteredFeatures
      .map(f => f.properties[metric])
      .filter(v => v !== null && v !== undefined);

    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);

    // Create color scale
    let colorScale;
    if (metric === "population_change_per_1000") {
      // diverging + log scale
      const posMax = Math.max(maxVal, 0);
      const negMin = Math.min(minVal, 0);

      colorScale = val => {
        if (val === 0) return 0.5; // middle
        if (val > 0) {
          return 0.5 + 0.5 * Math.log1p(val) / Math.log1p(posMax); // 0.5..1
        } else {
          return 0.5 - 0.5 * Math.log1p(-val) / Math.log1p(-negMin); // 0..0.5
        }
      };
    } else {
      // sequential for avg_age
      colorScale = scaleLinear().domain([minVal, maxVal]).range([0, 1]);
    }

    // Apply styles
    geojsonLayer.setStyle(f => {
      const val = f.properties[metric];
      const t = Math.max(0, Math.min(1, colorScale(val))); // clamp to [0,1]
      const fillColor =
        metric === "population_change_per_1000"
          ? interpolateRdBu(1 - t) // red=negative, blue=positive
          : interpolateViridis(t);

      const isVisible = filteredFeatures.includes(f);

      return {
        fillColor: isVisible ? fillColor : "#ccc",
        weight: 1,
        color: "white",
        dashArray: "2",
        fillOpacity: isVisible ? 0.8 : 0.2
      };
    });

    // Update legend
    const legendDiv = document.querySelector(".legend");
    if (legendDiv) {
      legendDiv.innerHTML = `<b>${metric === "avg_age" ? "Average Age" : "Population Change 2025"}</b><br>`;
      const gradient = document.createElement("div");
      gradient.style.height = "12px";
      gradient.style.width = "100px";
      gradient.style.margin = "5px 0";

      if (metric === "population_change_per_1000") {
        gradient.style.background = `linear-gradient(to right, ${interpolateRdBu(0)}, ${interpolateRdBu(0.5)}, ${interpolateRdBu(1)})`;
      } else {
        gradient.style.background = `linear-gradient(to right, ${interpolateViridis(0)}, ${interpolateViridis(1)})`;
      }

      legendDiv.appendChild(gradient);
      legendDiv.innerHTML += `${minVal.toFixed(0)} &nbsp;&nbsp;&nbsp;&nbsp; ${maxVal.toFixed(0)}`;
    }

    // Update tooltips
    geojsonLayer.eachLayer(layer => {
      const f = layer.feature;
      const val = f.properties[metric];
      const isActive = filteredFeatures.includes(f);

      const t = Math.max(0, Math.min(1, colorScale(val)));
      const fillColor =
        metric === "population_change_per_1000"
          ? interpolateRdBu(1 - t)
          : interpolateViridis(t);

      layer.setStyle({
        fillColor: isActive ? fillColor : "#ccc",
        weight: 1,
        color: "white",
        dashArray: "2",
        fillOpacity: isActive ? 0.8 : 0.2
      });

      if (isActive) {
        const formatted =
          val !== null && val !== undefined
            ? Number.isInteger(val)
              ? val.toLocaleString()
              : val.toFixed(1)
            : "n/a";
        layer.bindTooltip(`<b>${decodeUTF8(f.properties.g_name)}</b><br>${metric}: ${formatted}`);
      } else {
        layer.unbindTooltip();
      }
    });
  }

  // Search function
  function searchGemeinde() {
    if (!searchQuery || !geojsonData) {
      searchResults = [];
      return;
    }

    const q = searchQuery.toLowerCase();
    searchResults = geojsonData.features
      .filter(f => {
        const gId = f.properties.id?.toString();

        const isFiveDigitString = /^[0-9]{5}$/.test(gId);
        const isVienneseDistrict = Number(gId) >= 901 && Number(gId) <= 923;

        return (
          f.properties.name.toLowerCase().includes(q) &&
          (isFiveDigitString || isVienneseDistrict)
        );
      })
      .slice(0, 5); // top 5 suggestions
  }

  function selectGemeinde(f) {
    searchQuery = f.properties.name;
    searchResults = [];
    selectedGemeindeFeature = f; // store it

    const layer = geojsonLayer.getLayers().find(l => l.feature === f);
    if (layer) {
      const bounds = layer.getBounds ? layer.getBounds() : layer.getLatLng().toBounds(1000);
      map.fitBounds(bounds, { padding: [20, 20] });
      layer.openTooltip();
    }
  }

  onMount(async () => {
    const L = await import("leaflet");
    await import("leaflet/dist/leaflet.css");

    map = L.map("map").setView([47.5, 14.5], 7);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap &copy; CARTO'
    }).addTo(map);

    const geojsonText = await fetch(`${base}/municipalities.geojson`).then(r => r.text());
    geojsonData = JSON.parse(geojsonText);

    geojsonData.features.forEach(f => {
      if (f.properties?.g_name) f.properties.g_name = f.properties.g_name.normalize("NFC");
    });

    geojsonLayer = L.geoJSON(geojsonData, {
      style: f => ({ fillColor: "#fff", weight: 1, color: "white", fillOpacity: 0.8 }),
      onEachFeature: (f, layer) => {
        layer.bindTooltip(`<b>${decodeUTF8(f.properties.g_name)}</b><br>${currentMetric}: ${f.properties[currentMetric].toFixed(0)}`);
      }
    }).addTo(map);

    const legend = L.control({ position: "bottomright" });
    legend.onAdd = () => {
      const div = L.DomUtil.create("div", "legend");
      return div;
    };
    legend.addTo(map);

    updateStyle(currentMetric);
  });

  function toggleMetric(metric) {
    currentMetric = metric;
    updateStyle(metric);
  }

  function selectBundesland(b) {
    selectedGemeindeFeature = null; // clear selected Gemeinde
    selectedBundesland = b;
    updateStyle(currentMetric);
  }
</script>

<svelte:head>
  <meta charset="utf-8" />
</svelte:head>

<style>
  #map { height: 80vh; width: 100%; }
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

  .search-bar {
    margin: 10px;
    position: relative;
  }
  .search-bar input {
    width: 200px;
    padding: 5px;
  }
  .search-results {
    position: absolute;
    top: 28px;
    left: 0;
    background: white;
    border: 1px solid #ccc;
    z-index: 1000;
    width: 200px;
    max-height: 120px;
    overflow-y: auto;
  }
  .search-results div {
    padding: 4px 6px;
    cursor: pointer;
  }
  .search-results div:hover {
    background: #eee;
  }
</style>

<div class="toggle-buttons">
  <button on:click={() => toggleMetric("avg_age")}>Average Age</button>
  <button on:click={() => toggleMetric("population_change_per_1000")}>Population Change 2025</button>
</div>

<div class="search-bar">
  <input
    type="text"
    placeholder="Search Gemeinde..."
    bind:value={searchQuery}
    on:input={searchGemeinde}
  />
  {#if searchResults.length > 0}
    <div class="search-results">
      {#each searchResults as result}
        <div on:click={() => selectGemeinde(result)}>{result.properties.name}</div>
      {/each}
    </div>
  {/if}
</div>

<select on:change={(e) => selectBundesland(e.target.value)}>
  <option value="All">All</option>
  {#each Object.values(bundeslandMap) as bl}
    <option value={bl}>{bl}</option>
  {/each}
</select>

<div id="map"></div>
