/**
 * Servicio centralizado de comunicación HTTP con la API REST de FastAPI.
 *
 * Utiliza Fetch API nativa y la variable de entorno VITE_API_BASE_URL.
 * Administra errores HTTP 422 (validación), HTTP 500 y excepciones de red.
 */

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');

export class ApiError extends Error {
  constructor(message, status = null, details = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

/**
 * Normaliza y extrae un mensaje comprensible a partir de respuestas de error.
 */
function extractErrorMessage(status, data) {
  if (status === 422) {
    if (data && Array.isArray(data.detail)) {
      const messages = data.detail.map((err) => {
        const field = err.loc ? err.loc[err.loc.length - 1] : 'campo';
        return `[${field}]: ${err.msg}`;
      });
      return `Error de validación (422): ${messages.join(' | ')}`;
    }
    if (data && data.detail) {
      return `Error de validación (422): ${data.detail}`;
    }
    return 'Datos inválidos según las especificaciones del backend (HTTP 422).';
  }

  if (status === 500) {
    return (
      (data && data.detail) ||
      'Error interno del servidor estadístico (HTTP 500). Verifique las condiciones matemáticas de la muestra.'
    );
  }

  if (data && data.detail) {
    return data.detail;
  }

  return `Error en la solicitud HTTP (Código ${status}).`;
}

/**
 * Consulta el estado de salud de la API.
 * @param {AbortSignal} [signal]
 * @returns {Promise<{available: boolean, status: string, service?: string, version?: string, message?: string}>}
 */
export async function checkApiHealth(signal) {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      signal,
    });

    if (!response.ok) {
      return {
        available: false,
        status: 'error',
        message: `Servidor respondió con código ${response.status}`,
      };
    }

    const data = await response.json();
    return {
      available: data.status === 'healthy',
      status: data.status || 'healthy',
      service: data.service,
      version: data.version,
    };
  } catch (error) {
    if (error.name === 'AbortError') {
      throw error;
    }
    return {
      available: false,
      status: 'offline',
      message: 'No fue posible conectar con el servidor backend en ' + API_BASE_URL,
    };
  }
}

/**
 * Ejecuta el análisis integral de bondad de ajuste a la distribución normal.
 * 
 * @param {number[]} data - Arreglo numérico con al menos 10 observaciones.
 * @param {number} [alpha=0.05] - Nivel de significancia (0 < alpha < 1).
 * @param {AbortSignal} [signal] - Señal para cancelación de solicitudes obsoletas.
 * @returns {Promise<Object>} Resultado con descriptive_metrics, goodness_of_fit y pedagogical_synthesis.
 */
export async function analyzeGoodnessOfFit(data, alpha = 0.05, signal) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/goodness-of-fit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({ data, alpha }),
      signal,
    });

    const responseData = await response.json().catch(() => null);

    if (!response.ok) {
      const msg = extractErrorMessage(response.status, responseData);
      throw new ApiError(msg, response.status, responseData);
    }

    return responseData;
  } catch (error) {
    if (error instanceof ApiError || error.name === 'AbortError') {
      throw error;
    }
    throw new ApiError(
      `Fallo de conexión con el backend (${error.message}). Asegúrese de que el servidor FastAPI esté iniciado en ${API_BASE_URL}.`,
      null,
      error
    );
  }
}

/**
 * Ejecuta la comparación inferencial entre dos muestras independientes.
 * 
 * @param {number[]} sampleA - Muestra del Grupo A (n >= 5).
 * @param {number[]} sampleB - Muestra del Grupo B (n >= 5).
 * @param {number} [alpha=0.05] - Nivel de significancia.
 * @param {AbortSignal} [signal]
 * @returns {Promise<Object>} Resultado con sample_sizes, levene, student_t, mann_whitney_u y pedagogical_synthesis.
 */
export async function compareIndependentSamples(sampleA, sampleB, alpha = 0.05, signal) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/compare-samples`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        sample_a: sampleA,
        sample_b: sampleB,
        alpha,
      }),
      signal,
    });

    const responseData = await response.json().catch(() => null);

    if (!response.ok) {
      const msg = extractErrorMessage(response.status, responseData);
      throw new ApiError(msg, response.status, responseData);
    }

    return responseData;
  } catch (error) {
    if (error instanceof ApiError || error.name === 'AbortError') {
      throw error;
    }
    throw new ApiError(
      `Fallo de conexión con el backend (${error.message}). Asegúrese de que el servidor FastAPI esté iniciado en ${API_BASE_URL}.`,
      null,
      error
    );
  }
}

