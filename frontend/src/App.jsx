import { useState } from 'react'
import './App.css'

function App() {
  const [file, setFile] = useState(null);
  const [plantilla, setPlantilla] = useState(1);
  const [error, setError] = useState(null);

  const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!file || file.type !== "application/pdf") {
      setError("Solo se permiten archivos PDF.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("plantilla", plantilla);

    try {
      const response = await fetch(`${API_URL}/convert`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        setError("Error: " + data.detail);
        return;
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = file.name.replace(".pdf", ".xlsx");
      a.click();
      window.URL.revokeObjectURL(url);

      // 🔄 Resetear formulario y estados
      setFile(null);
      setPlantilla(1);
      e.target.reset();

    } catch (err) {
      setError("Error de conexión con el servidor.");
    }
  };

  return (
    <div className="container">
      <h1>PDF → Excel</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Seleccionar plantilla:
          <select value={plantilla} onChange={(e) => setPlantilla(e.target.value)}>
            <option value={1}>Plantilla 1</option>
            <option disabled value={2}>Plantilla 2</option>
            <option disabled value={3}>Plantilla 3</option>
          </select>
        </label>

        <label>
          Subir archivo PDF (max 5MB):
          <input type="file" accept=".pdf" onChange={(e) => setFile(e.target.files[0])} />
        </label>

        <button type="submit">Convertir</button>
      </form>

      {error && <p className="error">{error}</p>}
    </div>
  );
}

export default App
