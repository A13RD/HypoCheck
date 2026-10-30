# Suite de Inferencia Estadística y Bondad de Ajuste (HypoCheck)

**Proyecto de Aula 2026-2 | Estadística para Ingeniería — Universidad de Medellín**

---

## A. Descripción del Proyecto

**HypoCheck** es una suite académica y científica de inferencia estadística diseñada para evaluar la bondad de ajuste a la distribución normal y contrastar muestras independientes. El sistema integra un motor matemático riguroso en Python, una API REST validada con FastAPI/Pydantic y un dashboard interactivo en React con visualizaciones estadísticas en Plotly.js.

### Capacidades Estadísticas Principales

1. **Estadística Descriptiva Muestral**:
   - Tamaño muestral ($n$), media aritmética ($\bar{x}$), varianza muestral con corrección de Bessel ($s^2$, `ddof=1`), desviación estándar ($s$), coeficiente de asimetría de Fisher-Pearson sin sesgo ($g_1$) y exceso de curtosis de Fisher sin sesgo ($g_2$).
2. **Batería de Cuatro Pruebas de Bondad de Ajuste y Normalidad**:
   - **Kolmogorov-Smirnov (con calibración de Lilliefors por Monte Carlo)**: Reestima media y desviación estándar en cada réplica simulada (9999 simulaciones con semilla reproducible) para evitar el sesgo del valor-$p$ clásico cuando los parámetros se estiman de la muestra.
   - **Anderson-Darling**: Evalúa discrepancias cuadráticas ponderando con mayor sensibilidad las colas de la distribución frente a valores críticos tabulados ($\alpha \in \{0.01, 0.05, 0.10\}$).
   - **Shapiro-Wilk**: Contrasta la linealidad entre estadísticos de orden y cuantiles normales esperados ($W$ y valor-$p$), alertando sobre limitaciones de precisión numérica cuando $N > 5000$.
   - **Chi-cuadrada de Pearson**: Particiona el soporte completo $(-\infty, +\infty)$ con la regla $2^k > n$, aplica un algoritmo determinístico de fusión de intervalos adyacentes hasta garantizar $E_i \ge 5$ en toda clase y calcula $\nu = k_{\text{ajustado}} - 3$ grados de libertad.
3. **Comparación Inferencial de Dos Muestras Independientes**:
   - **Prueba de Levene** ($\alpha = 0.05$ fijo) para evaluar homocedasticidad ($H_0: \sigma_1^2 = \sigma_2^2$).
   - **Prueba $t$ de Student / Welch bilateral**: Selección automática de `equal_var` según el dictamen de Levene.
   - **Prueba $U$ de Mann-Whitney bilateral**: Contraste no paramétrico basado en rangos con corrección por empates.
4. **Síntesis Pedagógica Dinámica**:
   - Interpretación formal que contrasta sensibilidades metodológicas sin aplicar votaciones por mayoría.

---

## B. Tecnologías Utilizadas

### Backend
- **Python** (3.11+)
- **NumPy** (`>=1.26.0,<3.0.0`): Operaciones vectoriales y cálculo descriptivo.
- **SciPy** (`>=1.12.0,<2.0.0`): Funciones de distribución, pruebas de hipótesis y simulaciones Monte Carlo (`scipy.stats`).
- **FastAPI** (`>=0.110.0,<1.0.0`): Servidor web ASGI y definición de endpoints REST.
- **Pydantic v2** (`>=2.6.0,<3.0.0`): Validación estricta de esquemas de entrada y contratos JSON de respuesta.
- **Uvicorn** (`>=0.28.0,<1.0.0`): Servidor ASGI de ejecución.
- **HTTPX** (`>=0.27.0,<1.0.0`) y `unittest`: Pruebas unitarias y de integración.

### Frontend
- **React 18** (`^18.3.1`, JavaScript + JSX)
- **Vite** (`^5.4.14`): Empaquetador y servidor de desarrollo con carga diferida (`React.lazy`).
- **Mantine UI v7** (`@mantine/core`, `@mantine/hooks`): Sistema de componentes científicos con soporte de tema claro/oscuro, PostCSS y CSS Modules.
- **Plotly.js** (`plotly.js`, `react-plotly.js`): Histograma de densidad empírica con curva normal teórica superpuesta y diagrama de cajas y bigotes (*Boxplot*).
- **Fetch API**: Comunicación HTTP asíncrona con soporte de cancelación (`AbortController`).

---

## C. Estructura General del Proyecto

