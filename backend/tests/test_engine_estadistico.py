"""
Pruebas unitarias para el motor estadístico (MotorEstadistico).

Verifica de forma rigurosa los 15 puntos obligatorios definidos en la especificación
de la Etapa 1, empleando el módulo estándar unittest y datos sintéticos reproducibles.
"""

import math
import unittest
import numpy as np
import scipy.stats as stats

try:
    from backend.engine_estadistico import (
        MotorEstadistico,
        DatosInvalidosError,
        ParametroInvalidoError,
    )
except ImportError:
    from engine_estadistico import (
        MotorEstadistico,
        DatosInvalidosError,
        ParametroInvalidoError,
    )


class TestMotorEstadistico(unittest.TestCase):
    """Batería exhaustiva de pruebas unitarias para MotorEstadistico."""

    def setUp(self) -> None:
        """Inicializa una instancia del motor estadístico antes de cada prueba."""
        self.motor = MotorEstadistico()

    # -------------------------------------------------------------------------
    # 1. Cálculo correcto de la media
    # -------------------------------------------------------------------------
    def test_01_calculo_media(self) -> None:
        """Comprueba el cálculo exacto de la media aritmética frente a un valor analítico."""
        datos = [2.0, 4.0, 6.0, 8.0, 10.0]
        metricas = self.motor.calcular_metricas_descriptivas(datos)

        self.assertEqual(metricas["n"], 5)
        self.assertIsInstance(metricas["mean"], float)
        self.assertAlmostEqual(metricas["mean"], 6.0, places=10)

        # Muestra con decimales
        datos_float = [1.25, 2.75, 5.0, 3.0]
        metricas_float = self.motor.calcular_metricas_descriptivas(datos_float)
        self.assertAlmostEqual(metricas_float["mean"], 3.0, places=10)

    # -------------------------------------------------------------------------
    # 2. Cálculo correcto de varianza muestral y desviación estándar (ddof=1)
    # -------------------------------------------------------------------------
    def test_02_calculo_varianza_y_desviacion(self) -> None:
        """Verifica que varianza y desviación estándar usen ddof=1 y coincidan con fórmulas exactas."""
        datos = [10.0, 12.0, 23.0, 23.0, 16.0, 23.0, 21.0, 16.0]
        # Suma de x: 144, n = 8, media = 18.0
        # Desviaciones: [-8, -6, 5, 5, -2, 5, 3, -2]
        # Cuadrados: [64, 36, 25, 25, 4, 25, 9, 4] -> suma = 192
        # Varianza muestral = 192 / (8 - 1) = 192 / 7 = 27.428571428571427
        esperado_var = 192.0 / 7.0
        esperado_std = math.sqrt(esperado_var)

        metricas = self.motor.calcular_metricas_descriptivas(datos)
        self.assertIsInstance(metricas["variance"], float)
        self.assertIsInstance(metricas["std_dev"], float)
        self.assertAlmostEqual(metricas["variance"], esperado_var, places=10)
        self.assertAlmostEqual(metricas["std_dev"], esperado_std, places=10)

    # -------------------------------------------------------------------------
    # 3. Manejo de tamaños de muestra insuficientes para asimetría y curtosis
    # -------------------------------------------------------------------------
    def test_03_muestras_insuficientes_asimetria_y_curtosis(self) -> None:
        """Verifica que cuando n no permite calcular medidas válidas se retorne None sin generar NaN."""
        # n = 1: no se puede varianza, desviación, asimetría ni curtosis
        res_1 = self.motor.calcular_metricas_descriptivas([42.0])
        self.assertEqual(res_1["n"], 1)
        self.assertEqual(res_1["mean"], 42.0)
        self.assertIsNone(res_1["variance"])
        self.assertIsNone(res_1["std_dev"])
        self.assertIsNone(res_1["skewness"])
        self.assertIsNone(res_1["kurtosis"])

        # n = 2: varianza y std disponibles; asimetría y curtosis deben ser None
        res_2 = self.motor.calcular_metricas_descriptivas([10.0, 20.0])
        self.assertEqual(res_2["n"], 2)
        self.assertIsNotNone(res_2["variance"])
        self.assertIsNotNone(res_2["std_dev"])
        self.assertIsNone(res_2["skewness"])
        self.assertIsNone(res_2["kurtosis"])

        # n = 3: asimetría disponible (Fisher-Pearson sin sesgo); curtosis debe ser None
        res_3 = self.motor.calcular_metricas_descriptivas([10.0, 20.0, 35.0])
        self.assertEqual(res_3["n"], 3)
        self.assertIsNotNone(res_3["skewness"])
        self.assertIsNone(res_3["kurtosis"])

        # n = 4: ambas disponibles
        res_4 = self.motor.calcular_metricas_descriptivas([10.0, 20.0, 35.0, 50.0])
        self.assertEqual(res_4["n"], 4)
        self.assertIsNotNone(res_4["skewness"])
        self.assertIsNotNone(res_4["kurtosis"])

    # -------------------------------------------------------------------------
    # 4. Rechazo de entradas vacías
    # -------------------------------------------------------------------------
    def test_04_rechazo_entradas_vacias(self) -> None:
        """Verifica que muestras vacías o nulas lancen DatosInvalidosError."""
        for entrada in [[], (), np.array([]), None]:
            with self.assertRaises(DatosInvalidosError):
                self.motor.calcular_metricas_descriptivas(entrada)

            with self.assertRaises(DatosInvalidosError):
                self.motor.prueba_kolmogorov_smirnov_normal(entrada)

            with self.assertRaises(DatosInvalidosError):
                self.motor.prueba_anderson_darling_normal(entrada)

    # -------------------------------------------------------------------------
    # 5. Rechazo de valores NaN, infinitos y entradas no numéricas
    # -------------------------------------------------------------------------
    def test_05_rechazo_nan_infinitos_y_no_numericos(self) -> None:
        """Comprueba que NaN, +inf, -inf y strings no numéricos sean estrictamente rechazados."""
        casos_invalidos = [
            [1.0, 2.0, float("nan"), 4.0],
            [1.0, float("inf"), 3.0],
            [-float("inf"), 2.0, 3.0],
            ["a", "b", "c"],
            [1.0, "texto", 3.0],
        ]
        for caso in casos_invalidos:
            with self.assertRaises(DatosInvalidosError):
                self.motor.calcular_metricas_descriptivas(caso)

    # -------------------------------------------------------------------------
    # 6. Rechazo de matrices o estructuras multidimensionales
    # -------------------------------------------------------------------------
    def test_06_rechazo_estructuras_no_unidimensionales(self) -> None:
        """Asegura que matrices bidimensionales o tensores lancen DatosInvalidosError."""
        matriz_2d = [[1.0, 2.0], [3.0, 4.0]]
        tensor_3d = np.ones((2, 2, 2))

        with self.assertRaises(DatosInvalidosError):
            self.motor.calcular_metricas_descriptivas(matriz_2d)

        with self.assertRaises(DatosInvalidosError):
            self.motor.calcular_metricas_descriptivas(tensor_3d)

    # -------------------------------------------------------------------------
    # 7. Reproducibilidad de K-S con la misma semilla
    # -------------------------------------------------------------------------
    def test_07_reproducibilidad_ks_con_semilla(self) -> None:
        """Verifica que fijar la semilla en K-S produzca estadísticos y p-valores idénticos."""
        rng = np.random.default_rng(999)
        muestra = rng.normal(loc=5.0, scale=1.5, size=50).tolist()

        res_a = self.motor.prueba_kolmogorov_smirnov_normal(
            muestra, alpha=0.05, seed=42, n_mc_samples=500
        )
        res_b = self.motor.prueba_kolmogorov_smirnov_normal(
            muestra, alpha=0.05, seed=42, n_mc_samples=500
        )

        self.assertEqual(res_a["statistic"], res_b["statistic"])
        self.assertEqual(res_a["p_value"], res_b["p_value"])
        self.assertEqual(res_a["rejected"], res_b["rejected"])
        self.assertIn("Lilliefors", res_a["calibration_method"])

    # -------------------------------------------------------------------------
    # 8. Anderson-Darling: comparación correcta frente al valor crítico
    # -------------------------------------------------------------------------
    def test_08_anderson_darling_comparacion_valor_critico(self) -> None:
        """Verifica la coherencia entre estadístico A^2, valor crítico y decisión en Anderson-Darling."""
        rng = np.random.default_rng(1234)
        muestra_normal = rng.normal(loc=0.0, scale=1.0, size=50).tolist()

        # Probar niveles estándar contemplados: 0.01, 0.05, 0.10
        for alpha in [0.01, 0.05, 0.10]:
            res = self.motor.prueba_anderson_darling_normal(muestra_normal, alpha=alpha)
            self.assertEqual(res["alpha"], alpha)
            self.assertIsNone(res["p_value"])  # Contrato original: p-valor no inventado
            self.assertIsInstance(res["statistic"], float)
            self.assertIsInstance(res["critical_value"], float)
            self.assertEqual(res["rejected"], res["statistic"] > res["critical_value"])
            self.assertIn("colas", res["academic_verdict"].lower())

        # Probar nivel no tabulado para verificar excepción explícita
        with self.assertRaises(ParametroInvalidoError):
            self.motor.prueba_anderson_darling_normal(muestra_normal, alpha=0.03)

        # Probar con muestra marcadamente no normal (exponencial sesgada)
        muestra_exp = rng.exponential(scale=2.0, size=100).tolist()
        res_exp = self.motor.prueba_anderson_darling_normal(muestra_exp, alpha=0.05)
        self.assertTrue(res_exp["rejected"])
        self.assertGreater(res_exp["statistic"], res_exp["critical_value"])

    # -------------------------------------------------------------------------
    # 9. Funcionamiento del algoritmo de fusión de clases
    # -------------------------------------------------------------------------
    def test_09_algoritmo_fusion_clases(self) -> None:
        """Evalúa directamente el algoritmo de fusión para asegurar invariantes de Oi, Ei y límites."""
        clases_prueba = [
            {"lower": -float("inf"), "upper": 2.0, "observed": 1, "expected": 1.2},
            {"lower": 2.0, "upper": 4.0, "observed": 3, "expected": 4.0},
            {"lower": 4.0, "upper": 6.0, "observed": 10, "expected": 12.0},
            {"lower": 6.0, "upper": 8.0, "observed": 2, "expected": 3.5},
            {"lower": 8.0, "upper": float("inf"), "observed": 1, "expected": 0.8},
        ]
        oi_total_inicial = sum(c["observed"] for c in clases_prueba)
        ei_total_inicial = sum(c["expected"] for c in clases_prueba)

        fusionadas = self.motor._fusionar_clases(clases_prueba)

        # Invariantes de conservación
        oi_total_final = sum(c["observed"] for c in fusionadas)
        ei_total_final = sum(c["expected"] for c in fusionadas)

        self.assertEqual(oi_total_final, oi_total_inicial)
        self.assertAlmostEqual(ei_total_final, ei_total_inicial, places=7)

        # Verificar continuidad de límites
        self.assertEqual(fusionadas[0]["lower"], -float("inf"))
        self.assertEqual(fusionadas[-1]["upper"], float("inf"))
        for i in range(len(fusionadas) - 1):
            self.assertEqual(fusionadas[i]["upper"], fusionadas[i + 1]["lower"])

        # Todas las clases resultantes deben tener Ei >= 5 si era factible
        for c in fusionadas:
            self.assertGreaterEqual(c["expected"], 5.0)

    # -------------------------------------------------------------------------
    # 10. Garantía de que ninguna clase válida final tenga Ei < 5
    # -------------------------------------------------------------------------
    def test_10_garantia_todas_clases_finales_ei_mayor_igual_5(self) -> None:
        """Comprueba en Chi-cuadrada que cuando available=True, toda clase tenga Ei >= 5.0."""
        rng = np.random.default_rng(777)
        datos = rng.normal(loc=20.0, scale=4.0, size=80).tolist()

        resultado = self.motor.prueba_chi_cuadrada_normal(datos, alpha=0.05)
        self.assertTrue(resultado["available"])
        self.assertGreater(len(resultado["merged_classes"]), 0)

        for c in resultado["merged_classes"]:
            self.assertGreaterEqual(c["expected_frequency"], 5.0)

    # -------------------------------------------------------------------------
    # 11. Manejo de casos donde Chi-cuadrada no es estadísticamente aplicable
    # -------------------------------------------------------------------------
    def test_11_casos_chi_cuadrada_no_aplicable(self) -> None:
        """Verifica que ante muestra pequeña o grados de libertad <= 0 se devuelva available=False."""
        # n = 10: imposible obtener 4 clases con Ei >= 5 (requeriría al menos 20 observaciones)
        datos_pequenos = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        res_chi = self.motor.prueba_chi_cuadrada_normal(datos_pequenos)

        self.assertFalse(res_chi["available"])
        self.assertIsNone(res_chi["statistic"])
        self.assertIsNone(res_chi["critical_value"])
        self.assertIsNone(res_chi["p_value"])
        self.assertIsNotNone(res_chi["reason"])
        self.assertIn("insuficientes", res_chi["reason"].lower())

    # -------------------------------------------------------------------------
    # 12. Cálculo y grados de libertad de Chi-cuadrada
    # -------------------------------------------------------------------------
    def test_12_calculo_y_grados_de_libertad_chi_cuadrada(self) -> None:
        """Comprueba v = k_ajustado - 3 y la correspondencia entre estadístico, valor crítico y valor-p."""
        rng = np.random.default_rng(2026)
        datos = rng.normal(loc=50.0, scale=10.0, size=120).tolist()

        res = self.motor.prueba_chi_cuadrada_normal(datos, alpha=0.05)
        self.assertTrue(res["available"])

        k_ajustado = res["merged_classes_count"]
        v = res["degrees_of_freedom"]
        # Regla: v = k - p - 1 con p = 2 -> v = k - 3
        self.assertEqual(v, k_ajustado - 3)
        self.assertGreater(v, 0)

        # Validación del valor crítico contra SciPy
        crit_esperado = float(stats.chi2.ppf(0.95, v))
        self.assertAlmostEqual(res["critical_value"], crit_esperado, places=7)

        # Validación del p-valor contra SciPy
        p_esperado = float(stats.chi2.sf(res["statistic"], v))
        self.assertAlmostEqual(res["p_value"], p_esperado, places=7)

        # Equivalencia de decisiones
        decision_stat = res["statistic"] > res["critical_value"]
        decision_pval = res["p_value"] < res["alpha"]
        self.assertEqual(res["rejected"], decision_stat)
        self.assertEqual(res["rejected"], decision_pval)

    # -------------------------------------------------------------------------
    # 13. Funcionamiento de Levene y selección de equal_var
    # -------------------------------------------------------------------------
    def test_13_levene_y_seleccion_equal_var(self) -> None:
        """Verifica que Levene determine dinámicamente equal_var=True o False al nivel del 5%."""
        rng = np.random.default_rng(42)

        # Caso 1: Varianzas iguales (homocedasticidad) -> equal_var = True
        g1 = rng.normal(loc=10.0, scale=2.0, size=60).tolist()
        g2 = rng.normal(loc=12.0, scale=2.0, size=60).tolist()
        comp_homo = self.motor.comparar_muestras(g1, g2, alpha=0.05)
        self.assertTrue(comp_homo["levene"]["homocedasticity"])
        self.assertTrue(comp_homo["t_test"]["equal_var"])
        self.assertIn("Student para varianzas iguales", comp_homo["t_test"]["method"])

        # Caso 2: Varianzas notablemente desiguales (heterocedasticidad) -> equal_var = False (Welch)
        g3 = rng.normal(loc=10.0, scale=0.5, size=60).tolist()
        g4 = rng.normal(loc=10.0, scale=8.0, size=60).tolist()
        comp_hetero = self.motor.comparar_muestras(g3, g4, alpha=0.05)
        self.assertFalse(comp_hetero["levene"]["homocedasticity"])
        self.assertFalse(comp_hetero["t_test"]["equal_var"])
        self.assertIn("Welch", comp_hetero["t_test"]["method"])

    # -------------------------------------------------------------------------
    # 14. Obtención de resultados de t-Student y Mann-Whitney
    # -------------------------------------------------------------------------
    def test_14_resultados_ttest_y_mann_whitney(self) -> None:
        """Comprueba contrastes de dos muestras para hipótesis nula verdadera y falsa."""
        rng = np.random.default_rng(42)

        # Muestras extraídas de la misma distribución bajo H0 (no deben rechazar H0 con alpha=0.05)
        s_a = rng.normal(loc=0.0, scale=1.0, size=30).tolist()
        s_b = rng.normal(loc=0.0, scale=1.0, size=30).tolist()
        res_h0 = self.motor.comparar_muestras(s_a, s_b, alpha=0.05)
        self.assertFalse(res_h0["t_test"]["rejected"])
        self.assertFalse(res_h0["mann_whitney_u"]["rejected"])

        # Muestras claramente distintas
        s_c = [1.0, 2.0, 3.0, 4.0, 5.0]
        s_d = [100.0, 101.0, 102.0, 103.0, 104.0]
        res_dist = self.motor.comparar_muestras(s_c, s_d, alpha=0.05)
        self.assertTrue(res_dist["t_test"]["rejected"])
        self.assertTrue(res_dist["mann_whitney_u"]["rejected"])
        self.assertIn("dominancia estocástica", res_dist["academic_interpretation"].lower())

    # -------------------------------------------------------------------------
    # 15. Manejo de muestras constantes o que produzcan resultados no finitos
    # -------------------------------------------------------------------------
    def test_15_muestras_constantes_y_resultados_no_finitos(self) -> None:
        """Verifica que muestras constantes no generen NaNs no controlados ni excepciones genéricas."""
        constante = [5.0, 5.0, 5.0, 5.0, 5.0, 5.0]

        # Métricas descriptivas: varianza 0, asimetría/curtosis None (no NaN)
        m = self.motor.calcular_metricas_descriptivas(constante)
        self.assertEqual(m["variance"], 0.0)
        self.assertEqual(m["std_dev"], 0.0)
        self.assertIsNone(m["skewness"])
        self.assertIsNone(m["kurtosis"])

        # K-S debe rechazar o lanzar DatosInvalidosError ante dispersión cero
        with self.assertRaises(DatosInvalidosError):
            self.motor.prueba_kolmogorov_smirnov_normal(constante)

        # Anderson-Darling debe lanzar DatosInvalidosError ante dispersión cero
        with self.assertRaises(DatosInvalidosError):
            self.motor.prueba_anderson_darling_normal(constante)

        # Shapiro-Wilk debe lanzar DatosInvalidosError ante dispersión cero
        with self.assertRaises(DatosInvalidosError):
            self.motor.prueba_shapiro_wilk_normal(constante)

        # Chi-cuadrada debe reportar available=False sin error
        res_chi = self.motor.prueba_chi_cuadrada_normal(constante)
        self.assertFalse(res_chi["available"])
        self.assertIn("desviación estándar igual a cero", res_chi["reason"])

        # Comparar muestras con dos grupos constantes
        comp_const = self.motor.comparar_muestras(constante, [5.0] * 6)
        self.assertFalse(comp_const["t_test"]["rejected"])
        self.assertFalse(math.isnan(comp_const["levene"]["statistic"]))

    # -------------------------------------------------------------------------
    # 16. Validación de nivel de significancia y síntesis pedagógica
    # -------------------------------------------------------------------------
    def test_16_validaciones_alpha_y_sintesis_pedagogica(self) -> None:
        """Verifica el rechazo de alpha fuera de (0, 1) y la generación correcta de síntesis."""
        for alpha_invalido in [0.0, 1.0, -0.05, 1.5, "invalido"]:
            with self.assertRaises(ParametroInvalidoError):
                self.motor._validar_alpha(alpha_invalido)

        # Síntesis pedagógica a partir del flujo completo
        rng = np.random.default_rng(555)
        muestra = rng.normal(loc=15.0, scale=3.0, size=70).tolist()
        resultado_completo = self.motor.analizar_bondad_ajuste_completa(
            muestra, alpha=0.05, seed=123, n_mc_samples=500
        )

        sintesis = resultado_completo["pedagogical_synthesis"]
        self.assertIn("H0 (Hipótesis Nula)", sintesis)
        self.assertIn("Ha (Hipótesis Alternativa)", sintesis)
        self.assertIn("Kolmogorov-Smirnov", sintesis)
        self.assertIn("Anderson-Darling", sintesis)
        self.assertIn("Shapiro-Wilk", sintesis)
        self.assertIn("Chi-cuadrada", sintesis)
        self.assertIn("colas", sintesis.lower())

    # -------------------------------------------------------------------------
    # 17. Shapiro-Wilk con muestra válida
    # -------------------------------------------------------------------------
    def test_17_shapiro_wilk_muestra_valida(self) -> None:
        """Verifica la ejecución correcta de Shapiro-Wilk sobre una muestra normal válida."""
        rng = np.random.default_rng(101)
        datos = rng.normal(loc=25.0, scale=3.0, size=40).tolist()

        res = self.motor.prueba_shapiro_wilk_normal(datos, alpha=0.05)
        self.assertTrue(res["available"])
        self.assertIsInstance(res["statistic"], float)
        self.assertIsInstance(res["p_value"], float)
        self.assertEqual(res["alpha"], 0.05)
        self.assertIsInstance(res["rejected"], bool)
        self.assertEqual(res["method"], "Shapiro-Wilk")
        self.assertEqual(res["warnings"], [])
        self.assertIn("Shapiro-Wilk", res["academic_verdict"])
        self.assertIn("H0", res["academic_verdict"])

    # -------------------------------------------------------------------------
    # 18. Verificación numérica del estadístico W y valor-p de Shapiro-Wilk
    # -------------------------------------------------------------------------
    def test_18_shapiro_wilk_verificacion_w_y_pvalor(self) -> None:
        """Contrasta el estadístico W y valor-p devueltos contra SciPy directamente."""
        rng = np.random.default_rng(202)
        datos = rng.normal(loc=0.0, scale=1.0, size=35).tolist()

        res_motor = self.motor.prueba_shapiro_wilk_normal(datos, alpha=0.05)
        res_scipy = stats.shapiro(datos)

        self.assertAlmostEqual(res_motor["statistic"], float(res_scipy.statistic), places=9)
        self.assertAlmostEqual(res_motor["p_value"], float(res_scipy.pvalue), places=9)

    # -------------------------------------------------------------------------
    # 19. Decisión formal según alpha en Shapiro-Wilk
    # -------------------------------------------------------------------------
    def test_19_shapiro_wilk_decision_segun_alpha(self) -> None:
        """Verifica que la decisión formal refleje p < alpha para H0 verdadera y falsa."""
        rng = np.random.default_rng(303)

        # Muestra normal bajo H0 (no debe rechazar H0 al 5%)
        normal_data = rng.normal(loc=10.0, scale=2.0, size=50).tolist()
        res_norm = self.motor.prueba_shapiro_wilk_normal(normal_data, alpha=0.05)
        self.assertFalse(res_norm["rejected"])
        self.assertGreaterEqual(res_norm["p_value"], 0.05)

        # Muestra marcadamente no normal (exponencial sesgada, debe rechazar H0)
        exp_data = rng.exponential(scale=1.5, size=80).tolist()
        res_exp = self.motor.prueba_shapiro_wilk_normal(exp_data, alpha=0.05)
        self.assertTrue(res_exp["rejected"])
        self.assertLess(res_exp["p_value"], 0.05)

    # -------------------------------------------------------------------------
    # 20. Rechazo de muestras con menos de tres observaciones
    # -------------------------------------------------------------------------
    def test_20_shapiro_wilk_rechazo_menos_de_tres_observaciones(self) -> None:
        """Verifica que muestras con n < 3 lancen DatosInvalidosError."""
        for entrada in [[], [10.0], [10.0, 20.0]]:
            with self.assertRaises(DatosInvalidosError):
                self.motor.prueba_shapiro_wilk_normal(entrada)

    # -------------------------------------------------------------------------
    # 21. Rechazo de datos NaN e infinitos en Shapiro-Wilk
    # -------------------------------------------------------------------------
    def test_21_shapiro_wilk_rechazo_nan_e_infinitos(self) -> None:
        """Asegura que NaN, +inf, -inf y cadenas sean rechazados por Shapiro-Wilk."""
        entradas_invalidas = [
            [1.0, 2.0, float("nan")],
            [1.0, float("inf"), 3.0],
            [-float("inf"), 2.0, 4.0],
            ["x", "y", "z"],
        ]
        for entrada in entradas_invalidas:
            with self.assertRaises(DatosInvalidosError):
                self.motor.prueba_shapiro_wilk_normal(entrada)

    # -------------------------------------------------------------------------
    # 22. Manejo de muestras constantes en Shapiro-Wilk
    # -------------------------------------------------------------------------
    def test_22_shapiro_wilk_manejo_muestras_constantes(self) -> None:
        """Verifica que muestras con dispersión cero sean rechazadas indicando imposibilidad de evaluación."""
        constante = [7.0, 7.0, 7.0, 7.0, 7.0]
        with self.assertRaises(DatosInvalidosError) as ctx:
            self.motor.prueba_shapiro_wilk_normal(constante)
        self.assertIn("dispersión nula", str(ctx.exception).lower())

    # -------------------------------------------------------------------------
    # 23. Comportamiento con más de 5000 observaciones y advertencia
    # -------------------------------------------------------------------------
    def test_23_shapiro_wilk_advertencia_mas_de_5000_observaciones(self) -> None:
        """Comprueba que muestras con N > 5000 incluyan advertencia sobre precisión de SciPy."""
        rng = np.random.default_rng(404)

        # Muestra menor a 5000 (sin advertencias)
        pequena = rng.normal(loc=0.0, scale=1.0, size=200).tolist()
        res_peq = self.motor.prueba_shapiro_wilk_normal(pequena, alpha=0.05)
        self.assertEqual(len(res_peq["warnings"]), 0)

        # Muestra mayor a 5000 (debe incluir advertencia documentada)
        grande = rng.normal(loc=0.0, scale=1.0, size=5005).tolist()
        res_grande = self.motor.prueba_shapiro_wilk_normal(grande, alpha=0.05)
        self.assertGreater(len(res_grande["warnings"]), 0)
        self.assertIn("5000", res_grande["warnings"][0])


if __name__ == "__main__":
    unittest.main()
