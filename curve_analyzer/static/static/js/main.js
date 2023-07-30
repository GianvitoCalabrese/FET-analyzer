new Vue({
    el: 'body',
    data: {
        analysisResult: '',
        fileData: null,
    },
    methods: {
        uploadFile(event) {
            const file = event.target.files[0];
            const reader = new FileReader();

            reader.onload = (e) => {
                this.fileData = e.target.result;
            };

            reader.readAsText(file);
        },
        analyzeData() {
            if (!this.fileData) {
                alert('Carica un file CSV prima di procedere.');
                return;
            }

            fetch('/analyze_data/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken'),
                },
                body: JSON.stringify({ data: this.fileData }),
            })
            .then(response => response.json())
            .then(data => {
                this.analysisResult = data.result;
            })
            .catch(error => {
                console.error('Errore durante l\'analisi dei dati:', error);
            });
        },
        getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
    }
});
