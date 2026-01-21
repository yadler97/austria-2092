<script>
  import { onMount } from "svelte";
  import { scaleLinear } from "d3-scale";
  import { interpolateViridis, interpolateRdBu } from "d3-scale-chromatic";
  import { select } from "d3-selection";
  import { axisBottom, axisLeft } from "d3-axis";
  import { brush, brushSelection } from "d3-brush";
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

  // Scatter plot size
  const width = 400;
  const height = 400;
  const margin = { top: 20, right: 20, bottom: 40, left: 50 };

  let xScale, yScale;

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

  // Scatterplot
  function drawScatter() {
    if (!geojsonData) return;

    const svg = select("#scatterplot");
    svg.selectAll("*").remove(); // clear previous

    // Filter features based on selected Bundesland
    const filteredFeatures = geojsonData.features.filter(f => {
      const gId = f.properties?.id?.toString();
      const bl = gId ? bundeslandMap[gId[0]] : null;
      return selectedBundesland === "All" || bl === selectedBundesland;
    });

    if (filteredFeatures.length === 0) return;

    const xValues = filteredFeatures.map(f => f.properties.avg_age);
    const yValues = filteredFeatures.map(f => f.properties.population_change_per_1000);

    xScale = scaleLinear()
      .domain([Math.min(...xValues), Math.max(...xValues)])
      .range([margin.left, width - margin.right]);

    yScale = scaleLinear()
      .domain([Math.min(...yValues), Math.max(...yValues)])
      .range([height - margin.bottom, margin.top]);

    // axes
    svg.append("g")
      .attr("transform", `translate(0, ${height - margin.bottom})`)
      .call(axisBottom(xScale).ticks(5));

    svg.append("g")
      .attr("transform", `translate(${margin.left}, 0)`)
      .call(axisLeft(yScale).ticks(5));

    // points
    svg.selectAll("circle")
      .data(filteredFeatures)
      .enter()
      .append("circle")
      .attr("cx", f => xScale(f.properties.avg_age))
      .attr("cy", f => yScale(f.properties.population_change_per_1000))
      .attr("r", 5)
      .attr("fill", f => {
        const val = f.properties.population_change_per_1000;
        return val >= 0 ? interpolateRdBu(1) : interpolateRdBu(0); // simple red/blue
      })
      .attr("stroke", "#333")
      .attr("stroke-width", 1)
      .style("cursor", "pointer")
      .on("mouseover", function(event, f) {
        select(this).attr("r", 8);
        // Tooltip could be added here
      })
      .on("mouseout", function(event, f) {
        select(this).attr("r", 5);
      })
      .on("click", function(event, f) {
        // zoom map to selected Gemeinde
        selectedGemeindeFeature = f;
        const layer = geojsonLayer.getLayers().find(l => l.feature === f);
        if (layer) {
          const bounds = layer.getBounds ? layer.getBounds() : layer.getLatLng().toBounds(1000);
          map.fitBounds(bounds, { padding: [20, 20] });
          layer.openTooltip();
        }
      });

    // Brush
    const brushBehavior = brush()
      .extent([[margin.left, margin.top], [width - margin.right, height - margin.bottom]])
      .on("brush end", brushed);

    svg.append("g")
      .attr("class", "brush")
      .call(brushBehavior);
  }

  function brushed({ selection }) {
    if (!selection) return;

    const [[x0, y0], [x1, y1]] = selection;

    const selectedFeatures = geojsonData.features.filter(f => {
      const gId = f.properties?.g_id?.toString();
      const bl = gId ? bundeslandMap[gId[0]] : null;
      if (selectedBundesland !== "All" && bl !== selectedBundesland) return false;

      const cx = xScale(f.properties.avg_age);
      const cy = yScale(f.properties.population_change_per_1000);
      return cx >= x0 && cx <= x1 && cy >= y0 && cy <= y1;
    });

    // Highlight on scatter plot
    const svg = select("#scatterplot");
    svg.selectAll("circle")
      .attr("fill", f => selectedFeatures.includes(f) ? "orange" : "#ccc");

    // Highlight on map
    geojsonLayer.eachLayer(layer => {
      const f = layer.feature;
      if (selectedFeatures.includes(f)) {
        layer.setStyle({ fillOpacity: 0.9, color: "orange" });
      } else {
        layer.setStyle({ fillOpacity: 0.5, color: "white" });
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

    // Load GeoJSON
    const geojsonText = await fetch(`${base}/municipalities.geojson`).then(r => r.text());
    geojsonData = JSON.parse(geojsonText);

    geojsonData.features.forEach(f => {
      if (f.properties?.g_name) f.properties.g_name = f.properties.g_name.normalize("NFC");
    });

    // Add GeoJSON layer
    geojsonLayer = L.geoJSON(geojsonData, {
      style: f => ({ fillColor: "#fff", weight: 1, color: "white", fillOpacity: 0.8 }),
      onEachFeature: (f, layer) => {
        layer.bindTooltip(`<b>${f.properties.g_name}</b><br>${f.properties[currentMetric]}`);
      }
    }).addTo(map);

    updateStyle(currentMetric);

    drawScatter();
  });

  function toggleMetric(metric) {
    currentMetric = metric;
    updateStyle(metric);
  }

  function selectBundesland(b) {
    selectedGemeindeFeature = null; // clear selected Gemeinde
    selectedBundesland = b;
    updateStyle(currentMetric);
    drawScatter();
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

<div style="display: flex; gap: 20px;">
  <div id="map" style="flex: 1; height: 80vh;"></div>
  <svg id="scatterplot" style="flex: 1; height: 80vh;"></svg>
</div>