```text
HypoCheck/
├── backend/
│   ├── __init__.py
│   ├── engine_estadistico.py       # Motor matemático independiente (clase MotorEstadistico)
│   ├── schemas.py                  # Modelos Pydantic de validación de entrada y salida JSON
│   ├── app.py                      # Servidor FastAPI, endpoints REST, CORS y manejo de errores
│   ├── requirements.txt            # Dependencias del backend
│   ├── .env.example                # Plantilla de variables de entorno del backend
│   └── tests/
│       ├── test_engine_estadistico.py  # 23 pruebas unitarias del motor estadístico
│       └── test_api.py                 # 23 pruebas de integración de la API REST
├── frontend/
│   ├── index.html                  # Documento raíz HTML5
│   ├── package.json                # Dependencias y scripts de Node/Vite
│   ├── postcss.config.cjs          # Configuración PostCSS para Mantine UI
│   ├── vite.config.js              # Configuración de Vite y división de chunks
│   ├── .env.example                # Plantilla de variables de entorno del frontend
│   └── src/
│       ├── main.jsx                # Punto de entrada React y MantineProvider
│       ├── App.jsx                 # Estado global, navegación por pestañas y conexión HTTP
│       ├── services/
│       │   └── api.js              # Cliente HTTP centralizado (Fetch API)
│       ├── data/
│       │   └── presets.js          # Escenarios sintéticos reproducibles (E-Commerce, Normal, Gamma)
│       ├── styles/
│       │   ├── global.css          # Estilos globales
│       │   └── Dashboard.module.css# CSS Module responsivo para el dashboard
│       └── components/
│           ├── layout/             # Header (estado API + tema) y Footer institucional
│           ├── analysis/           # Presets, entrada manual, tarjetas, tabla de 4 pruebas y síntesis
│           ├── charts/             # Histograma + curva normal y Boxplot (Plotly.js)
│           └── comparison/         # Comparación de dos muestras (Levene, t-Student/Welch, Mann-Whitney)
├── requirements.txt                # Referencia a backend/requirements.txt
├── .gitignore                      # Exclusión de entornos virtuales, node_modules, dist y .env
└── README.md                       # Documentación técnica integral
```

---

## D. Requisitos Previos

- **Python**: `3.11` o superior (verificado en Python `3.12`).
- **Node.js**: `18.0.0` o superior (verificado en Node.js `24.15.0`) y `npm` `9+`.

---

## E. Instalación

Abra una terminal de **Windows PowerShell** en la raíz del repositorio (`HypoCheck`) y ejecute los siguientes pasos:

### 1. Configuración del Backend (Python)

```powershell
# Crear el entorno virtual de Python
python -m venv .venv

# Activar el entorno virtual en Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Instalar las dependencias del backend
pip install -r requirements.txt
```

### 2. Configuración del Frontend (Node.js / Vite)

```powershell
# Ingresar al directorio del frontend
cd frontend

# Instalar las dependencias de Node.js
npm install

# Volver a la raíz del proyecto
cd ..
```

---

## F. Ejecución de la Aplicación

Para utilizar el sistema completo, levante el backend y el frontend en dos terminales independientes de **Windows PowerShell**:

### Terminal 1 — Servidor Backend (FastAPI en puerto `8000`)

Desde la raíz del proyecto (`HypoCheck`):

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

### Terminal 2 — Servidor de Desarrollo Frontend (Vite en puerto `5173`)

Desde la carpeta `frontend`:

```powershell
cd frontend
npm run dev
```

Una vez iniciados ambos servicios, abra su navegador en:
- **Aplicación Web (Dashboard)**: `http://localhost:5173`
- **Documentación Interactiva Swagger UI**: `http://127.0.0.1:8000/docs`
- **Documentación ReDoc**: `http://127.0.0.1:8000/redoc`

---

## G. Variables de Entorno

El proyecto funciona directamente en desarrollo local con sus valores predeterminados, pero permite personalizar la configuración mediante archivos `.env` creados a partir de las plantillas `.env.example` (no se incluyen archivos `.env` reales ni secretos en el repositorio).

### 1. Backend (`backend/.env.example`)
- `CORS_ORIGINS`: Lista de orígenes permitidos separados por comas.
  - Valor por defecto si no se define: `http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:5500,http://127.0.0.1:5500,http://localhost:8080,http://127.0.0.1:8080`.
  - Para crear el archivo `.env` en PowerShell:
    ```powershell
    Copy-Item backend\.env.example backend\.env
    ```

