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
  },
  mounted() {
    console.log("Vue app mounted!");
    // Vue instance has mounted, check if element exists
    const appDiv = document.getElementById('app');
    if (!appDiv) {
      console.error("Vue: #app element not found in DOM!");
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

      fetch('/analyze_data/', {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        console.log('Dati ricevuti dalla chiamata API:', data);
        if ('result' in data && data.result.x_values && data.result.x_values.length > 0) {
          this.analysisResult = "Analisi completata!";
          this.drawScatter(data.result);
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
    drawScatter(result) {
      console.log("Drawing scatter plot...", result);
      this.clearScatter();
      const canvas = document.getElementById('scatterChart');
      if (!canvas) {
        console.error("Canvas not found!");
        return;
      }
      const ctx = canvas.getContext('2d');
      this.scatterChart = new Chart(ctx, {
        type: 'scatter',
        data: {
          datasets: [{
            label: 'Scatter Plot',
            data: result.x_values.map((x, i) => ({ x, y: result.y_values[i] })),
            backgroundColor: 'rgba(75, 192, 192, 1)',
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
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
