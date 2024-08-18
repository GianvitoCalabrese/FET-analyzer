new Vue({
  el: '#app',
  data: {
    fileInput: null,
    analysisResult: null,
    scatterChart: null,
    columnOptions: [], // Inizializza come array vuoto
    selectedXColumn: '', // Inizializza come stringa vuota
    selectedYColumn: '', // Inizializza come stringa vuota
  },
  methods: {
    submitData() {
      const formData = new FormData();
      formData.append('data', this.fileInput);
      formData.append('x_column', this.selectedXColumn);
      formData.append('y_column', this.selectedYColumn);

      fetch('/analyze_data/', {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        console.log('Dati ricevuti dalla chiamata API:', data);
        if ('result' in data) {
          this.analysisResult = data.result;
          if (this.scatterChart) {
            this.scatterChart.destroy(); // Distruggi il grafico precedente se esiste
          }
          this.scatterChart = this.plotScatter(data); // Crea e traccia il grafico con i dati ricevuti
        } else {
          console.error('Errore durante l\'analisi dei dati:', data.error);
        }
      })
      .catch(error => {
        console.error('Error:', error);
      });
    },
    fileChanged(event) {
      this.fileInput = event.target.files[0];
      
      // Estrai le colonne dal file CSV e aggiorna i menu a discesa
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target.result;
        console.log('target', text);
        const lines = text.split('\n');
        //console.log('Lines 0:', lines[0]);
        if (lines.length > 0) {
          const headers = lines[0].split('\t');
          console.log('Colonne estratte:', headers); //debugging
          this.columnOptions = headers; // Popola le opzioni delle colonne
          if (this.columnOptions.length > 0) {
            this.selectedXColumn = this.columnOptions[1]; // Seleziona la prima colonna per x di default
            this.selectedYColumn = this.columnOptions[2]; // Seleziona la seconda colonna per y di default
          }
        }
      };
      reader.readAsText(this.fileInput);
    },
    plotScatter(data) {
      // Assicurati che i dati siano nel formato corretto per il tracciamento dello scatter plot utilizzando Chart.js
      // Ad esempio, i dati dovrebbero essere un array di oggetti con le proprietà 'x' e 'y'.
      // Puoi adattare i dati in base alle tue esigenze.

      console.log('Dati ricevuti:', data);

      const ctx = document.getElementById('scatterChart').getContext('2d');
      const scatterChart = new Chart(ctx, {
        type: 'scatter',
        data: {
          datasets: [{
            label: 'Scatter Plot',
            data: data.result.x_values.map((x, index) => ({ x, y: data.result.y_values[index] })),
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
              /* Opzioni di scala per l'asse x */
              min: Math.min(...data.result.x_values), // Imposta il valore minimo dell'asse x come il valore minimo dei dati x
              max: Math.max(...data.result.x_values), // Imposta il valore massimo dell'asse x come il valore massimo dei dati x
            },
            y: {
              type: 'linear',
              position: 'left',
              /* Opzioni di scala per l'asse y */
              min: Math.min(...data.result.y_values), // Imposta il valore minimo dell'asse y come il valore minimo dei dati y
              max: Math.max(...data.result.y_values), // Imposta il valore massimo dell'asse y come il valore massimo dei dati y
            },
          },
        },
      });

      return scatterChart;
    },
  }
});