### 2. Frontend (`frontend/.env.example`)
- `VITE_API_BASE_URL`: URL base del servidor FastAPI.
  - Valor por defecto si no se define: `http://127.0.0.1:8000`.
  - Para crear el archivo `.env` en PowerShell:
    ```powershell
    Copy-Item frontend\.env.example frontend\.env
    ```

---

## H. Ejecución de Pruebas y Compilación

### 1. Pruebas Unitarias y de Integración del Backend (46 pruebas)

Desde la raíz del proyecto (`HypoCheck`) en PowerShell:

```powershell
# Ejecutar toda la batería de pruebas (motor estadístico + API REST)
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v

# Ejecutar únicamente las pruebas unitarias del motor estadístico (23 pruebas)
.\.venv\Scripts\python.exe -m unittest backend/tests/test_engine_estadistico.py -v

# Ejecutar únicamente las pruebas de integración de FastAPI (23 pruebas)
.\.venv\Scripts\python.exe -m unittest backend/tests/test_api.py -v
```

### 2. Compilación de Producción del Frontend

Desde la carpeta `frontend`:

```powershell
cd frontend
npm run build
```

Los artefactos optimizados se generan en `frontend/dist/`. Para previsualizar la compilación de producción localmente:

```powershell
npm run preview
```

---

## I. Documentación de Endpoints REST

| Método | Ruta | Descripción | Requisitos de Entrada |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Metadatos del servicio, versión y rutas de documentación. | Ninguno. |
| `GET` | `/health` | Estado de salud del servidor (`{"status": "healthy"}`). | Ninguno. |
| `POST` | `/api/v1/goodness-of-fit` | Métricas descriptivas, 4 pruebas de normalidad (K-S, A-D, Shapiro-Wilk, Chi-cuadrada) y síntesis pedagógica. | JSON: `{"data": list[float] (n >= 10), "alpha": float (0 < alpha < 1)}`. |
| `POST` | `/api/v1/compare-samples` | Comparación de dos muestras independientes (Levene, t-Student/Welch y Mann-Whitney U). | JSON: `{"sample_a": list[float] (n >= 5), "sample_b": list[float] (n >= 5), "alpha": float}`. |

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

---

## J. Alcance y Limitaciones Estadísticas

1. **Principio Epistemológico Fundamental**:
   No rechazar la hipótesis nula ($H_0$) **nunca demuestra que la distribución poblacional sea estrictamente normal**. Únicamente indica que, con el tamaño muestral disponible y al nivel de significancia $\alpha$ seleccionado, no existe evidencia empírica suficiente para descartar la compatibilidad con el modelo normal.
2. **Condiciones de Aplicabilidad en Chi-cuadrada de Pearson**:
   Dado que se estiman dos parámetros muestrales ($\mu$ y $\sigma$) y se exige la condición de Cochran/Pearson de frecuencias esperadas mínimas $E_i \ge 5$ en todas las clases tras la fusión determinística, los grados de libertad son $\nu = k_{\text{ajustado}} - 3$. En muestras pequeñas ($n < 20$) o con asimetría extrema y valores atípicos severos que fuerzan la fusión en 3 o menos clases ($\nu \le 0$), la prueba reporta explícitamente `available: false` con su justificación matemática sin interrumpir las otras tres pruebas.
3. **Precisión de Shapiro-Wilk para Muestras Masivas ($N > 5000$)**:
   De acuerdo con la documentación de `scipy.stats.shapiro` (algoritmo de Royston), para $N > 5000$ el estadístico $W$ es exacto pero el cálculo del valor-$p$ puede presentar limitaciones de precisión; el sistema incluye una advertencia explícita en el campo `warnings`.
4. **Valores Críticos en Anderson-Darling**:
   La prueba de Anderson-Darling para normalidad en `scipy.stats.anderson` utiliza niveles de significancia tabulados ($15\%, 10\%, 5\%, 2.5\%, 1\%$). El sistema opera con los niveles estándar $\alpha \in \{0.01, 0.05, 0.10\}$ y no inventa valores-$p$ no proporcionados por la rutina original.
5. **Interpretación en Comparación de Dos Muestras**:
   - La prueba de **Levene** evalúa igualdad de varianzas (homocedasticidad), **no normalidad**.
   - El rechazo de Levene conduce al uso de la prueba **$t$ de Welch** para varianzas desiguales, no necesariamente al descarte del enfoque paramétrico.
   - La prueba **$U$ de Mann-Whitney** evalúa dominancia estocástica (diferencia en la distribución de rangos); solo equivale a una comparación estricta de medianas cuando ambas distribuciones tienen idéntica forma y dispersión.

