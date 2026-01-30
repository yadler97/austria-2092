<script>
  import { onMount } from "svelte";
  import { scaleLinear } from "d3-scale";
  import { interpolateViridis, interpolateRdBu } from "d3-scale-chromatic";
  import { select } from "d3-selection";
  import { axisBottom, axisLeft } from "d3-axis";
  import { brush } from "d3-brush";
  import { base } from '$app/paths';

  let map;
  let legendDiv;
  let geojsonLayer;
  let geojsonData;
  let currentMetric = "avg_age"; 
  let selectedBundesland = "All";
  let searchQuery = "";
  let searchInput;
  let searchResults = [];
  let selectedGemeindeFeature = null;
  let circleById = new Map();
  let adminLevel = "districts";
  let fullGeojsonData;
  let hoverLayer;
  let hoverId = null

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

  const metricLabels = {
    avg_age: "Average Age",
    population_change_per_1000: "Population Change Per 1000",
    foreigner_share_2025: "Foreigner Share"
  };

  // Scatter plot size
  const margin = { top: 20, right: 20, bottom: 40, left: 50 };
  let width, height;

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
    // const legendDiv = document.querySelector(".legend");
    if (legendDiv) {
      legendDiv.innerHTML = `<b>${
        metric === "avg_age"
          ? "Average Age"
          : metric === "population_change_per_1000"
          ? "Population Change 2025"
          : "Foreigner Share 2025"
      }</b><br>`;
      const gradient = document.createElement("div");
      gradient.style.height = "12px";
      gradient.style.minWidth = "100px";
      gradient.style.width = "100%";
      gradient.style.margin = "5px 0";

      if (metric === "population_change_per_1000") {
        gradient.style.background = `linear-gradient(to right, ${interpolateRdBu(1)}, ${interpolateRdBu(0.5)}, ${interpolateRdBu(0)})`;
      } else {
        gradient.style.background = `linear-gradient(to right, ${interpolateViridis(0)}, ${interpolateViridis(1)})`;
      }

      legendDiv.appendChild(gradient);
      legendDiv.innerHTML += `
        <div style="display: flex">
          <span style="width: -webkit-fill-available">${minVal.toFixed(0)}</span>
          <span>${maxVal.toFixed(0)}</span>
        </div>
      `;
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
        let formatted;

        if (val === null || val === undefined) {
          formatted = "n/a";
        } else if (metric === "foreigner_share_2025") {
          formatted = (val * 100).toFixed(1) + " %";
        } else if (metric === "population_change_per_1000") {
          formatted = val.toFixed(1);
        } else if (Number.isInteger(val)) {
          formatted = val.toLocaleString();
        } else {
          formatted = val.toFixed(1);
        }
        layer.bindTooltip(`<b>${decodeUTF8(f.properties.g_name)}</b><br>${metricLabels[metric]}: ${formatted}`);
      } else {
        layer.unbindTooltip();
      }
    });
  }

  function isFeatureInBundesland(f) {
    if (!f.properties?.id) return false;
    const gId = f.properties.id.toString();
    const bl = bundeslandMap[gId[0]]; // first digit = Bundesland code
    return selectedBundesland === "All" || bl === selectedBundesland;
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
        const id = f.properties?.id;
        const name = f.properties?.g_name?.toLowerCase() || "";

        // Filter by name match
        if (!name.includes(q)) return false;

        // Filter by admin level
        const levelOk = adminLevel === "districts" ? isDistrict(id) : isMunicipality(id);

        // Filter by selected Bundesland
        const blOk = isFeatureInBundesland(f);

        return levelOk && blOk;
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
    svg.selectAll("*").remove(); // clear previous content

    // Filter features by selected Bundesland
    const filteredFeatures = geojsonData.features.filter(f =>
      isFeatureInBundesland(f) &&
      (adminLevel === "districts" ? isDistrict(f.properties.id) : isMunicipality(f.properties.id))
    );

    if (filteredFeatures.length === 0) return;

    const xValues = filteredFeatures.map(f => f.properties.avg_age);
    const yValues = filteredFeatures.map(f => f.properties.population_change_per_1000);

    // Scales
    const xPadding = (Math.max(...xValues) - Math.min(...xValues)) * 0.05; // 5% padding
    const yPadding = (Math.max(...yValues) - Math.min(...yValues)) * 0.05;

    xScale = scaleLinear()
      .domain([Math.min(...xValues) - xPadding, Math.max(...xValues) + xPadding])
      .range([margin.left, width - margin.right]);

    yScale = scaleLinear()
      .domain([Math.min(...yValues) - yPadding, Math.max(...yValues) + yPadding])
      .range([height - margin.bottom, margin.top]);

    // Axes
    svg.append("g")
      .attr("transform", `translate(0, ${height - margin.bottom})`)
      .call(axisBottom(xScale).ticks(5));

    svg.append("g")
      .attr("transform", `translate(${margin.left},0)`)
      .call(axisLeft(yScale).ticks(5));

    svg.append("text")
      .attr("x", width / 2)
      .attr("y", height - 5)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("font-family", "sans-serif")
      .text("Average Age");

    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -height / 2)
      .attr("y", 15)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("font-family", "sans-serif")
      .text("Population Change per 1000");

    // --- 1️⃣ Brush Layer ---
    const brushG = svg.append("g")
      .attr("class", "brush")
      .call(
        brush()
          .extent([[margin.left, margin.top], [width - margin.right, height - margin.bottom]])
          .on("brush end", brushed)
      );

    // Prevent default context menu
    svg.on("contextmenu", (event) => event.preventDefault());

    // Overlay: right-click brush, left-click ignored here
    brushG.selectAll(".overlay")
      .attr("fill", "transparent")
      .style("pointer-events", "all")
      .on("mousedown", function(event) {
        if (event.button === 2) {
          // right-click → start brush normally
          select(this).dispatch("start");
        }
        // left-click handled by circles
      });

    const tooltip = select("#scatter-tooltip");

    // --- 2️⃣ Draw Points on TOP of brush ---
    svg.selectAll("circle")
      .data(filteredFeatures)
      .enter()
      .append("circle")
      .attr("cx", f => xScale(f.properties.avg_age))
      .attr("cy", f => yScale(f.properties.population_change_per_1000))
      .attr("r", 5)
      .attr("fill", f => f.properties.population_change_per_1000 >= 0 ? interpolateRdBu(1) : interpolateRdBu(0))
      .attr("stroke", "#333")
      .attr("stroke-width", 1)
      .style("cursor", "pointer")
      .each(function(f) {
        circleById.set(f.properties.id, select(this)); // store reference
      })
      .on("mouseover", function(event, f) {
        select(this)
          .transition()
          .duration(150)
          .attr("r", 12)
          .attr("fill", "orange");

        hoverFeatureOnMap(f);

        const avgAge = f.properties.avg_age !== null ? f.properties.avg_age.toFixed(1) : "n/a";
        const popChange = f.properties.population_change_per_1000 !== null
          ? f.properties.population_change_per_1000.toFixed(1)
          : "n/a";
        const foreignerShare = f.properties.foreigner_share_2025 !== null
          ? (f.properties.foreigner_share_2025 * 100).toFixed(1) + " %"
          : "n/a";

        tooltip
          .style("opacity", 1)
          .html(`<b>${f.properties.name}</b><br>${metricLabels["avg_age"]}: ${avgAge}<br>${metricLabels["population_change_per_1000"]}: ${popChange}<br>${metricLabels["foreigner_share_2025"]}: ${foreignerShare}`)
          .style("left", (event.pageX + 10) + "px")
          .style("top", (event.pageY + 10) + "px");
      })
      .on("mousemove", function(event, f) {
        tooltip
          .style("left", (event.pageX + 10) + "px")
          .style("top", (event.pageY + 10) + "px");
      })
      .on("mouseout", function(event, f) {
        select(this)
          .transition()
          .duration(150)
          .attr("r", 5)
          .attr("fill", f.properties.population_change_per_1000 >= 0 ? interpolateRdBu(1) : interpolateRdBu(0));

        unhoverFeatureOnMap(f);

        tooltip.style("opacity", 0);
      })
      .on("click", function(event, f) {
        // Left-click → zoom to Gemeinde
        selectedGemeindeFeature = f;
        const layer = geojsonLayer.getLayers().find(l => l.feature === f);
        if (layer) {
          const bounds = layer.getBounds ? layer.getBounds() : layer.getLatLng().toBounds(1000);
          map.fitBounds(bounds, { padding: [20, 20] });
          layer.openTooltip();
        }
      });

      geojsonLayer.eachLayer(layer => {
        const id = layer.feature.properties.id;

        layer.on("mouseover", () => {
          if (!isFeatureInBundesland(layer.feature)) return;
          hoverFeatureOnMap(layer.feature);

          const circle = circleById.get(id);
          if (circle) {
            circle.attr("fill", "orange").attr("r", 12);
          }
        });

        layer.on("mouseout", () => {
          unhoverFeatureOnMap(layer.feature);

          const circle = circleById.get(layer.feature.properties.id);
          if (circle) {
            circle.attr("fill", circle.data()[0].properties.population_change_per_1000 >= 0 ? interpolateRdBu(1) : interpolateRdBu(0))
                  .attr("r", 5);
          }
        });
      });

    function brushed({ selection }) {
      if (!selection) return;
      const [[x0, y0], [x1, y1]] = selection;

      const selectedFeatures = filteredFeatures.filter(f => {
        const cx = xScale(f.properties.avg_age);
        const cy = yScale(f.properties.population_change_per_1000);
        return cx >= x0 && cx <= x1 && cy >= y0 && cy <= y1;
      });

      // Highlight on scatterplot
      svg.selectAll("circle")
        .attr("fill", f => selectedFeatures.includes(f) ? "orange" : f.properties.population_change_per_1000 >= 0 ? interpolateRdBu(1) : interpolateRdBu(0));

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
  }

  function refreshGeojsonLayer() {
    if (geojsonLayer) map.removeLayer(geojsonLayer);

    geojsonData = {
      ...fullGeojsonData,
      features: filterFeaturesByLevel(fullGeojsonData.features)
    };

    geojsonLayer = L.geoJSON(geojsonData, {
      style: f => ({ fillColor: "#fff", weight: 1, color: "white", fillOpacity: 0.8 }),
      onEachFeature: (f, layer) => {
        layer.bindTooltip(`<b>${f.properties.g_name}</b><br>${f.properties[currentMetric]}`);
      }
    }).addTo(map);

    circleById.clear();
    selectedGemeindeFeature = null;

    updateStyle(currentMetric);
    drawScatter();
  }

  function hoverFeatureOnMap(feature) {
    const id = feature.properties.id;

    // If already hovering this feature, do nothing
    if (hoverId === id) return;

    // Remove previous hover overlay
    if (hoverLayer) {
      map.removeLayer(hoverLayer);
      hoverLayer = null;
    }

    // Add new hover overlay
    hoverLayer = L.geoJSON(feature, {
      style: {
        fillOpacity: 0.5,
        weight: 3,
        color: "#ff6600",
        dashArray: ""
      },
      interactive: false // important: overlay doesn't catch mouse events
    }).addTo(map);

    hoverId = id;
  }

  function unhoverFeatureOnMap(feature) {
    const id = feature.properties.id;

    if (hoverId === id && hoverLayer) {
      map.removeLayer(hoverLayer);
      hoverLayer = null;
      hoverId = null;
    }
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
    fullGeojsonData = JSON.parse(geojsonText);

    fullGeojsonData.features.forEach(f => {
      if (f.properties?.g_name) f.properties.g_name = f.properties.g_name.normalize("NFC");
    });

    geojsonData = {
      type: "FeatureCollection",
      features: filterFeaturesByLevel(fullGeojsonData.features)
    };

    // Add GeoJSON layer
    geojsonLayer = L.geoJSON(geojsonData, {
      style: f => ({ fillColor: "#fff", weight: 1, color: "white", fillOpacity: 0.8 }),
      onEachFeature: (f, layer) => {
        layer.bindTooltip(`<b>${f.properties.g_name}</b><br>${f.properties[currentMetric]}`);
      }
    }).addTo(map);

    const legend = L.control({ position: "bottomright" });

    legend.onAdd = () => {
      legendDiv = L.DomUtil.create("div", "legend");
      return legendDiv;
    };

    legend.addTo(map);

    updateStyle(currentMetric);

    const container = document.getElementById("scatter-container");
    width = container.clientWidth;
    height = container.clientHeight;

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

  function selectAllText() {
    if (searchInput) searchInput.select();
  }

  function isDistrict(id) {
    if (!id) return false;
    const s = id.toString();
    return s.length === 3 || (Number(s) >= 901 && Number(s) <= 923);
  }

  function isMunicipality(id) {
    if (!id) return false;
    const s = id.toString();
    return s.length === 5 || (Number(s) >= 901 && Number(s) <= 923);
  }

  function filterFeaturesByLevel(features) {
    return features.filter(f => {
      const id = f.properties?.id;
      return adminLevel === "districts"
        ? isDistrict(id)
        : isMunicipality(id);
    });
  }
</script>

<svelte:head>
  <meta charset="utf-8" />
</svelte:head>

<style>
  #map {
    width: 100%;
    height: 100%;
  }
  #scatterplot {
    width: 100%;
    height: 100%;
  }
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
    z-index: 2000;
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
  .toggle-buttons button {
    margin-right: 10px;
    padding: 5px 10px;
    cursor: pointer;
    background: #f5f5f5;
    border: 1px solid #ccc;
    border-radius: 4px;
    transition: all 0.15s ease;
  }
  .toggle-buttons button:hover {
    background: #eaeaea;
  }
  .toggle-buttons button.active {
    background: #333;
    color: white;
    border-color: #333;
    font-weight: 600;
  }
  .toggle-buttons, .bundesland-selection span {
    font-family: sans-serif;
    font-size: inherit;
    line-height: inherit;
  }
  .search-bar input {
    background: #f5f5f5;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 5px 10px;
    font-family: sans-serif;
    font-size: inherit;
    transition: all 0.15s ease;
    width: 200px;
  }
  .search-bar input:hover,
  .search-bar input:focus {
    background: #eaeaea;
    outline: none;
    border-color: #999;
  }
  .proposed {
      font-family: sans-serif;
  }
  .bundesland-selection {
    margin: 10px;
  }
  .bundesland-selection select {
    background: #f5f5f5;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 5px 10px;
    font-family: sans-serif;
    font-size: inherit;
    transition: all 0.15s ease;
  }
  .bundesland-selection select:hover,
  .bundesland-selection select:focus {
    background: #eaeaea;
    outline: none;
    border-color: #999;
  }
