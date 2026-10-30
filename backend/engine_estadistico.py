"""
Módulo del Motor Estadístico para la Suite de Inferencia Estadística y Bondad de Ajuste.

Desarrollado para la asignatura Estadística para Ingeniería (Universidad de Medellín, 2026-2).
Contiene la clase MotorEstadistico con los métodos para:
- Validación y preparación rigurosa de datos numéricos.
- Cálculo de métricas estadísticas descriptivas muestrales.
- Prueba de normalidad de Kolmogorov-Smirnov con p-valor calibrado por Monte Carlo (Lilliefors paramétrico).
- Prueba de normalidad de Anderson-Darling con selección dinámica de valores críticos.
- Prueba de bondad de ajuste Chi-cuadrada de Pearson con regla de k inicial (2^k > n),
  soporte real completo (-inf a +inf), y algoritmo determinístico de fusión de clases (Ei >= 5).
- Comparación de dos muestras independientes (Levene al 5%, t-Student / Welch bilateral y Mann-Whitney U bilateral).
- Generación de síntesis pedagógica dinámica e integrada.
"""

from __future__ import annotations

import math
import warnings
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import scipy.stats as stats


class ErrorEstadistico(Exception):
    """Excepción base para errores del motor estadístico."""
    pass


class DatosInvalidosError(ValueError, ErrorEstadistico):
    """Excepción lanzada cuando los datos de entrada no cumplen las condiciones requeridas."""
    pass


class ParametroInvalidoError(ValueError, ErrorEstadistico):
    """Excepción lanzada cuando un parámetro de configuración (e.g. alpha) es inválido."""
    pass


