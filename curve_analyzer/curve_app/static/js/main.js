console.log("main.js version 2024-07-04-1 loaded!");

new Vue({
  el: '#app',
  data: {
    fileInput: null,
    analysisResult: null,
    scatterChart: null,
    columnOptions: [],
    selectedXColumn: '',
    selectedYColumn: '',
  selectedColorColumn: '',
  selectedColorK: 5,
  },
  mounted() {
    console.log("Vue app mounted!");
    // Vue instance has mounted, check if element exists
    const appDiv = document.getElementById('app');
    if (!appDiv) {
      console.error("Vue: #app element not found in DOM!");
    }
  },
  watch: {
    selectedColorColumn(newVal, oldVal) {
      // if a file is loaded, re-submit the form to recompute color buckets
      if (this.fileInput && newVal && newVal !== oldVal) {
        console.log('Color column changed, auto-submitting to recompute buckets:', newVal);
        this.submitData();
      }
    }
  },
  methods: {
    submitData() {
      console.log("submitData called");
      if (!this.fileInput) {
        alert("Carica prima un file!");
        return;
      }
      if (!this.selectedXColumn || !this.selectedYColumn) {
        alert("Seleziona entrambe le colonne!");
        return;
      }
      console.log("Submitting with X:", this.selectedXColumn, "Y:", this.selectedYColumn);

      const formData = new FormData();
      formData.append('data', this.fileInput);
  formData.append('x_column', this.selectedXColumn.trim());
  formData.append('y_column', this.selectedYColumn.trim());
  formData.append('color_column', this.selectedColorColumn.trim());
  formData.append('color_k', String(this.selectedColorK));
  console.log("color_column:", this.selectedColorColumn, "k:", this.selectedColorK);
      fetch('/analyze_data/', {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        console.log('Dati ricevuti dalla chiamata API:', data);
          if ('result' in data && data.result.x_values && data.result.x_values.length > 0) {
            this.analysisResult = "Analisi completata!";
            this.analysisResult = "Analisi completata!";
            this.drawScatter(data.result, data.color_values || null, data.legend || null);
            // render legend (HTML) if provided
            if (data.legend && Array.isArray(data.legend)) {
              this.renderLegend(data.legend);
            } else {
              this.clearLegend();
            }
        } else {
          this.analysisResult = "Nessun dato da visualizzare.";
          this.clearScatter();
        }
      })
      .catch(error => {
        this.analysisResult = "Errore durante l'analisi dei dati.";
        console.error('Error:', error);
        this.clearScatter();
      });
    },
    fileChanged(event) {
      console.log("fileChanged called");
      this.fileInput = event.target.files[0];
      if (!this.fileInput) {
        console.warn("No file selected!");
        this.columnOptions = [];
        this.selectedXColumn = '';
        this.selectedYColumn = '';
        return;
      }
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target.result;
        const lines = text.split(/\r\n|\n|\r/).filter(line => line.trim() !== '');
        if (lines.length > 0) {
          this.columnOptions = lines[0].trim().split('\t').map(col => col.trim());
          console.log('Colonne estratte:', this.columnOptions);
          if (this.columnOptions.length > 1) {
            this.selectedXColumn = this.columnOptions[1];
            this.selectedYColumn = this.columnOptions[2] || this.columnOptions[1];
          } else if (this.columnOptions.length === 1) {
            this.selectedXColumn = this.selectedYColumn = this.columnOptions[0];
          }
          console.log("Default X:", this.selectedXColumn, "Default Y:", this.selectedYColumn);
        } else {
          this.columnOptions = [];
          this.selectedXColumn = '';
          this.selectedYColumn = '';
          console.warn("No columns found in file!");
        }
      };
      reader.onerror = (e) => {
        console.error("Error reading file:", e);
      };
      reader.readAsText(this.fileInput);
    },
    drawScatter(result, colorValues, legendArr) {
      console.log("Drawing scatter plot...", result);
      this.clearScatter();
      const canvas = document.getElementById('scatterChart');
      if (!canvas) {
        console.error("Canvas not found!");
        return;
      }
      const ctx = canvas.getContext('2d');
      // If we have per-point colors and a legend, build one dataset per legend entry so the Chart legend shows each bucket
      const datasets = [];
      if (colorValues && colorValues.length === result.x_values.length && Array.isArray(legendArr) && legendArr.length > 0) {
        // Build array of points with their colors
        const pts = result.x_values.map((x, i) => ({ x, y: result.y_values[i], color: colorValues[i] }));
        // For each legend entry, collect matching points
        legendArr.forEach(entry => {
          const color = entry.color;
          const label = entry.label;
          const dataPoints = pts.filter(p => p.color === color).map(p => ({ x: p.x, y: p.y }));
          if (dataPoints.length > 0) {
            datasets.push({
              label: label,
              data: dataPoints,
              showLine: false,
              pointBackgroundColor: color,
              backgroundColor: color,
              pointRadius: 3,
            });
          }
        });
        // Any points that didn't match legend colors (e.g., None or unexpected) go into an 'Uncategorized' gray dataset
        const unmatched = pts.filter(p => !legendArr.some(e => e.color === p.color));
        if (unmatched.length > 0) {
          datasets.push({
            label: 'Uncategorized',
            data: unmatched.map(p => ({ x: p.x, y: p.y })),
            showLine: false,
            pointBackgroundColor: 'rgba(200,200,200,0.6)',
            backgroundColor: 'rgba(200,200,200,0.6)',
            pointRadius: 3,
          });
        }
      } else {
        // fallback: single dataset with uniform color or per-point colors if supported
        datasets.push({
          label: 'Scatter Plot',
          data: result.x_values.map((x, i) => ({ x, y: result.y_values[i] })),
          showLine: false,
          pointBackgroundColor: (colorValues && colorValues.length === result.x_values.length) ? colorValues : 'rgba(75, 192, 192, 1)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          pointRadius: 3,
        });
      }

      this.scatterChart = new Chart(ctx, {
        type: 'scatter',
        data: { datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              labels: {
                usePointStyle: true,
              }
            }
          },
          scales: {
            x: {
              type: 'linear',
              position: 'bottom',
              min: Math.min(...result.x_values),
              max: Math.max(...result.x_values),
            },
            y: {
              type: 'linear',
              position: 'left',
              min: Math.min(...result.y_values),
              max: Math.max(...result.y_values),
            },
          },
        },
      });
    },
    renderLegend(legendArr) {
      const container = document.getElementById('legend');
      if (!container) return;
      container.innerHTML = '';
      const ul = document.createElement('ul');
      ul.style.listStyle = 'none';
      ul.style.padding = '0';
      ul.style.display = 'flex';
      ul.style.flexWrap = 'wrap';
      legendArr.forEach(item => {
        const li = document.createElement('li');
        li.style.marginRight = '12px';
        li.style.display = 'flex';
        li.style.alignItems = 'center';
        const sw = document.createElement('span');
        sw.style.display = 'inline-block';
        sw.style.width = '14px';
        sw.style.height = '14px';
        sw.style.background = item.color;
        sw.style.marginRight = '6px';
        sw.style.border = '1px solid rgba(0,0,0,0.2)';
        const lbl = document.createElement('span');
        lbl.textContent = item.label;
        li.appendChild(sw);
        li.appendChild(lbl);
        ul.appendChild(li);
      });
      container.appendChild(ul);
    },
    clearLegend() {
      const container = document.getElementById('legend');
      if (container) container.innerHTML = '';
    },
    clearScatter() {
      if (this.scatterChart) {
        try {
          this.scatterChart.destroy();
          console.log("Previous scatter chart destroyed.");
        } catch (err) {
          console.warn("Error destroying previous chart:", err);
        }
        this.scatterChart = null;
      }
    }
  }
});
