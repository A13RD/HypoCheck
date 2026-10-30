"""
Esquemas Pydantic para la API REST de la Suite de Inferencia Estadística y Bondad de Ajuste.

Define los modelos de validación de entrada y estructuras de respuesta JSON
para los endpoints de bondad de ajuste y comparación de muestras independientes.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Modelos de Solicitud (Request Models)
# =============================================================================

class GoodnessOfFitRequest(BaseModel):
    """
    Modelo de solicitud para la prueba de bondad de ajuste a la distribución normal.
    """
    data: List[float] = Field(
        ...,
        min_length=10,
        description="Muestra numérica continua con un mínimo de 10 observaciones.",
        examples=[[160.2, 172.5, 180.1, 165.8, 190.3, 175.0, 168.9, 183.2, 170.4, 177.1]],
    )
    alpha: float = Field(
        default=0.05,
        gt=0.0,
        lt=1.0,
        description="Nivel de significancia estadística (0 < alpha < 1).",
        examples=[0.05],
    )

    @field_validator("data")
    @classmethod
    def validar_datos_finitos_y_tamano(cls, valores: List[float]) -> List[float]:
        """Valida que todos los elementos de la muestra sean números reales finitos."""
        if not valores:
            raise ValueError("La muestra no puede estar vacía.")
        if len(valores) < 10:
            raise ValueError("La muestra debe contener al menos 10 observaciones.")
        for idx, val in enumerate(valores):
            if val is None or not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
                raise ValueError(
                    f"El elemento en el índice {idx} contiene un valor no numérico, NaN o infinito ({val})."
                )
        return valores

    @field_validator("alpha")
    @classmethod
    def validar_alpha_rango(cls, val: float) -> float:
        """Valida que alpha sea estrictamente un flotante finito en (0, 1)."""
        if not math.isfinite(val) or val <= 0.0 or val >= 1.0:
            raise ValueError("El nivel de significancia (alpha) debe encontrarse estrictamente entre 0 y 1.")
        return val


class CompareSamplesRequest(BaseModel):
    """
    Modelo de solicitud para la comparación inferencial entre dos muestras independientes.
    """
    sample_a: List[float] = Field(
        ...,
        min_length=5,
        description="Muestra numérica del Grupo A con un mínimo de 5 observaciones.",
        examples=[[10.5, 12.3, 11.8, 13.2, 14.1]],
    )
    sample_b: List[float] = Field(
        ...,
        min_length=5,
        description="Muestra numérica del Grupo B con un mínimo de 5 observaciones.",
        examples=[[15.2, 16.4, 14.8, 17.1, 16.8]],
    )
    alpha: float = Field(
        default=0.05,
        gt=0.0,
        lt=1.0,
        description="Nivel de significancia estadística para t-Student y Mann-Whitney (0 < alpha < 1).",
        examples=[0.05],
    )

    @field_validator("sample_a", "sample_b")
    @classmethod
    def validar_muestra_finita(cls, valores: List[float]) -> List[float]:
        """Valida que todos los elementos de cada grupo sean números reales finitos."""
        if not valores:
            raise ValueError("La muestra no puede estar vacía.")
        if len(valores) < 5:
            raise ValueError("Cada muestra debe contener al menos 5 observaciones.")
        for idx, val in enumerate(valores):
            if val is None or not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
                raise ValueError(
                    f"El elemento en el índice {idx} contiene un valor no numérico, NaN o infinito ({val})."
                )
        return valores

    @field_validator("alpha")
    @classmethod
    def validar_alpha_comparacion(cls, val: float) -> float:
        """Valida que alpha sea estrictamente un flotante finito en (0, 1)."""
        if not math.isfinite(val) or val <= 0.0 or val >= 1.0:
            raise ValueError("El nivel de significancia (alpha) debe encontrarse estrictamente entre 0 y 1.")
        return val


# =============================================================================
# Modelos de Respuesta (Response Models)
# =============================================================================

class DescriptiveMetricsResponse(BaseModel):
    """Métricas estadísticas descriptivas de una muestra."""
    n: int = Field(..., description="Número de observaciones válidas.")
    mean: float = Field(..., description="Media aritmética muestral.")
    variance: Optional[float] = Field(None, description="Varianza muestral (ddof=1).")
    std_dev: Optional[float] = Field(None, description="Desviación estándar muestral (ddof=1).")
    skewness: Optional[float] = Field(None, description="Coeficiente de asimetría muestral (Fisher-Pearson sin sesgo).")
    kurtosis: Optional[float] = Field(None, description="Exceso de curtosis muestral (Fisher sin sesgo).")


class KolmogorovSmirnovResponse(BaseModel):
    """Resultado de la prueba de Kolmogorov-Smirnov calibrada por Monte Carlo (Lilliefors)."""
    statistic: float = Field(..., description="Estadístico de prueba D (máxima distancia vertical).")
    p_value: float = Field(..., description="Valor-p calibrado por simulación Monte Carlo con reestimación.")
    rejected: bool = Field(..., description="Indica si se rechaza H0 al nivel de significancia especificado.")
    academic_verdict: str = Field(..., description="Interpretación pedagógica y académica del resultado.")
    calibration_method: Optional[str] = Field(None, description="Método de calibración del valor-p.")
    alpha: Optional[float] = Field(None, description="Nivel de significancia evaluado.")


class AndersonDarlingResponse(BaseModel):
    """Resultado de la prueba de Anderson-Darling para distribución normal."""
    statistic: float = Field(..., description="Estadístico de prueba A^2.")
    critical_value: float = Field(..., description="Valor crítico correspondiente al nivel alpha.")
    rejected: bool = Field(..., description="Indica si se rechaza H0 (A^2 > valor crítico).")
    academic_verdict: str = Field(..., description="Interpretación pedagógica destacando sensibilidad en colas.")
    significance_level: Optional[float] = Field(None, description="Nivel de significancia tabulado.")
    alpha: Optional[float] = Field(None, description="Nivel de significancia evaluado.")
    p_value: Optional[float] = Field(None, description="Valor-p (reportado como null respetando el contrato original).")


class ShapiroWilkResponse(BaseModel):
    """Resultado de la prueba de normalidad de Shapiro-Wilk."""
    available: bool = Field(default=True, description="Indica si la prueba se ejecutó satisfactoriamente.")
    statistic: Optional[float] = Field(None, description="Estadístico de prueba W de Shapiro-Wilk.")
    p_value: Optional[float] = Field(None, description="Valor-p de la prueba Shapiro-Wilk.")
    alpha: float = Field(..., description="Nivel de significancia evaluado.")
    rejected: Optional[bool] = Field(None, description="Indica si se rechaza H0 al nivel alpha (p < alpha).")
    method: str = Field(default="Shapiro-Wilk", description="Nombre del método estadístico.")
    warnings: List[str] = Field(default_factory=list, description="Advertencias estadísticas asociadas al cálculo.")
    academic_verdict: str = Field(..., description="Interpretación pedagógica y académica del resultado.")
    reason: Optional[str] = Field(None, description="Motivo en caso de que la prueba no esté disponible.")


class ChiSquareResponse(BaseModel):
    """Resultado de la prueba Chi-cuadrada de bondad de ajuste con fusión de clases."""
    available: bool = Field(..., description="Indica si la prueba pudo ejecutarse válidamente.")
    statistic: Optional[float] = Field(None, description="Estadístico de prueba Chi-cuadrada (EP).")
    degrees_of_freedom: Optional[int] = Field(None, description="Grados de libertad v = k_ajustado - 3.")
    critical_value: Optional[float] = Field(None, description="Valor crítico chi2(1 - alpha, v).")
    p_value: Optional[float] = Field(None, description="Valor-p chi2.sf(EP, v).")
    merged_classes_count: int = Field(..., description="Número de clases finales tras fusión (Ei >= 5).")
    rejected: Optional[bool] = Field(None, description="Indica si se rechaza H0 (EP > valor crítico).")
    academic_verdict: str = Field(..., description="Interpretación académica del resultado o diagnóstico de no aplicabilidad.")
    reason: Optional[str] = Field(None, description="Motivo por el cual la prueba no estuvo disponible, si aplica.")
    initial_classes_count: Optional[int] = Field(None, description="Número inicial de clases calculado (2^k > n).")
    merged_classes: Optional[List[Dict[str, Any]]] = Field(None, description="Detalle de clases fusionadas.")


class GoodnessOfFitContainer(BaseModel):
    """Contenedor de las cuatro pruebas de bondad de ajuste."""
    kolmogorov_smirnov: KolmogorovSmirnovResponse
    anderson_darling: AndersonDarlingResponse
    shapiro_wilk: ShapiroWilkResponse
    chi_square: ChiSquareResponse


class GoodnessOfFitResponse(BaseModel):
    """Respuesta completa del endpoint de bondad de ajuste."""
    descriptive_metrics: DescriptiveMetricsResponse
    goodness_of_fit: GoodnessOfFitContainer
    pedagogical_synthesis: str = Field(..., description="Síntesis académica global integrada.")


# =============================================================================
# Modelos de Respuesta para Comparación de Muestras
# =============================================================================

class SampleSizesResponse(BaseModel):
    """Tamaño de las muestras en la comparación."""
    sample_a: int = Field(..., description="Número de observaciones del Grupo A.")
    sample_b: int = Field(..., description="Número de observaciones del Grupo B.")


class LeveneResponse(BaseModel):
    """Resultado de la prueba de Levene para homocedasticidad."""
    statistic: Optional[float] = Field(..., description="Estadístico W de Levene.")
    p_value: Optional[float] = Field(..., description="Valor-p de Levene al 5% fijo.")
    equal_variances: bool = Field(..., description="Indica si se asumen varianzas iguales (p > 0.05).")
    academic_verdict: str = Field(..., description="Interpretación académica sobre homocedasticidad.")
    significance_level: Optional[float] = Field(0.05, description="Nivel de significancia fijo de Levene (5%).")
    rejected: Optional[bool] = Field(None, description="Indica si se rechaza la igualdad de varianzas.")


class StudentTResponse(BaseModel):
    """Resultado de la prueba t-Student (o Welch) para diferencia de medias."""
    statistic: Optional[float] = Field(..., description="Estadístico t.")
    p_value: Optional[float] = Field(..., description="Valor-p bilateral.")
    equal_var: bool = Field(..., description="Indica si se empleó la variante estándar (True) o Welch (False).")
    rejected: bool = Field(..., description="Indica si se rechaza la igualdad de medias al nivel alpha.")
    method: Optional[str] = Field(None, description="Variante metodológica empleada.")
    verdict: Optional[str] = Field(None, description="Dictamen específico de la prueba t.")


class MannWhitneyResponse(BaseModel):
    """Resultado de la prueba U de Mann-Whitney (no paramétrica)."""
    statistic: Optional[float] = Field(..., description="Estadístico U.")
    p_value: Optional[float] = Field(..., description="Valor-p bilateral.")
    rejected: bool = Field(..., description="Indica si se rechaza H0 al nivel alpha.")
    verdict: Optional[str] = Field(None, description="Dictamen específico de Mann-Whitney.")


class CompareSamplesResponse(BaseModel):
    """Respuesta completa del endpoint de comparación de dos muestras independientes."""
    sample_sizes: SampleSizesResponse
    levene: LeveneResponse
    student_t: StudentTResponse
    mann_whitney_u: MannWhitneyResponse
    pedagogical_synthesis: str = Field(..., description="Síntesis pedagógica completa de la comparación.")