class MotorEstadistico:
    """
    Motor estadístico computacional para inferencia y pruebas de bondad de ajuste.

    Centraliza la lógica matemática sin dependencias de interfaces gráficas o servicios web,
    garantizando resultados reproducibles, tipos nativos de Python y tratamiento explícito
    de casos frontera.
    """

    # -------------------------------------------------------------------------
    # A. Validación y preparación de datos
    # -------------------------------------------------------------------------

    def _validar_datos(self, datos: Any, min_tamano: int = 1) -> np.ndarray:
        """
        Valida y convierte la muestra de entrada en un arreglo NumPy unidimensional de tipo flotante.

        Reglas de validación:
        - Acepta listas, tuplas o arreglos numéricos.
        - Rechaza entradas no numéricas.
        - Convierte a np.ndarray con dtype np.float64.
        - Comprueba que la muestra no esté vacía.
        - Comprueba que la muestra sea estrictamente unidimensional.
        - Rechaza valores NaN, infinitos (+inf, -inf).
        - Verifica que cumpla con el tamaño mínimo requerido (`min_tamano`).

        Args:
            datos: Muestra a evaluar (secuencia numérica).
            min_tamano: Número mínimo de observaciones requeridas.

        Returns:
            np.ndarray: Arreglo validado de tipo float64 y una dimensión.

        Raises:
            DatosInvalidosError: Si la muestra incumple alguna regla de validación.
        """
        if datos is None:
            raise DatosInvalidosError("Los datos no pueden ser None.")

        # Conversión a arreglo NumPy
        try:
            arr = np.asarray(datos, dtype=np.float64)
        except (ValueError, TypeError) as exc:
            raise DatosInvalidosError(
                f"La entrada contiene elementos no numéricos o incompatibles: {exc}"
            ) from exc

        # Validación de dimensionalidad
        if arr.ndim != 1:
            raise DatosInvalidosError(
                f"Los datos deben ser una muestra unidimensional. Se recibió dimensión {arr.ndim}."
            )

        # Comprobar que no esté vacía
        if arr.size == 0:
            raise DatosInvalidosError("La muestra no puede estar vacía.")

        # Comprobar tamaño mínimo
        if arr.size < min_tamano:
            raise DatosInvalidosError(
                f"Tamaño de muestra insuficiente: se requieren al menos {min_tamano} observaciones, "
                f"pero se recibieron {arr.size}."
            )

        # Comprobar valores finitos (sin NaN ni infinitos)
        if not np.all(np.isfinite(arr)):
            raise DatosInvalidosError(
                "La muestra contiene valores no numéricos, NaN o infinitos (+inf/-inf)."
            )

        return arr

    def _validar_alpha(self, alpha: float) -> float:
        """
        Valida que el nivel de significancia se encuentre en el intervalo abierto (0, 1).

        Args:
            alpha: Nivel de significancia a validar.

        Returns:
            float: El valor de alpha como flotante nativo.

        Raises:
            ParametroInvalidoError: Si alpha no es un número real entre 0 y 1 exclusivo.
        """
        try:
            alpha_f = float(alpha)
        except (ValueError, TypeError) as exc:
            raise ParametroInvalidoError(
                f"El nivel de significancia alpha debe ser numérico: {exc}"
            ) from exc

        if not math.isfinite(alpha_f) or alpha_f <= 0.0 or alpha_f >= 1.0:
            raise ParametroInvalidoError(
                f"El nivel de significancia (alpha) debe encontrarse estrictamente entre 0 y 1 "
                f"(excluyendo ambos extremos). Se recibió: {alpha}."
            )

        return alpha_f

    # -------------------------------------------------------------------------
    # B. Medidas descriptivas
    # -------------------------------------------------------------------------

    def calcular_metricas_descriptivas(self, datos: Any) -> Dict[str, Optional[Union[int, float]]]:
        """
        Calcula estadísticas descriptivas muestrales sobre una colección de datos numéricos.

        Devuelve:
        - `n`: número de observaciones válidas.
        - `mean`: media aritmética muestral.
        - `variance`: varianza muestral (ddof=1).
        - `std_dev`: desviación estándar muestral (ddof=1).
        - `skewness`: coeficiente de asimetría muestral (Fisher-Pearson sin sesgo, bias=False).
        - `kurtosis`: exceso de curtosis muestral (Fisher sin sesgo, fisher=True, bias=False).

        Consideraciones:
        - Si el tamaño de la muestra es insuficiente para una métrica (n < 2 para varianza/std,
          n < 3 para asimetría, n < 4 para curtosis, o varianza cero), se retorna None en vez de NaN.
        - No se redondean los resultados internamente.
        - Todos los valores devueltos son tipos nativos de Python.

        Args:
            datos: Muestra numérica a procesar.

        Returns:
            Dict[str, Optional[Union[int, float]]]: Diccionario con las métricas calculadas.
        """
        arr = self._validar_datos(datos, min_tamano=1)
        n = int(arr.size)
        mean_val = float(np.mean(arr))

        variance_val: Optional[float] = None
        std_val: Optional[float] = None
        skewness_val: Optional[float] = None
        kurtosis_val: Optional[float] = None

        if n >= 2:
            s2 = float(np.var(arr, ddof=1))
            s = float(np.std(arr, ddof=1))
            variance_val = s2
            std_val = s

            # Para asimetría y curtosis se requiere varianza no nula
            if s > 0.0:
                if n >= 3:
                    sk = float(stats.skew(arr, bias=False))
                    if math.isfinite(sk):
                        skewness_val = sk
                if n >= 4:
                    kt = float(stats.kurtosis(arr, fisher=True, bias=False))
                    if math.isfinite(kt):
                        kurtosis_val = kt

        return {
            "n": n,
            "mean": mean_val,
            "variance": variance_val,
            "std_dev": std_val,
            "skewness": skewness_val,
            "kurtosis": kurtosis_val,
        }

    # -------------------------------------------------------------------------
    # C. Kolmogorov-Smirnov (K-S)
    # -------------------------------------------------------------------------

    def prueba_kolmogorov_smirnov_normal(
        self,
        datos: Any,
        alpha: float = 0.05,
        seed: Optional[int] = None,
        n_mc_samples: int = 9999,
    ) -> Dict[str, Any]:
        """
        Ejecuta la prueba de Kolmogorov-Smirnov para contrastar normalidad con parámetros estimados.

        Para evitar la distorsión del p-valor clásico de K-S cuando la media y la desviación
        estándar son estimadas a partir de la propia muestra (prueba de Lilliefors), se utiliza
        `scipy.stats.goodness_of_fit` con reestimación de parámetros en cada réplica Monte Carlo.

        Hipótesis:
        - H0: La muestra proviene de una población con distribución normal N(mu, sigma^2).
        - H1: La muestra no proviene de una distribución normal.

        Regla de decisión:
        - Si valor-p < alpha: se rechaza H0 en favor de H1.
        - Si valor-p >= alpha: no se rechaza H0.

        Args:
            datos: Muestra numérica.
            alpha: Nivel de significancia (por defecto 0.05).
            seed: Semilla para el generador pseudoaleatorio de Monte Carlo (reproducibilidad).
            n_mc_samples: Número de réplicas Monte Carlo (por defecto 9999).

        Returns:
            Dict[str, Any]: Resultados estructurados de la prueba K-S.

        Raises:
            DatosInvalidosError: Si los datos no son válidos o la desviación estándar es cero.
            ParametroInvalidoError: Si alpha o n_mc_samples son inválidos.
        """
        arr = self._validar_datos(datos, min_tamano=3)
        alpha_val = self._validar_alpha(alpha)

        if n_mc_samples < 100:
            raise ParametroInvalidoError(
                f"El número de simulaciones Monte Carlo debe ser al menos 100. Se recibió {n_mc_samples}."
            )

        std_muestral = float(np.std(arr, ddof=1))
        if math.isclose(std_muestral, 0.0, abs_tol=1e-12):
            raise DatosInvalidosError(
                "La muestra presenta dispersión nula (desviación estándar igual a cero). "
                "No es posible ajustar una distribución normal continua."
            )

        # Ejecución con scipy.stats.goodness_of_fit para calibración adecuada
        res = stats.goodness_of_fit(
            dist=stats.norm,
            data=arr,
            statistic="ks",
            n_mc_samples=int(n_mc_samples),
            random_state=seed,
        )

        statistic = float(res.statistic)
        p_value = float(res.pvalue)
        rejected = bool(p_value < alpha_val)

        decision_str = "Se rechaza H0" if rejected else "No se rechaza H0"
        academic_verdict = (
            f"Prueba de Kolmogorov-Smirnov (calibración Monte Carlo con parámetros estimados / Lilliefors):\n"
            f"- Estadístico D = {statistic:.5f}\n"
            f"- Valor-p calibrado = {p_value:.5f} (obtenido mediante {n_mc_samples} réplicas)\n"
            f"- Nivel de significancia alpha = {alpha_val:.4f}\n"
            f"- Decisión: {decision_str}.\n"
            + (
                f"Existe evidencia estadística suficiente al nivel de significancia {alpha_val:.2%} "
                f"para concluir que los datos no provienen de una distribución normal."
                if rejected
                else (
                    f"No existe evidencia estadística suficiente al nivel de significancia {alpha_val:.2%} "
                    f"para descartar la hipótesis de normalidad. "
                    f"Nota pedagógica: La ausencia de rechazo indica compatibilidad empírica, pero NO "
                    f"constituye una demostración matemática de que la distribución subyacente sea exactamente normal."
                )
            )
        )

        return {
            "statistic": statistic,
            "p_value": p_value,
            "alpha": alpha_val,
            "rejected": rejected,
            "academic_verdict": academic_verdict,
            "calibration_method": (
                f"Monte Carlo paramétrico (Lilliefors) con reestimación de parámetros "
                f"({n_mc_samples} simulaciones)"
            ),
            "n_mc_samples": int(n_mc_samples),
            "seed": seed,
        }

    # -------------------------------------------------------------------------
    # D. Anderson-Darling
    # -------------------------------------------------------------------------

    def prueba_anderson_darling_normal(
        self,
        datos: Any,
        alpha: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Ejecuta la prueba de Anderson-Darling para contrastar normalidad.

        La prueba de Anderson-Darling evalúa la discrepancia entre la distribución empírica
        y la normal teórica estimada, ponderando con mayor peso las diferencias observadas
        en las colas de la distribución.

        Criterio de decisión:
        - Si A^2 > valor_crítico(alpha): se rechaza H0.
        - En caso contrario: no se rechaza H0.

        El método identifica el valor crítico correspondiente según la tabla provista por SciPy
        para la distribución normal, admitiendo inicialmente niveles de significancia 0.01, 0.05 y 0.10.
        El p-valor se reporta como None, respetando el contrato original basado en valores críticos.

        Args:
            datos: Muestra numérica.
            alpha: Nivel de significancia (0.01, 0.05, 0.10, etc.).

        Returns:
            Dict[str, Any]: Resultados estructurados de la prueba Anderson-Darling.

        Raises:
            DatosInvalidosError: Si los datos no son válidos o tienen dispersión nula.
            ParametroInvalidoError: Si alpha no tiene un valor crítico tabulado en SciPy.
        """
        arr = self._validar_datos(datos, min_tamano=5)
        alpha_val = self._validar_alpha(alpha)

        std_muestral = float(np.std(arr, ddof=1))
        if math.isclose(std_muestral, 0.0, abs_tol=1e-12):
            raise DatosInvalidosError(
                "La muestra presenta dispersión nula (desviación estándar igual a cero). "
                "No es posible calcular el estadístico de Anderson-Darling."
            )

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            res = stats.anderson(arr, dist="norm")

        statistic = float(res.statistic)
        sig_levels = [float(s) for s in res.significance_level]
        crit_values = [float(c) for c in res.critical_values]

        # SciPy expresa significance_level en porcentaje (e.g. 15.0, 10.0, 5.0, 2.5, 1.0)
        alpha_pct = alpha_val * 100.0

        match_idx: Optional[int] = None
        for i, sl in enumerate(sig_levels):
            if math.isclose(sl, alpha_pct, rel_tol=1e-3, abs_tol=1e-3):
                match_idx = i
                break

        if match_idx is None:
            niveles_disponibles = [sl / 100.0 for sl in sig_levels]
            raise ParametroInvalidoError(
                f"El nivel de significancia alpha={alpha_val} no está disponible en los valores "
                f"críticos tabulados por SciPy para Anderson-Darling (normal). "
                f"Niveles admitidos: {niveles_disponibles}."
            )

        critical_value = crit_values[match_idx]
        significance_level_ret = sig_levels[match_idx] / 100.0
        rejected = bool(statistic > critical_value)

        decision_str = "Se rechaza H0" if rejected else "No se rechaza H0"
        academic_verdict = (
            f"Prueba de Anderson-Darling (distribución normal):\n"
            f"- Estadístico A^2 = {statistic:.5f}\n"
            f"- Valor crítico = {critical_value:.5f} para alpha = {alpha_val:.4f} "
            f"({significance_level_ret:.1%})\n"
            f"- Criterio: A^2 {'>' if rejected else '<='} Valor Crítico -> {decision_str}.\n"
            f"- Sensibilidad metodológica: Anderson-Darling otorga una ponderación sustancialmente "
            f"mayor a las discrepancias en las colas de la distribución en comparación con Kolmogorov-Smirnov.\n"
            + (
                f"Existe evidencia estadística para rechazar la hipótesis de normalidad al nivel de "
                f"significancia {alpha_val:.2%} debido a discrepancias acumuladas significativas, "
                f"particularmente en los extremos de la muestra."
                if rejected
                else (
                    f"No existe evidencia estadística para rechazar la hipótesis de normalidad al nivel "
                    f"de significancia {alpha_val:.2%}. Las observaciones no se apartan significativamente "
                    f"del comportamiento esperado en el centro ni en las colas de una distribución normal."
                )
            )
        )

        return {
            "statistic": statistic,
            "critical_value": critical_value,
            "significance_level": significance_level_ret,
            "alpha": alpha_val,
            "p_value": None,
            "rejected": rejected,
            "academic_verdict": academic_verdict,
        }

    # -------------------------------------------------------------------------
    # E. Chi-cuadrada de Pearson
    # -------------------------------------------------------------------------

    def _determinar_k_inicial(self, n: int) -> int:
        """
        Determina el número inicial de clases k como el menor entero positivo tal que 2^k > n.

        Args:
            n: Tamaño de la muestra.

        Returns:
            int: Número inicial de clases k >= 1.
        """
        k = 1
        while (2 ** k) <= n:
            k += 1
        return k

    def _fusionar_clases(self, clases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Algoritmo obligatorio de fusión determinística de clases contiguas.

        Regla de fusión:
        - Mientras exista alguna clase con frecuencia esperada Ei < 5:
          1. Se identifica la clase deficiente con la menor Ei (en caso de empate, la de menor índice).
          2. Se selecciona el vecino adyacente (izquierdo o derecho) con la menor frecuencia esperada.
             En caso de empate en la frecuencia esperada de ambos vecinos, se prioriza el vecino izquierdo.
          3. Si la clase deficiente es la primera (extremo izquierdo), su único vecino es la clase siguiente.
             Si es la última (extremo derecho), su único vecino es la clase previa.
          4. Se fusionan sumando sus frecuencias observadas (Oi) y esperadas (Ei), y unificando los límites
             inferior y superior del nuevo intervalo continuo.
          5. Se repite el proceso hasta que todas las clases cumplan Ei >= 5 o queden menos de 2 clases.

        No se eliminan clases vacías ni se descartan observaciones.

        Args:
            clases: Lista de diccionarios de clases con claves:
                    'lower', 'upper', 'observed', 'expected'.

        Returns:
            List[Dict[str, Any]]: Lista de clases resultantes tras las fusiones necesarias.
        """
        clases_actuales = [dict(c) for c in clases]

        while True:
            # Identificar índices de clases deficientes (Ei < 5.0)
            deficientes = [i for i, c in enumerate(clases_actuales) if c["expected"] < 5.0]
            if not deficientes:
                break  # Condición cumplida en todas las clases

            if len(clases_actuales) < 2:
                # No es posible fusionar más
                break

            # Seleccionar la clase con menor Ei (rompiendo empates por menor índice)
            min_idx = min(deficientes, key=lambda i: (clases_actuales[i]["expected"], i))

            # Determinar vecino a fusionar
            if min_idx == 0:
                vecino_idx = 1
            elif min_idx == len(clases_actuales) - 1:
                vecino_idx = len(clases_actuales) - 2
            else:
                ei_izq = clases_actuales[min_idx - 1]["expected"]
                ei_der = clases_actuales[min_idx + 1]["expected"]
                if ei_izq < ei_der:
                    vecino_idx = min_idx - 1
                elif ei_der < ei_izq:
                    vecino_idx = min_idx + 1
                else:
                    # Empate determinístico: priorizar vecino izquierdo
                    vecino_idx = min_idx - 1

            idx_a = min(min_idx, vecino_idx)
            idx_b = max(min_idx, vecino_idx)

            clase_fusionada = {
                "lower": clases_actuales[idx_a]["lower"],
                "upper": clases_actuales[idx_b]["upper"],
                "observed": int(clases_actuales[idx_a]["observed"] + clases_actuales[idx_b]["observed"]),
                "expected": float(clases_actuales[idx_a]["expected"] + clases_actuales[idx_b]["expected"]),
            }

            clases_actuales = (
                clases_actuales[:idx_a]
                + [clase_fusionada]
                + clases_actuales[idx_b + 1:]
            )

        return clases_actuales

    def prueba_chi_cuadrada_normal(
        self,
        datos: Any,
        alpha: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Ejecuta la prueba de bondad de ajuste Chi-cuadrada de Pearson para normalidad.

        Metodología de la asignatura:
        1. k inicial: menor entero positivo k con 2^k > n.
        2. Soporte continuo completo (-inf, +inf) con clases intermedias uniformes sobre el rango.
        3. Frecuencias observadas Oi completas sin pérdida de datos.
        4. Frecuencias esperadas Ei mediante la función normal acumulada (CDF) con parámetros muestrales
           (media y desviación estándar con ddof=1).
        5. Algoritmo de fusión determinístico para clases con Ei < 5.
        6. Grados de libertad v = k_ajustado - p - 1 = k_ajustado - 3 (con p = 2 parámetros estimados).
        7. Estadístico EP = sum((Oi - Ei)^2 / Ei).
        8. Valor crítico = chi2.ppf(1 - alpha, v), p-valor = chi2.sf(EP, v).
        9. Si la prueba no es aplicable (v <= 0, Ei < 5 remanentes, dispersión cero), devuelve
           `available: False` con diagnóstico explicativo sin omitir la prueba silenciosamente.

        Args:
            datos: Muestra numérica.
            alpha: Nivel de significancia (por defecto 0.05).

        Returns:
            Dict[str, Any]: Resultados completos o diagnóstico de no aplicabilidad.
        """
        arr = self._validar_datos(datos, min_tamano=1)
        alpha_val = self._validar_alpha(alpha)
        n = int(arr.size)

        # Validación de variabilidad muestral
        s = float(np.std(arr, ddof=1)) if n >= 2 else 0.0
        if n < 2 or math.isclose(s, 0.0, abs_tol=1e-12):
            return {
                "available": False,
                "statistic": None,
                "degrees_of_freedom": None,
                "critical_value": None,
                "p_value": None,
                "alpha": alpha_val,
                "initial_classes_count": 0,
                "merged_classes_count": 0,
                "merged_classes": [],
                "rejected": None,
                "reason": (
                    "La muestra presenta desviación estándar igual a cero o tamaño insuficiente (n < 2). "
                    "No es posible construir intervalos con soporte continuo ni estimar la distribución normal."
                ),
                "academic_verdict": (
                    "Prueba Chi-cuadrada no aplicable: dispersión muestral nula o tamaño insuficiente."
                ),
            }

        mu = float(np.mean(arr))
        x_min = float(np.min(arr))
        x_max = float(np.max(arr))

        # 1. Determinación de k inicial (2^k > n)
        k_inicial = self._determinar_k_inicial(n)

        # 2. Construcción de intervalos iniciales
        # Amplitud uniforme en el rango muestral
        amplitud = (x_max - x_min) / float(k_inicial)
        puntos_corte = [x_min + j * amplitud for j in range(1, k_inicial)]

        clases_iniciales: List[Dict[str, Any]] = []

        # Clase 0: (-inf, puntos_corte[0]]
        lim_inf_0 = -float("inf")
        lim_sup_0 = puntos_corte[0] if puntos_corte else float("inf")
        o_0 = int(np.sum(arr <= lim_sup_0))
        clases_iniciales.append({
            "lower": lim_inf_0,
            "upper": lim_sup_0,
            "observed": o_0,
        })

        # Clases intermedias: (puntos_corte[j], puntos_corte[j+1]]
        for j in range(len(puntos_corte) - 1):
            c_inf = puntos_corte[j]
            c_sup = puntos_corte[j + 1]
            o_j = int(np.sum((arr > c_inf) & (arr <= c_sup)))
            clases_iniciales.append({
                "lower": c_inf,
                "upper": c_sup,
                "observed": o_j,
            })

        # Última clase: (puntos_corte[-1], +inf)
        if puntos_corte:
            lim_inf_last = puntos_corte[-1]
            lim_sup_last = float("inf")
            o_last = int(np.sum(arr > lim_inf_last))
            clases_iniciales.append({
                "lower": lim_inf_last,
                "upper": lim_sup_last,
                "observed": o_last,
            })

        # 4. Frecuencias esperadas Ei = n * [CDF(Lsup) - CDF(Linf)]
        dist_normal = stats.norm(loc=mu, scale=s)
        for c in clases_iniciales:
            p_inf = 0.0 if math.isinf(c["lower"]) and c["lower"] < 0 else float(dist_normal.cdf(c["lower"]))
            p_sup = 1.0 if math.isinf(c["upper"]) and c["upper"] > 0 else float(dist_normal.cdf(c["upper"]))
            prob_intervalo = max(0.0, p_sup - p_inf)
            c["expected"] = float(n * prob_intervalo)

        # 5. Algoritmo obligatorio de fusión de clases (Ei >= 5)
        clases_fusionadas = self._fusionar_clases(clases_iniciales)
        k_ajustado = len(clases_fusionadas)

        # Formatear información de clases fusionadas para diagnóstico y salida
        clases_formateadas: List[Dict[str, Any]] = []
        for idx, c in enumerate(clases_fusionadas, start=1):
            clases_formateadas.append({
                "class_index": idx,
                "lower_limit": None if math.isinf(c["lower"]) else float(c["lower"]),
                "upper_limit": None if math.isinf(c["upper"]) else float(c["upper"]),
                "observed_frequency": int(c["observed"]),
                "expected_frequency": float(c["expected"]),
            })

        # Verificación del cumplimiento estricto de Ei >= 5
        algun_ei_invalido = any(c["expected"] < 5.0 for c in clases_fusionadas)
        if algun_ei_invalido:
            return {
                "available": False,
                "statistic": None,
                "degrees_of_freedom": None,
                "critical_value": None,
                "p_value": None,
                "alpha": alpha_val,
                "initial_classes_count": k_inicial,
                "merged_classes_count": k_ajustado,
                "merged_classes": clases_formateadas,
                "rejected": None,
                "reason": (
                    f"No fue posible lograr frecuencias esperadas Ei >= 5 en todas las clases tras fusionar "
                    f"(el tamaño de muestra n={n} es insuficiente para la dispersión observada)."
                ),
                "academic_verdict": (
                    f"Prueba Chi-cuadrada no aplicable: condición de frecuencias esperadas mínimas "
                    f"(Ei >= 5) no satisfecha tras agotar las fusiones posibles."
                ),
            }

        # 6. Grados de libertad: v = k_ajustado - p - 1 = k_ajustado - 3
        p_params = 2
        v = k_ajustado - p_params - 1

        if v <= 0:
            return {
                "available": False,
                "statistic": None,
                "degrees_of_freedom": v,
                "critical_value": None,
                "p_value": None,
                "alpha": alpha_val,
                "initial_classes_count": k_inicial,
                "merged_classes_count": k_ajustado,
                "merged_classes": clases_formateadas,
                "rejected": None,
                "reason": (
                    f"El número final de clases fusionadas ({k_ajustado}) genera grados de libertad "
                    f"insuficientes (v = k - p - 1 = {k_ajustado} - 2 - 1 = {v} <= 0). "
                    f"Se requieren al menos 4 clases válidas tras la fusión para estimar media y varianza."
                ),
                "academic_verdict": (
                    f"Prueba Chi-cuadrada no aplicable: grados de libertad v = {v} <= 0 tras la fusión "
                    f"de intervalos para satisfacer Ei >= 5."
                ),
            }

        # 7. Estadístico Chi-cuadrada EP = sum((Oi - Ei)^2 / Ei)
        ep = float(sum((c["observed"] - c["expected"]) ** 2 / c["expected"] for c in clases_fusionadas))

        # 8. Valor crítico y valor-p
        critical_value = float(stats.chi2.ppf(1.0 - alpha_val, v))
        p_value = float(stats.chi2.sf(ep, v))
        rejected = bool(ep > critical_value)

        decision_str = "Se rechaza H0" if rejected else "No se rechaza H0"
        academic_verdict = (
            f"Prueba de bondad de ajuste Chi-cuadrada de Pearson (distribución normal):\n"
            f"- Número inicial de clases (2^k > {n}): k = {k_inicial}\n"
            f"- Clases finales tras fusión (todas con Ei >= 5): k_ajustado = {k_ajustado}\n"
            f"- Parámetros estimados: p = 2 (media = {mu:.4f}, desviación estándar = {s:.4f})\n"
            f"- Grados de libertad: v = {k_ajustado} - 2 - 1 = {v}\n"
            f"- Estadístico de prueba EP = {ep:.5f}\n"
            f"- Valor crítico chi2({1.0 - alpha_val:.2f}, {v}) = {critical_value:.5f}\n"
            f"- Valor-p = {p_value:.5f}\n"
            f"- Decisión (EP {'>' if rejected else '<='} valor crítico | p-valor {'<' if rejected else '>='} {alpha_val}): {decision_str}.\n"
            + (
                f"Existe evidencia estadística suficiente al nivel de significancia {alpha_val:.2%} "
                f"para concluir que los datos observados difieren significativamente de las frecuencias "
                f"esperadas bajo el modelo normal."
                if rejected
                else (
                    f"No existe evidencia estadística suficiente al nivel de significancia {alpha_val:.2%} "
                    f"para descartar el modelo normal. Las frecuencias observadas son concordantes con "
                    f"las esperadas bajo la distribución normal ajustada. (Nota: esto no certifica normalidad absoluta)."
                )
            )
        )

        return {
            "available": True,
            "statistic": ep,
            "degrees_of_freedom": v,
            "critical_value": critical_value,
            "p_value": p_value,
            "alpha": alpha_val,
            "initial_classes_count": k_inicial,
            "merged_classes_count": k_ajustado,
            "merged_classes": clases_formateadas,
            "rejected": rejected,
            "academic_verdict": academic_verdict,
            "reason": None,
        }

    # -------------------------------------------------------------------------
    # F. Comparación de dos muestras independientes
    # -------------------------------------------------------------------------

    def comparar_muestras(
        self,
        sample_a: Any,
        sample_b: Any,
        alpha: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Realiza la comparación inferencial entre dos muestras numéricas independientes.

        Flujo metodológico:
        1. Validación de muestras (al menos 5 observaciones cada una, numéricas, unidimensionales, finitas).
        2. Prueba de Levene para evaluar igualdad de varianzas (homocedasticidad) a un nivel fijo de 0.05 (5%):
           - Si p_levene > 0.05: no se rechaza igualdad de varianzas -> equal_var = True.
           - Si p_levene <= 0.05: se rechaza igualdad de varianzas -> equal_var = False (Welch).
        3. Prueba t-Student bilateral para diferencia de medias con equal_var determinado dinámicamente.
        4. Prueba U de Mann-Whitney bilateral para contraste no paramétrico (gestión correcta de empates).
        5. Interpretación académica rigurosa (sin asumir erróneamente que Mann-Whitney evalúa únicamente
           medianas sin supuestos de forma distribucional idéntica).

        Args:
            sample_a: Muestra del Grupo A.
            sample_b: Muestra del Grupo B.
            alpha: Nivel de significancia para t-Student y Mann-Whitney (por defecto 0.05).

        Returns:
            Dict[str, Any]: Resultados completos de la comparación.

        Raises:
            DatosInvalidosError: Si alguna muestra no cumple los requisitos mínimos.
            ParametroInvalidoError: Si alpha no es válido.
        """
        arr_a = self._validar_datos(sample_a, min_tamano=5)
        arr_b = self._validar_datos(sample_b, min_tamano=5)
        alpha_val = self._validar_alpha(alpha)

        n_a = int(arr_a.size)
        n_b = int(arr_b.size)

        var_a = float(np.var(arr_a, ddof=1))
        var_b = float(np.var(arr_b, ddof=1))

        # Caso frontera: ambas muestras constantes (varianzas cero)
        if math.isclose(var_a, 0.0, abs_tol=1e-12) and math.isclose(var_b, 0.0, abs_tol=1e-12):
            mean_a = float(np.mean(arr_a))
            mean_b = float(np.mean(arr_b))
            iguales = math.isclose(mean_a, mean_b, abs_tol=1e-12)

            levene_res = {
                "statistic": 0.0,
                "p_value": 1.0,
                "significance_level": 0.05,
                "homocedasticity": True,
                "equal_var": True,
                "rejected": False,
                "note": "Ambas muestras tienen varianza cero; las varianzas se consideran idénticas.",
            }
            t_res = {
                "statistic": 0.0 if iguales else (float("inf") if mean_a > mean_b else -float("inf")),
                "p_value": 1.0 if iguales else 0.0,
                "method": "Student estándar (varianzas idénticas = 0)",
                "equal_var": True,
                "rejected": not iguales,
                "verdict": (
                    "Muestras constantes con medias idénticas; no existe diferencia."
                    if iguales
                    else "Muestras constantes con valores distintos; diferencia determinística absoluta."
                ),
            }
            # Mann-Whitney
            mwu = stats.mannwhitneyu(arr_a, arr_b, alternative="two-sided")
            mwu_stat = float(mwu.statistic)
            mwu_p = float(mwu.pvalue)
            mwu_rej = bool(mwu_p < alpha_val)
            mwu_res = {
                "statistic": mwu_stat,
                "p_value": mwu_p,
                "rejected": mwu_rej,
                "verdict": "Se rechaza H0 en Mann-Whitney" if mwu_rej else "No se rechaza H0 en Mann-Whitney",
            }
            return {
                "n_a": n_a,
                "n_b": n_b,
                "alpha": alpha_val,
                "levene": levene_res,
                "t_test": t_res,
                "mann_whitney_u": mwu_res,
                "academic_interpretation": (
                    "Comparación sobre muestras sin dispersión (ambas constantes). "
                    "Las decisiones reflejan la igualdad o divergencia puntual exacta entre grupos."
                ),
            }

        # 1. Prueba de Levene (nivel fijo 0.05)
        levene_out = stats.levene(arr_a, arr_b)
        levene_stat = float(levene_out.statistic)
        levene_p = float(levene_out.pvalue)

        # Si p > 0.05, no se rechaza igualdad de varianzas -> equal_var = True
        # Si p <= 0.05, se rechaza igualdad de varianzas -> equal_var = False
        levene_rejected = bool(levene_p <= 0.05)
        equal_var = not levene_rejected
        homocedasticidad = equal_var

        # 2. Prueba t-Student bilateral
        t_out = stats.ttest_ind(arr_a, arr_b, equal_var=equal_var, alternative="two-sided")
        t_stat = float(t_out.statistic)
        t_p = float(t_out.pvalue)
        t_rejected = bool(t_p < alpha_val)
        metodo_t = (
            "t-Student para varianzas iguales (homocedasticidad)"
            if equal_var
            else "t-Student de Welch para varianzas desiguales (heterocedasticidad)"
        )

        # 3. Prueba Mann-Whitney U bilateral
        mwu_out = stats.mannwhitneyu(arr_a, arr_b, alternative="two-sided")
        mwu_stat = float(mwu_out.statistic)
        mwu_p = float(mwu_out.pvalue)
        mwu_rejected = bool(mwu_p < alpha_val)

        # 4. Interpretación pedagógica
        t_decision_str = "Se rechaza H0 (medias diferentes)" if t_rejected else "No se rechaza H0 (medias similares)"
        mwu_decision_str = (
            "Se rechaza H0 (distribuciones diferentes)"
            if mwu_rejected
            else "No se rechaza H0 (distribuciones comparables)"
        )

        interpretacion = (
            f"Comparación de dos muestras independientes (n_A = {n_a}, n_B = {n_b}, alpha = {alpha_val:.2%}):\n"
            f"1. Homocedasticidad (Levene, alpha fijo = 5.0%):\n"
            f"   - Estadístico W = {levene_stat:.4f}, valor-p = {levene_p:.4f}\n"
            f"   - Decisión: {'Se rechaza la igualdad de varianzas (p <= 0.05); se asume heterocedasticidad.' if levene_rejected else 'No se rechaza la igualdad de varianzas (p > 0.05); se asume homocedasticidad.'}\n"
            f"2. Prueba t de Student ({metodo_t}):\n"
            f"   - Estadístico t = {t_stat:.4f}, valor-p = {t_p:.4f}\n"
            f"   - Decisión al nivel {alpha_val:.2%}: {t_decision_str}.\n"
            f"3. Prueba no paramétrica U de Mann-Whitney (bilateral):\n"
            f"   - Estadístico U = {mwu_stat:.1f}, valor-p = {mwu_p:.4f}\n"
            f"   - Decisión al nivel {alpha_val:.2%}: {mwu_decision_str}.\n"
            f"Nota metodológica: Mann-Whitney evalúa dominancia estocástica general (igualdad de funciones "
            f"de distribución continua). Solo debe interpretarse estrictamente como comparación de medianas "
            f"cuando ambas poblaciones comparten la misma forma y dispersión bajo la hipótesis nula."
        )

        return {
            "n_a": n_a,
            "n_b": n_b,
            "alpha": alpha_val,
            "levene": {
                "statistic": levene_stat,
                "p_value": levene_p,
                "significance_level": 0.05,
                "homocedasticity": homocedasticidad,
                "equal_var": equal_var,
                "rejected": levene_rejected,
            },
            "t_test": {
                "statistic": t_stat,
                "p_value": t_p,
                "method": metodo_t,
                "equal_var": equal_var,
                "rejected": t_rejected,
                "verdict": t_decision_str,
            },
            "mann_whitney_u": {
                "statistic": mwu_stat,
                "p_value": mwu_p,
                "rejected": mwu_rejected,
                "verdict": mwu_decision_str,
            },
            "academic_interpretation": interpretacion,
        }

    # -------------------------------------------------------------------------
    # G. Síntesis pedagógica
    # -------------------------------------------------------------------------

    def generar_sintesis_pedagogica(
        self,
        resultados_ks: Dict[str, Any],
        resultados_ad: Dict[str, Any],
        resultados_chi2: Dict[str, Any],
    ) -> str:
        """
        Genera una síntesis académica e interpretativa integral a partir de los resultados
        de las pruebas de bondad de ajuste de Kolmogorov-Smirnov, Anderson-Darling y Chi-cuadrada.

        Contempla:
        1. Definición formal de la hipótesis nula (H0) y alternativa (H1).
        2. Criterio del valor-p frente al nivel de significancia alpha.
        3. Claridad epistemológica: no rechazar H0 no equivale a demostrar que H0 es verdadera.
        4. Comparación de sensibilidades: sensibilidad central de K-S vs. ponderación de colas en A-D.
        5. Estado y diagnóstico de la prueba Chi-cuadrada y cumplimiento de la condición Ei >= 5.

        Args:
            resultados_ks: Diccionario devuelto por prueba_kolmogorov_smirnov_normal.
            resultados_ad: Diccionario devuelto por prueba_anderson_darling_normal.
            resultados_chi2: Diccionario devuelto por prueba_chi_cuadrada_normal.

        Returns:
            str: Texto estructurado con la síntesis pedagógica detallada.
        """
        lineas: List[str] = []

        lineas.append("=== SÍNTESIS PEDAGÓGICA Y ANÁLISIS DE BONDAD DE AJUSTE A LA DISTRIBUCIÓN NORMAL ===")
        lineas.append("")
        lineas.append("1. Marco de Hipótesis:")
        lineas.append("   - H0 (Hipótesis Nula): La muestra proviene de una población con distribución normal.")
        lineas.append("   - H1 (Hipótesis Alternativa): La muestra proviene de una población con distribución no normal.")
        lineas.append("")
        lineas.append("2. Criterio de Decisión y Significado del Valor-p:")
        lineas.append("   - Si valor-p < alpha: Los datos observados son altamente improbables bajo H0; por tanto, se rechaza H0.")
        lineas.append("   - Si valor-p >= alpha: No existe evidencia suficiente para descartar H0.")
        lineas.append("   - IMPORTANTE (Principio Epistemológico): No rechazar H0 NUNCA demuestra que los datos sean")
        lineas.append("     estrictamente normales. Significa únicamente que no se detectaron desviaciones estadísticamente")
        lineas.append("     significativas con la muestra y el nivel de significancia analizados.")
        lineas.append("")

        lineas.append("3. Comparación Metodológica de Sensibilidad:")
        lineas.append("   - Kolmogorov-Smirnov (K-S con Lilliefors): Cuantifica la máxima discrepancia vertical D entre")
        lineas.append("     la distribución empírica y la teórica acumulada. Presenta mayor sensibilidad alrededor del centro")
        lineas.append("     (mediana) de la distribución.")
        lineas.append("   - Anderson-Darling (A-D): Pondera de forma cuadrática las discrepancias dividiendo por la varianza")
        lineas.append("     teórica en cada punto, otorgando un peso sustancialmente superior a las colas (extremos de la distribución).")
        lineas.append("   - Chi-cuadrada de Pearson: Evalúa el ajuste discretizado en clases disjuntas que cubren todo el soporte (-inf, +inf).")
        lineas.append("")

        # Diagnóstico K-S
        ks_stat = resultados_ks.get("statistic")
        ks_p = resultados_ks.get("p_value")
        ks_rej = resultados_ks.get("rejected")
        lineas.append("4. Resultados Empíricos Observados:")
        if ks_stat is not None and ks_p is not None:
            lineas.append(
                f"   [K-S] Estadístico D = {ks_stat:.5f}, p-valor calibrado = {ks_p:.5f}. "
                f"Decisión: {'Rechaza normalidad' if ks_rej else 'No rechaza normalidad'}."
            )
        else:
            lineas.append("   [K-S] No disponible o datos no calculados.")

        # Diagnóstico A-D
        ad_stat = resultados_ad.get("statistic")
        ad_crit = resultados_ad.get("critical_value")
        ad_rej = resultados_ad.get("rejected")
        if ad_stat is not None and ad_crit is not None:
            lineas.append(
                f"   [A-D] Estadístico A^2 = {ad_stat:.5f}, valor crítico = {ad_crit:.5f}. "
                f"Decisión: {'Rechaza normalidad' if ad_rej else 'No rechaza normalidad'}."
            )
        else:
            lineas.append("   [A-D] No disponible o datos no calculados.")

        # Diagnóstico Chi-cuadrada
        chi2_disp = resultados_chi2.get("available", False)
        if chi2_disp:
            chi2_stat = resultados_chi2.get("statistic")
            chi2_p = resultados_chi2.get("p_value")
            chi2_v = resultados_chi2.get("degrees_of_freedom")
            chi2_k_ini = resultados_chi2.get("initial_classes_count")
            chi2_k_fin = resultados_chi2.get("merged_classes_count")
            chi2_rej = resultados_chi2.get("rejected")
            lineas.append(
                f"   [Chi2] Estadístico EP = {chi2_stat:.5f}, p-valor = {chi2_p:.5f}, grados de libertad v = {chi2_v}. "
                f"Clases iniciales = {chi2_k_ini}, clases tras fusión = {chi2_k_fin} (todas con Ei >= 5). "
                f"Decisión: {'Rechaza normalidad' if chi2_rej else 'No rechaza normalidad'}."
            )
        else:
            motivo = resultados_chi2.get("reason", "Condiciones estadísticas no cumplidas.")
            lineas.append(
                f"   [Chi2] PRUEBA NO APLICABLE: {motivo}"
            )

        lineas.append("")
        lineas.append("5. Dictamen Académico Global:")
        rechazos = sum(
            1 for r in [ks_rej, ad_rej, (chi2_rej if chi2_disp else None)] if r is True
        )
        total_evaluadas = 2 + (1 if chi2_disp else 0)

        if rechazos == total_evaluadas:
            lineas.append(
                "   Conclusión: Todas las pruebas ejecutadas rechazan concordantemente la hipótesis nula de normalidad. "
                "Existe fuerte evidencia en el centro y en las colas de que la muestra proviene de un modelo no normal. "
                "Se aconseja emplear métodos no paramétricos o transformaciones de variable (e.g. Box-Cox)."
            )
        elif rechazos == 0:
            lineas.append(
                "   Conclusión: Ninguna de las pruebas de bondad de ajuste rechaza la hipótesis nula de normalidad. "
                "La muestra es plenamente compatible con el modelo normal tanto en la región central como en sus colas. "
                "Es razonable continuar con procedimientos inferenciales clásicos basados en normalidad."
            )
        else:
            lineas.append(
                f"   Conclusión: Se observan discrepancias entre las pruebas ({rechazos} de {total_evaluadas} rechazan normalidad). "
                "Esto es habitual cuando la desviación de normalidad se concentra específicamente en colas pesadas/ligeras "
                "(detectadas por Anderson-Darling pero no por K-S) o por efectos del agrupamiento en Chi-cuadrada. "
                "Se recomienda inspeccionar visualmente los datos y considerar el contexto del fenómeno de ingeniería."
            )

        return "\n".join(lineas)

    # -------------------------------------------------------------------------
    # H. Flujo unificado de bondad de ajuste
    # -------------------------------------------------------------------------

    def analizar_bondad_ajuste_completa(
        self,
        datos: Any,
        alpha: float = 0.05,
        seed: Optional[int] = None,
        n_mc_samples: int = 9999,
    ) -> Dict[str, Any]:
        """
        Ejecuta el conjunto completo de análisis descriptivo, pruebas de bondad de ajuste
        y síntesis pedagógica sobre una muestra numérica.

        Args:
            datos: Muestra numérica a evaluar.
            alpha: Nivel de significancia (0.01, 0.05, 0.10).
            seed: Semilla para reproducibilidad de Monte Carlo en K-S.
            n_mc_samples: Número de réplicas Monte Carlo para K-S.

        Returns:
            Dict[str, Any]: Estructura consolidada lista para serialización JSON.
        """
        metricas = self.calcular_metricas_descriptivas(datos)
        ks = self.prueba_kolmogorov_smirnov_normal(
            datos=datos,
            alpha=alpha,
            seed=seed,
            n_mc_samples=n_mc_samples,
        )
        ad = self.prueba_anderson_darling_normal(
            datos=datos,
            alpha=alpha,
        )
        chi2 = self.prueba_chi_cuadrada_normal(
            datos=datos,
            alpha=alpha,
        )
        sintesis = self.generar_sintesis_pedagogica(
            resultados_ks=ks,
            resultados_ad=ad,
            resultados_chi2=chi2,
        )

        return {
            "descriptive_metrics": metricas,
            "kolmogorov_smirnov": ks,
            "anderson_darling": ad,
            "chi_square": chi2,
            "pedagogical_synthesis": sintesis,
        }

