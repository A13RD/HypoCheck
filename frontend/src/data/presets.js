/**
 * Conjuntos de datos predeterminados y deterministas para la Suite de Inferencia Estadística.
 * 
 * Cumplen con la especificación de la Etapa 3:
 * 1. Escenario de Latencias E-Commerce (asimétrico con colas pesadas / valores extremos).
 * 2. Escenario 1 - Rúbrica (Normal): n = 60, media teórica = 175, desviación estándar teórica = 30.
 * 3. Escenario 2 - Rúbrica (Gamma): n = 60, forma = 1.2, escala = 150.
 * 4. Escenario de Comparación de Dos Muestras (Grupos A y B reproducibles).
 */

export const PRESET_SCENARIOS = {
  ecommerce: {
    id: 'ecommerce',
    title: 'Datos simulados de latencias E-Commerce',
    buttonLabel: 'Cargar escenario de Latencias E-Commerce',
    description:
      'Muestra sintética reproducible de 40 tiempos de respuesta HTTP (milisegundos) en un servidor de comercio electrónico. ' +
      'Presenta asimetría positiva pronunciada y observaciones extremas para evaluar el comportamiento de las pruebas ante apartamientos de la normalidad.',
    isSimulated: true,
    data: [
      124.5, 132.1, 128.4, 145.2, 138.9, 152.0, 130.8, 141.5, 127.3, 135.6,
      148.2, 160.4, 142.7, 136.9, 155.1, 149.3, 162.8, 158.4, 170.2, 165.5,
      185.0, 192.4, 178.6, 210.3, 225.8, 240.1, 265.4, 280.9, 310.5, 345.2,
      390.0, 420.5, 480.2, 530.8, 620.1, 750.4, 890.2, 1120.5, 1340.0, 1580.6
    ]
  },

  rubricNormal: {
    id: 'rubricNormal',
    title: 'Escenario 1 - Rúbrica (Distribución Normal)',
    buttonLabel: 'Cargar Escenario 1 - Rúbrica (Normal)',
    description:
      'Muestra sintética determinista de 60 observaciones generadas bajo una distribución Gaussiana con media teórica μ = 175 ' +
      'y desviación estándar teórica σ = 30 (semilla pseudoaleatoria fija 2026). Diseñada para comprobar la no-rejección de H0.',
    isSimulated: true,
    data: [
      151.21, 182.22, 118.11, 216.87, 194.15, 166.24, 165.64, 184.12, 166.97, 168.22,
      196.60, 190.44, 173.08, 172.44, 179.83, 156.58, 162.89, 191.45, 171.09, 133.77,
      160.68, 194.70, 168.03, 170.54, 194.26, 229.74, 153.60, 215.45, 138.10, 180.25,
      139.91, 215.54, 200.02, 209.13, 148.43, 195.54, 159.43, 161.28, 190.20, 201.30,
      181.13, 156.16, 150.23, 218.33, 192.82, 196.59, 240.50, 150.52, 251.78, 269.53,
      223.55, 199.81, 155.09, 204.83, 161.72, 174.35, 166.29, 183.51, 213.64, 158.33
    ]
  },

  rubricGamma: {
    id: 'rubricGamma',
    title: 'Escenario 2 - Rúbrica (Distribución Gamma)',
    buttonLabel: 'Cargar Escenario 2 - Rúbrica (Gamma)',
    description:
      'Muestra sintética determinista de 60 observaciones generadas bajo una distribución Gamma con parámetro de forma k = 1.2 ' +
      'y escala θ = 150 (media teórica = 180, semilla pseudoaleatoria fija 2026). Presenta asimetría positiva inherente a procesos de confiabilidad y colas.',
    isSimulated: true,
    data: [
      35.24, 36.25, 39.65, 63.50, 23.36, 6.95, 767.36, 357.50, 109.79, 405.23,
      481.21, 138.17, 189.38, 57.57, 43.51, 230.61, 147.07, 83.58, 30.88, 3.48,
      312.20, 438.76, 124.98, 210.63, 47.09, 146.69, 126.24, 28.80, 311.87, 357.09,
      56.17, 258.76, 161.96, 94.45, 2.58, 281.07, 76.51, 287.73, 34.88, 477.53,
      143.11, 37.42, 488.57, 125.93, 29.16, 115.89, 288.30, 76.41, 212.45, 237.49,
      310.35, 969.43, 274.17, 41.79, 186.07, 56.63, 43.03, 447.83, 136.15, 362.04
    ]
  }
};

export const PRESET_TWO_SAMPLES = {
  title: 'Muestras Reproducibles de Resistencia a la Tracción (MPa)',
  description:
    'Grupo A: Aleación estándar (Control, n=15, μ≈52 MPa). ' +
    'Grupo B: Aleación tratada térmicamente (Tratamiento, n=15, μ≈61 MPa). Homocedásticas con diferencia de medias significativa.',
  sampleA: [
    50.2, 53.1, 49.8, 54.3, 51.7, 52.5, 48.9, 53.8, 50.6, 51.2,
    55.1, 49.3, 52.8, 53.4, 51.0
  ],
  sampleB: [
    60.5, 62.1, 58.7, 63.4, 61.2, 59.8, 64.0, 60.9, 61.8, 59.2,
    62.7, 61.4, 63.1, 58.9, 62.3
  ]
};

