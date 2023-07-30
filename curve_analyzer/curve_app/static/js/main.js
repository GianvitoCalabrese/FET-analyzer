new Vue({
  el: '#app',
  data: {
    fileInput: null,
    analysisResult: null,
    scatterChart: null,
  },
  methods: {
    submitData() {
      const formData = new FormData();
      formData.append('data', this.fileInput);

      fetch('/analyze_data/', {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        console.log('Dati ricevuti dalla chiamata API:', data);
        if ('result' in data) {
          this.analysisResult = data.result;
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
            data: {
              x: data.result.x_values,
              y: data.result.y_values,
            },
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
