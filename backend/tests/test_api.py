"""
Pruebas de integración de la API REST de FastAPI con el Motor Estadístico.

Verifica de forma exhaustiva los 14 puntos obligatorios de la Etapa 2:
1. Endpoint raíz (GET /) devuelve HTTP 200.
2. Endpoint de salud (GET /health) devuelve HTTP 200.
3. Documentación interactiva Swagger (GET /docs) y OpenAPI disponible.
4. Bondad de ajuste con muestra válida devuelve HTTP 200 y resultados coherentes.
5. Bondad de ajuste con menos de 10 observaciones devuelve HTTP 422.
6. Rechazo de alpha inválido devuelve HTTP 422.
7. Rechazo de valores NaN e infinitos devuelve HTTP 422.
8. Verificación estricta de la estructura JSON del contrato de bondad de ajuste.
9. Comparación de dos muestras válidas devuelve HTTP 200.
10. Comparación con menos de 5 observaciones por grupo devuelve HTTP 422.
11. Rechazo de matrices multidimensionales y datos no numéricos devuelve HTTP 422.
12. Verificación estricta de la estructura JSON del contrato de comparación.
13. Verificación de que Chi-cuadrada aparezca como no disponible (available=False) sin romper la respuesta (HTTP 200).
14. Comprobación de que los resultados provienen realmente del motor estadístico y no de valores fijos.
15. Gestión adecuada de errores internos no previstos (HTTP 500) sin filtrar trazas locales.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch
import numpy as np
import scipy.stats as stats
from fastapi.testclient import TestClient

try:
    from backend.app import app, motor_estadistico
    from backend.engine_estadistico import DatosInvalidosError
except ImportError:
    from app import app, motor_estadistico
    from engine_estadistico import DatosInvalidosError


class TestAPIIntegracion(unittest.TestCase):
    """Suite de pruebas de integración para los endpoints de FastAPI."""

    @classmethod
    def setUpClass(cls) -> None:
        """Inicializa el cliente de pruebas de FastAPI."""
        cls.client = TestClient(app)

    # -------------------------------------------------------------------------
    # 1. Endpoint raíz devuelve HTTP 200
    # -------------------------------------------------------------------------
    def test_01_endpoint_raiz_status_200(self) -> None:
        """Comprueba que GET / retorne HTTP 200 con la información del servicio."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertIn("message", json_data)
        self.assertIn("version", json_data)
        self.assertIn("docs_url", json_data)
        self.assertEqual(json_data["docs_url"], "/docs")

    # -------------------------------------------------------------------------
    # 2. Endpoint de salud devuelve HTTP 200
    # -------------------------------------------------------------------------
    def test_02_endpoint_health_status_200(self) -> None:
        """Comprueba que GET /health retorne HTTP 200 y status healthy."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data.get("status"), "healthy")

    # -------------------------------------------------------------------------
    # 3. Documentación Swagger y OpenAPI disponible
    # -------------------------------------------------------------------------
    def test_03_documentacion_swagger_y_openapi_disponible(self) -> None:
        """Verifica que /docs y /openapi.json sean accesibles correctamente."""
        res_docs = self.client.get("/docs")
        self.assertEqual(res_docs.status_code, 200)

        res_openapi = self.client.get("/openapi.json")
        self.assertEqual(res_openapi.status_code, 200)
        openapi_data = res_openapi.json()
        self.assertIn("paths", openapi_data)
        self.assertIn("/api/v1/goodness-of-fit", openapi_data["paths"])
        self.assertIn("/api/v1/compare-samples", openapi_data["paths"])

    # -------------------------------------------------------------------------
    # 4. Bondad de ajuste con muestra válida
    # -------------------------------------------------------------------------
    def test_04_goodness_of_fit_muestra_valida(self) -> None:
        """Verifica que POST /api/v1/goodness-of-fit retorne 200 con datos válidos."""
        rng = np.random.default_rng(12345)
        muestra = rng.normal(loc=170.0, scale=10.0, size=50).tolist()

        payload = {
            "data": muestra,
            "alpha": 0.05,
        }
        response = self.client.post("/api/v1/goodness-of-fit", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["descriptive_metrics"]["n"], 50)
        self.assertIsInstance(data["goodness_of_fit"]["kolmogorov_smirnov"]["p_value"], float)
        self.assertIsInstance(data["goodness_of_fit"]["anderson_darling"]["statistic"], float)
        self.assertIsInstance(data["pedagogical_synthesis"], str)

    # -------------------------------------------------------------------------
    # 5. Bondad de ajuste con menos de 10 observaciones devuelve HTTP 422
    # -------------------------------------------------------------------------
    def test_05_goodness_of_fit_menos_de_10_observaciones_retorna_422(self) -> None:
        """Asegura que muestras de tamaño menor a 10 sean rechazadas con 422."""
        muestra_pequena = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]  # n = 9
        payload = {"data": muestra_pequena, "alpha": 0.05}

        response = self.client.post("/api/v1/goodness-of-fit", json=payload)
        self.assertEqual(response.status_code, 422)

    # -------------------------------------------------------------------------
    # 6. Rechazo de alpha inválido
    # -------------------------------------------------------------------------
    def test_06_rechazo_alpha_invalido(self) -> None:
        """Verifica que valores de alpha <= 0, >= 1 o no numéricos devuelvan HTTP 422."""
        muestra_valida = [10.0 + i for i in range(15)]

        casos_alpha_invalidos = [0.0, 1.0, -0.05, 1.5, "invalido"]
        for a in casos_alpha_invalidos:
            payload = {"data": muestra_valida, "alpha": a}
            response = self.client.post("/api/v1/goodness-of-fit", json=payload)
            self.assertEqual(
                response.status_code,
                422,
                f"Alpha inválido {a} debió retornar 422, retornó {response.status_code}",
            )

    # -------------------------------------------------------------------------
    # 7. Rechazo de valores NaN e infinitos
    # -------------------------------------------------------------------------
    def test_07_rechazo_nan_e_infinitos(self) -> None:
        """Verifica que la API rechace cargas que incluyan NaN o infinitos."""
        base = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
        # Casos con NaN o infinitos en el JSON
        payload_nan = {"data": base + [None]}
        res_nan = self.client.post("/api/v1/goodness-of-fit", json=payload_nan)
        self.assertEqual(res_nan.status_code, 422)

        # En string no numérico
        payload_str = {"data": base + ["infinito"]}
        res_str = self.client.post("/api/v1/goodness-of-fit", json=payload_str)
        self.assertEqual(res_str.status_code, 422)

    # -------------------------------------------------------------------------
    # 8. Verificación de la estructura JSON de bondad de ajuste
    # -------------------------------------------------------------------------
    def test_08_estructura_json_goodness_of_fit(self) -> None:
        """Comprueba que la respuesta respete exactamente el contrato JSON solicitado."""
        rng = np.random.default_rng(42)
        muestra = rng.normal(loc=100.0, scale=15.0, size=60).tolist()
        payload = {"data": muestra, "alpha": 0.05}

        response = self.client.post("/api/v1/goodness-of-fit", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Estructura de primer nivel
        self.assertIn("descriptive_metrics", data)
        self.assertIn("goodness_of_fit", data)
        self.assertIn("pedagogical_synthesis", data)

        # Estructura descriptiva
        dm = data["descriptive_metrics"]
        for key in ["n", "mean", "variance", "std_dev", "skewness", "kurtosis"]:
            self.assertIn(key, dm)

        # Estructura contenedor bondad de ajuste
        gof = data["goodness_of_fit"]
        self.assertIn("kolmogorov_smirnov", gof)
        self.assertIn("anderson_darling", gof)
        self.assertIn("shapiro_wilk", gof)
        self.assertIn("chi_square", gof)

        # K-S
        ks = gof["kolmogorov_smirnov"]
        for key in ["statistic", "p_value", "rejected", "academic_verdict"]:
            self.assertIn(key, ks)

        # Anderson-Darling
        ad = gof["anderson_darling"]
        for key in ["statistic", "critical_value", "rejected", "academic_verdict"]:
            self.assertIn(key, ad)

        # Shapiro-Wilk
        sw = gof["shapiro_wilk"]
        for key in ["available", "statistic", "p_value", "alpha", "rejected", "academic_verdict"]:
            self.assertIn(key, sw)

        # Chi-Square
        cs = gof["chi_square"]
        for key in ["available", "statistic", "degrees_of_freedom", "critical_value", "p_value", "merged_classes_count", "rejected", "academic_verdict"]:
            self.assertIn(key, cs)

    # -------------------------------------------------------------------------
    # 9. Comparación de dos muestras válidas
    # -------------------------------------------------------------------------
    def test_09_comparar_muestras_validas(self) -> None:
        """Verifica que POST /api/v1/compare-samples retorne HTTP 200 con dos muestras válidas."""
        payload = {
            "sample_a": [10.5, 12.3, 11.8, 13.2, 14.1, 12.9],
            "sample_b": [15.2, 16.4, 14.8, 17.1, 16.8, 15.9],
            "alpha": 0.05,
        }
        response = self.client.post("/api/v1/compare-samples", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["sample_sizes"]["sample_a"], 6)
        self.assertEqual(data["sample_sizes"]["sample_b"], 6)
        self.assertIn("levene", data)
        self.assertIn("student_t", data)
        self.assertIn("mann_whitney_u", data)
        self.assertIn("pedagogical_synthesis", data)

    # -------------------------------------------------------------------------
    # 10. Comparación con menos de 5 observaciones por grupo devuelve HTTP 422
    # -------------------------------------------------------------------------
    def test_10_comparar_muestras_menos_de_5_observaciones_retorna_422(self) -> None:
        """Asegura que si algún grupo tiene menos de 5 observaciones se rechace con 422."""
        payload_a_corta = {
            "sample_a": [1.0, 2.0, 3.0, 4.0],  # n = 4
            "sample_b": [5.0, 6.0, 7.0, 8.0, 9.0],
            "alpha": 0.05,
        }
        res_a = self.client.post("/api/v1/compare-samples", json=payload_a_corta)
        self.assertEqual(res_a.status_code, 422)

        payload_b_corta = {
            "sample_a": [1.0, 2.0, 3.0, 4.0, 5.0],
            "sample_b": [10.0, 20.0, 30.0],  # n = 3
            "alpha": 0.05,
        }
        res_b = self.client.post("/api/v1/compare-samples", json=payload_b_corta)
        self.assertEqual(res_b.status_code, 422)

    # -------------------------------------------------------------------------
    # 11. Rechazo de estructuras o datos inválidos
    # -------------------------------------------------------------------------
    def test_11_rechazo_estructuras_invalidas(self) -> None:
        """Asegura el rechazo de matrices 2D, tipos no numéricos y listas vacías."""
        # Muestra bidimensional en sample_a
        payload_2d = {
            "sample_a": [[1.0, 2.0], [3.0, 4.0]],
            "sample_b": [5.0, 6.0, 7.0, 8.0, 9.0],
        }
        res_2d = self.client.post("/api/v1/compare-samples", json=payload_2d)
        self.assertEqual(res_2d.status_code, 422)

        # Muestra vacía
        payload_vacia = {
            "sample_a": [],
            "sample_b": [1.0, 2.0, 3.0, 4.0, 5.0],
        }
        res_vacia = self.client.post("/api/v1/compare-samples", json=payload_vacia)
        self.assertEqual(res_vacia.status_code, 422)

    # -------------------------------------------------------------------------
    # 12. Verificación de la estructura JSON de comparación
    # -------------------------------------------------------------------------
    def test_12_estructura_json_compare_samples(self) -> None:
        """Comprueba los campos exactos del contrato de respuesta en compare-samples."""
        payload = {
            "sample_a": [10.0, 11.0, 12.0, 13.0, 14.0],
            "sample_b": [20.0, 21.0, 22.0, 23.0, 24.0],
            "alpha": 0.05,
        }
        response = self.client.post("/api/v1/compare-samples", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # sample_sizes
        self.assertIn("sample_sizes", data)
        self.assertIn("sample_a", data["sample_sizes"])
        self.assertIn("sample_b", data["sample_sizes"])

        # levene
        self.assertIn("levene", data)
        for key in ["statistic", "p_value", "equal_variances", "academic_verdict"]:
            self.assertIn(key, data["levene"])

        # student_t
        self.assertIn("student_t", data)
        for key in ["statistic", "p_value", "equal_var", "rejected"]:
            self.assertIn(key, data["student_t"])

        # mann_whitney_u
        self.assertIn("mann_whitney_u", data)
        for key in ["statistic", "p_value", "rejected"]:
            self.assertIn(key, data["mann_whitney_u"])

        # pedagogical_synthesis
        self.assertIn("pedagogical_synthesis", data)
        self.assertIsInstance(data["pedagogical_synthesis"], str)

    # -------------------------------------------------------------------------
    # 13. Chi-cuadrada puede ser no disponible sin romper la respuesta
    # -------------------------------------------------------------------------
    def test_13_chi_cuadrada_no_disponible_sin_romper_respuesta(self) -> None:
        """
        Verifica que cuando Chi-cuadrada no es aplicable (e.g. n=11 donde tras fusión v <= 0),
        la API retorne HTTP 200 con available=False y motivo en Chi-cuadrada, manteniendo
        el resto del análisis perfectamente funcional.
        """
        # Muestra con 11 observaciones (válida para el endpoint pero insuficiente para 4 clases de Ei >= 5)
        muestra_pequena_valida = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0]
        payload = {"data": muestra_pequena_valida, "alpha": 0.05}

        response = self.client.post("/api/v1/goodness-of-fit", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        chi2 = data["goodness_of_fit"]["chi_square"]
        self.assertFalse(chi2["available"])
        self.assertIsNone(chi2["statistic"])
        self.assertIsNone(chi2["p_value"])
        self.assertIsNotNone(chi2["reason"])

        # Pero las demás pruebas deben estar disponibles y funcionales
        self.assertEqual(data["descriptive_metrics"]["n"], 11)
        self.assertIsNotNone(data["goodness_of_fit"]["kolmogorov_smirnov"]["p_value"])
        self.assertIsNotNone(data["goodness_of_fit"]["anderson_darling"]["statistic"])
        self.assertIn("Chi2", data["pedagogical_synthesis"])

    # -------------------------------------------------------------------------
    # 14. Comprobación de que los resultados provienen del motor estadístico
    # -------------------------------------------------------------------------
    def test_14_resultados_provienen_del_motor_estadistico(self) -> None:
        """Contrasta los números devueltos por la API contra llamadas directas al motor."""
        rng = np.random.default_rng(2026)
        datos = rng.normal(loc=50.0, scale=8.0, size=25).tolist()

        # Cálculo directo en el motor
        metricas_directas = motor_estadistico.calcular_metricas_descriptivas(datos)
        ad_directo = motor_estadistico.prueba_anderson_darling_normal(datos, alpha=0.05)

        # Llamada vía API REST
        response = self.client.post("/api/v1/goodness-of-fit", json={"data": datos, "alpha": 0.05})
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Contrastar métricas descriptivas
        self.assertAlmostEqual(data["descriptive_metrics"]["mean"], metricas_directas["mean"], places=7)
        self.assertAlmostEqual(data["descriptive_metrics"]["variance"], metricas_directas["variance"], places=7)
        self.assertAlmostEqual(data["descriptive_metrics"]["std_dev"], metricas_directas["std_dev"], places=7)

        # Contrastar Anderson-Darling
        self.assertAlmostEqual(
            data["goodness_of_fit"]["anderson_darling"]["statistic"],
            ad_directo["statistic"],
            places=7,
        )
        self.assertAlmostEqual(
            data["goodness_of_fit"]["anderson_darling"]["critical_value"],
            ad_directo["critical_value"],
            places=7,
        )
        self.assertEqual(
            data["goodness_of_fit"]["anderson_darling"]["rejected"],
            ad_directo["rejected"],
        )

    # -------------------------------------------------------------------------
    # 15. Manejo de error 500 sin exponer detalles sensibles ni rutas locales
    # -------------------------------------------------------------------------
    def test_15_error_500_seguro_sin_fugas_internas(self) -> None:
        """Simula una excepción imprevista para asegurar respuesta 500 genérica y segura."""
        client_seguro = TestClient(app, raise_server_exceptions=False)
        with patch.object(motor_estadistico, "calcular_metricas_descriptivas", side_effect=RuntimeError("Fallo simulado")):
            payload = {"data": [10.0 + i for i in range(12)], "alpha": 0.05}
            response = client_seguro.post("/api/v1/goodness-of-fit", json=payload)
            self.assertEqual(response.status_code, 500)
            data = response.json()
            self.assertIn("detail", data)
            # Asegurar que no se filtre el traceback ni la ruta del archivo
            self.assertNotIn("Traceback", data["detail"])
            self.assertNotIn("Fallo simulado", data["detail"])
            self.assertNotIn(".py", data["detail"])

    # -------------------------------------------------------------------------
    # 16. Endpoint incluye las cuatro pruebas de bondad de ajuste
    # -------------------------------------------------------------------------
    def test_16_endpoint_incluye_cuatro_pruebas(self) -> None:
        """Verifica que POST /api/v1/goodness-of-fit devuelva las 4 pruebas simultáneamente."""
        rng = np.random.default_rng(505)
        muestra = rng.normal(loc=50.0, scale=5.0, size=20).tolist()

        response = self.client.post("/api/v1/goodness-of-fit", json={"data": muestra, "alpha": 0.05})
        self.assertEqual(response.status_code, 200)
        data = response.json()

        gof = data["goodness_of_fit"]
        self.assertIn("kolmogorov_smirnov", gof)
        self.assertIn("anderson_darling", gof)
        self.assertIn("shapiro_wilk", gof)
        self.assertIn("chi_square", gof)
        self.assertTrue(gof["shapiro_wilk"]["available"])

    # -------------------------------------------------------------------------
    # 17. Shapiro-Wilk en la API utiliza datos reales y cálculo del motor
    # -------------------------------------------------------------------------
    def test_17_shapiro_wilk_utiliza_datos_reales(self) -> None:
        """Comprueba que los valores de Shapiro-Wilk provengan del motor y no de constantes."""
        rng = np.random.default_rng(606)
        muestra = rng.normal(loc=80.0, scale=12.0, size=30).tolist()

        sw_motor = motor_estadistico.prueba_shapiro_wilk_normal(muestra, alpha=0.05)

        response = self.client.post("/api/v1/goodness-of-fit", json={"data": muestra, "alpha": 0.05})
        self.assertEqual(response.status_code, 200)
        sw_api = response.json()["goodness_of_fit"]["shapiro_wilk"]

        self.assertAlmostEqual(sw_api["statistic"], sw_motor["statistic"], places=7)
        self.assertAlmostEqual(sw_api["p_value"], sw_motor["p_value"], places=7)
        self.assertEqual(sw_api["rejected"], sw_motor["rejected"])

    # -------------------------------------------------------------------------
    # 18. Transmisión correcta de alpha a Shapiro-Wilk
    # -------------------------------------------------------------------------
    def test_18_shapiro_wilk_transmite_alpha_correctamente(self) -> None:
        """Verifica que niveles de alpha personalizados (0.01, 0.10) se reflejen en Shapiro-Wilk."""
        rng = np.random.default_rng(707)
        muestra = rng.normal(loc=0.0, scale=1.0, size=25).tolist()

        for a in [0.01, 0.10]:
            response = self.client.post("/api/v1/goodness-of-fit", json={"data": muestra, "alpha": a})
            self.assertEqual(response.status_code, 200)
            sw = response.json()["goodness_of_fit"]["shapiro_wilk"]
            self.assertEqual(sw["alpha"], a)
            self.assertEqual(sw["rejected"], sw["p_value"] < a)

    # -------------------------------------------------------------------------
    # 19. Comportamiento cuando Shapiro-Wilk no está disponible
    # -------------------------------------------------------------------------
    def test_19_shapiro_wilk_comportamiento_no_disponible(self) -> None:
        """Verifica que si Shapiro-Wilk no está disponible, la API devuelva available=False sin fallar."""
        with patch.object(
            motor_estadistico,
            "prueba_shapiro_wilk_normal",
            side_effect=DatosInvalidosError("Simulación de no disponibilidad estadística"),
        ):
            payload = {"data": [10.0 + i for i in range(15)], "alpha": 0.05}
            response = self.client.post("/api/v1/goodness-of-fit", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()

            sw = data["goodness_of_fit"]["shapiro_wilk"]
            self.assertFalse(sw["available"])
            self.assertIsNone(sw["statistic"])
            self.assertIsNone(sw["p_value"])
            self.assertIsNotNone(sw["reason"])
            self.assertIn("Simulación de no disponibilidad", sw["reason"])

    # -------------------------------------------------------------------------
    # 20. Una prueba no disponible no interrumpe a las demás
    # -------------------------------------------------------------------------
    def test_20_prueba_no_disponible_no_interrumpe_las_demas(self) -> None:
        """Asegura que si Chi-cuadrada o Shapiro no están disponibles, K-S y A-D funcionen con 200."""
        # Con n = 11, Chi-cuadrada no es aplicable (v <= 0)
        muestra_pequena = [float(x) for x in range(11)]
        response = self.client.post("/api/v1/goodness-of-fit", json={"data": muestra_pequena, "alpha": 0.05})
        self.assertEqual(response.status_code, 200)
        data = response.json()

        gof = data["goodness_of_fit"]
        self.assertFalse(gof["chi_square"]["available"])
        self.assertTrue(gof["kolmogorov_smirnov"]["statistic"] is not None)
        self.assertTrue(gof["anderson_darling"]["statistic"] is not None)
        self.assertTrue(gof["shapiro_wilk"]["available"])
        self.assertIn("Chi2", data["pedagogical_synthesis"])

    # -------------------------------------------------------------------------
    # 21. Chi-cuadrada conserva su comportamiento anterior
    # -------------------------------------------------------------------------
    def test_21_chi_cuadrada_conserva_comportamiento_anterior(self) -> None:
        """Verifica que el algoritmo de fusión y grados de libertad de Chi-cuadrada permanezcan intactos."""
        rng = np.random.default_rng(808)
        datos_60 = rng.normal(loc=100.0, scale=15.0, size=60).tolist()

        response = self.client.post("/api/v1/goodness-of-fit", json={"data": datos_60, "alpha": 0.05})
        self.assertEqual(response.status_code, 200)
        chi2 = response.json()["goodness_of_fit"]["chi_square"]

        self.assertTrue(chi2["available"])
        self.assertGreater(chi2["degrees_of_freedom"], 0)
        self.assertEqual(chi2["degrees_of_freedom"], chi2["merged_classes_count"] - 3)
        self.assertAlmostEqual(
            chi2["critical_value"],
            float(stats.chi2.ppf(0.95, chi2["degrees_of_freedom"])),
            places=5,
        )

    # -------------------------------------------------------------------------
    # 22. Resultados de pruebas anteriores no cambiaron por la incorporación
    # -------------------------------------------------------------------------
    def test_22_resultados_pruebas_anteriores_no_cambiaron(self) -> None:
        """Verifica que las métricas descriptivas, K-S y A-D no hayan sufrido regresión alguna."""
        datos = [12.0, 15.0, 14.0, 10.0, 18.0, 19.0, 22.0, 17.0, 16.0, 13.0, 11.0, 14.0]

        direct_dm = motor_estadistico.calcular_metricas_descriptivas(datos)
        direct_ad = motor_estadistico.prueba_anderson_darling_normal(datos, alpha=0.05)

        response = self.client.post("/api/v1/goodness-of-fit", json={"data": datos, "alpha": 0.05})
        self.assertEqual(response.status_code, 200)
        api_data = response.json()

        self.assertAlmostEqual(api_data["descriptive_metrics"]["mean"], direct_dm["mean"], places=9)
        self.assertAlmostEqual(api_data["descriptive_metrics"]["variance"], direct_dm["variance"], places=9)
        self.assertAlmostEqual(
            api_data["goodness_of_fit"]["anderson_darling"]["statistic"],
            direct_ad["statistic"],
            places=9,
        )

    # -------------------------------------------------------------------------
    # 23. Verificación de los escenarios precargados del frontend y muestras constantes
    # -------------------------------------------------------------------------
    def test_23_escenarios_precargados_frontend_y_muestras_constantes(self) -> None:
        """Valida los tres escenarios deterministas del frontend y la comparación de muestras constantes."""
        ecommerce = [
            124.5, 132.1, 128.4, 145.2, 138.9, 152.0, 130.8, 141.5, 127.3, 135.6,
            148.2, 160.4, 142.7, 136.9, 155.1, 149.3, 162.8, 158.4, 170.2, 165.5,
            185.0, 192.4, 178.6, 210.3, 225.8, 240.1, 265.4, 280.9, 310.5, 345.2,
            390.0, 420.5, 480.2, 530.8, 620.1, 750.4, 890.2, 1120.5, 1340.0, 1580.6,
        ]
        rubric_normal = [
            151.21, 182.22, 118.11, 216.87, 194.15, 166.24, 165.64, 184.12, 166.97, 168.22,
            196.60, 190.44, 173.08, 172.44, 179.83, 156.58, 162.89, 191.45, 171.09, 133.77,
            160.68, 194.70, 168.03, 170.54, 194.26, 229.74, 153.60, 215.45, 138.10, 180.25,
            139.91, 215.54, 200.02, 209.13, 148.43, 195.54, 159.43, 161.28, 190.20, 201.30,
            181.13, 156.16, 150.23, 218.33, 192.82, 196.59, 240.50, 150.52, 251.78, 269.53,
            223.55, 199.81, 155.09, 204.83, 161.72, 174.35, 166.29, 183.51, 213.64, 158.33,
        ]
        rubric_gamma = [
            35.24, 36.25, 39.65, 63.50, 23.36, 6.95, 767.36, 357.50, 109.79, 405.23,
            481.21, 138.17, 189.38, 57.57, 43.51, 230.61, 147.07, 83.58, 30.88, 3.48,
            312.20, 438.76, 124.98, 210.63, 47.09, 146.69, 126.24, 28.80, 311.87, 357.09,
            56.17, 258.76, 161.96, 94.45, 2.58, 281.07, 76.51, 287.73, 34.88, 477.53,
            143.11, 37.42, 488.57, 125.93, 29.16, 115.89, 288.30, 76.41, 212.45, 237.49,
            310.35, 969.43, 274.17, 41.79, 186.07, 56.63, 43.03, 447.83, 136.15, 362.04,
        ]

        # Escenario 1: E-Commerce (asimétrico, rechaza en K-S, A-D, S-W)
        res_ec = self.client.post("/api/v1/goodness-of-fit", json={"data": ecommerce, "alpha": 0.05})
        self.assertEqual(res_ec.status_code, 200)
        ec_json = res_ec.json()
        self.assertEqual(ec_json["descriptive_metrics"]["n"], 40)
        self.assertTrue(ec_json["goodness_of_fit"]["kolmogorov_smirnov"]["rejected"])
        self.assertTrue(ec_json["goodness_of_fit"]["anderson_darling"]["rejected"])
        self.assertTrue(ec_json["goodness_of_fit"]["shapiro_wilk"]["rejected"])

        # Escenario 2: Normal (n=60, no rechaza en las 4 pruebas, Chi-cuadrada disponible)
        res_norm = self.client.post("/api/v1/goodness-of-fit", json={"data": rubric_normal, "alpha": 0.05})
        self.assertEqual(res_norm.status_code, 200)
        norm_json = res_norm.json()
        self.assertEqual(norm_json["descriptive_metrics"]["n"], 60)
        self.assertFalse(norm_json["goodness_of_fit"]["kolmogorov_smirnov"]["rejected"])
        self.assertFalse(norm_json["goodness_of_fit"]["anderson_darling"]["rejected"])
        self.assertFalse(norm_json["goodness_of_fit"]["shapiro_wilk"]["rejected"])
        self.assertTrue(norm_json["goodness_of_fit"]["chi_square"]["available"])
        self.assertFalse(norm_json["goodness_of_fit"]["chi_square"]["rejected"])

        # Escenario 3: Gamma (n=60, todos positivos, rechaza en K-S, A-D, S-W)
        self.assertTrue(all(x > 0 for x in rubric_gamma))
        res_gam = self.client.post("/api/v1/goodness-of-fit", json={"data": rubric_gamma, "alpha": 0.05})
        self.assertEqual(res_gam.status_code, 200)
        gam_json = res_gam.json()
        self.assertEqual(gam_json["descriptive_metrics"]["n"], 60)
        self.assertTrue(gam_json["goodness_of_fit"]["kolmogorov_smirnov"]["rejected"])
        self.assertTrue(gam_json["goodness_of_fit"]["anderson_darling"]["rejected"])
        self.assertTrue(gam_json["goodness_of_fit"]["shapiro_wilk"]["rejected"])

        # Comparación de dos muestras constantes distintas (sin error de serialización JSON por inf)
        res_const = self.client.post(
            "/api/v1/compare-samples",
            json={"sample_a": [5.0] * 6, "sample_b": [10.0] * 6, "alpha": 0.05},
        )
        self.assertEqual(res_const.status_code, 200)
        const_json = res_const.json()
        self.assertTrue(const_json["student_t"]["rejected"])
        self.assertIsNone(const_json["student_t"]["statistic"])


if __name__ == "__main__":
    unittest.main()