</style>

<div class="toggle-buttons">
  <span>Select Metric:</span>
  <button class:active={currentMetric === "avg_age"} on:click={() => toggleMetric("avg_age")}>Average Age</button>
  <button class:active={currentMetric === "population_change_per_1000"} on:click={() => toggleMetric("population_change_per_1000")}>Population Change 2025</button>
  <button class:active={currentMetric === "foreigner_share_2025"} on:click={() => toggleMetric("foreigner_share_2025")}>Foreigner Share 2025</button>
</div>

<div class="toggle-buttons">
  <span>Admin level:</span>
  <button
    class:active={adminLevel === "districts"}
    on:click={() => { adminLevel = "districts"; refreshGeojsonLayer(); }}>
    Districts
  </button>

  <button
    class:active={adminLevel === "municipalities"}
    on:click={() => { adminLevel = "municipalities"; refreshGeojsonLayer(); }}>
    Municipalities
  </button>
</div>

<div class="search-bar">
  <input
    type="text"
    placeholder="Search Gemeinde..."
    bind:value={searchQuery}
    on:input={searchGemeinde}
    on:focus={selectAllText}
    bind:this={searchInput}
  />
  {#if searchResults.length > 0}
    <div class="search-results">
      {#each searchResults as result}
        <div class="proposed" on:click={() => selectGemeinde(result)}>{result.properties.name}</div>
      {/each}
    </div>
  {/if}
</div>

<div class="bundesland-selection">
  <span>Select Bundesland:</span>
  <select on:change={(e) => selectBundesland(e.target.value)}>
    <option value="All">All</option>
    {#each Object.values(bundeslandMap) as bl}
      <option value={bl}>{bl}</option>
    {/each}
  </select>
</div>

<div style="display: flex; gap: 20px; height: 80vh;">
  <div id="map" style="flex: 1; height: 100%;"></div>

  <div id="scatter-container" style="flex: 1; position: relative;">
    <svg id="scatterplot" style="width: 100%; height: 100%;"></svg>
  </div>
</div>

<div id="scatter-tooltip"
  style="position: absolute; pointer-events: none; background: white; padding: 4px 6px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px; opacity: 0; transition: opacity 0.1s; font-family: sans-serif;">
</div>