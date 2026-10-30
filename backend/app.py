"""
Servidor principal FastAPI para la Suite de Inferencia Estadística y Bondad de Ajuste.

Expone los endpoints REST para el consumo del motor estadístico:
- POST /api/v1/goodness-of-fit: Análisis descriptivo, K-S, Anderson-Darling, Chi-cuadrada y síntesis.
- POST /api/v1/compare-samples: Homocedasticidad (Levene), t-Student / Welch y Mann-Whitney U.
- GET /: Verificación básica del servicio y enlaces a la documentación.
- GET /health: Health check de disponibilidad.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

try:
    from backend.engine_estadistico import (
        MotorEstadistico,
        DatosInvalidosError,
        ParametroInvalidoError,
    )
    from backend.schemas import (
        GoodnessOfFitRequest,
        GoodnessOfFitResponse,
        GoodnessOfFitContainer,
        DescriptiveMetricsResponse,
        KolmogorovSmirnovResponse,
        AndersonDarlingResponse,
        ChiSquareResponse,
        CompareSamplesRequest,
        CompareSamplesResponse,
        SampleSizesResponse,
        LeveneResponse,
        StudentTResponse,
        MannWhitneyResponse,
    )
except ImportError:
    from engine_estadistico import (
        MotorEstadistico,
        DatosInvalidosError,
        ParametroInvalidoError,
    )
    from schemas import (
        GoodnessOfFitRequest,
        GoodnessOfFitResponse,
        GoodnessOfFitContainer,
        DescriptiveMetricsResponse,
        KolmogorovSmirnovResponse,
        AndersonDarlingResponse,
        ChiSquareResponse,
        CompareSamplesRequest,
        CompareSamplesResponse,
        SampleSizesResponse,
        LeveneResponse,
        StudentTResponse,
        MannWhitneyResponse,
    )

# Configuración del registrador de eventos (logging)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("HypoCheckBackend")

# Instancia central de FastAPI
app = FastAPI(
    title="Suite de Inferencia Estadística y Bondad de Ajuste API",
    description=(
        "API REST científica para la evaluación de bondad de ajuste a la distribución normal "
        "(Kolmogorov-Smirnov, Anderson-Darling, Chi-cuadrada de Pearson) y comparación inferencial "
        "de dos muestras independientes (Levene, t-Student, Welch, Mann-Whitney U).\n\n"
        "Desarrollado para Estadística para Ingeniería — Universidad de Medellín (2026-2)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuración de CORS
cors_env = os.getenv("CORS_ORIGINS", "")
if cors_env.strip():
    allowed_origins = [o.strip() for o in cors_env.split(",") if o.strip()]
else:
    # Orígenes de desarrollo locales para Vite, Live Server y puertos estándar
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Instancia reutilizable y sin estado del motor estadístico
motor_estadistico = MotorEstadistico()


# =============================================================================
# Manejadores de Excepciones Globales
# =============================================================================

@app.exception_handler(DatosInvalidosError)
async def datos_invalidos_handler(request: Request, exc: DatosInvalidosError) -> JSONResponse:
    """Gestiona errores cuando una muestra estadística incumple condiciones del motor."""
    logger.warning("Error de datos estadísticos inválidos en %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )


@app.exception_handler(ParametroInvalidoError)
async def parametro_invalido_handler(request: Request, exc: ParametroInvalidoError) -> JSONResponse:
    """Gestiona errores de parámetros de configuración estadística inválidos."""
    logger.warning("Error de parámetro estadístico inválido en %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Captura cualquier excepción no prevista sin exponer rutas internas ni trazas sensibles."""
    logger.error("Error no controlado procesando %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor al procesar el análisis estadístico."},
    )


# =============================================================================
# Endpoints Complementarios
# =============================================================================

@app.get(
    "/",
    tags=["General"],
    summary="Información de la API",
    description="Devuelve el estado general del servicio, versión y enlaces a la documentación interactiva.",
)
def root_info() -> Dict[str, str]:
    """Retorna información general de la API."""
    return {
        "message": "Suite de Inferencia Estadística y Bondad de Ajuste API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }


@app.get(
    "/health",
    tags=["General"],
    summary="Verificación de disponibilidad (Health Check)",
    description="Confirma la disponibilidad y operatividad básica del servicio FastAPI.",
)
def health_check() -> Dict[str, str]:
    """Retorna estado saludable del servicio."""
    return {
        "status": "healthy"
    }


# =============================================================================
# Endpoints Estadísticos Principales
# =============================================================================

@app.post(
    "/api/v1/goodness-of-fit",
    response_model=GoodnessOfFitResponse,
    status_code=status.HTTP_200_OK,
    tags=["Estadística"],
    summary="Análisis de bondad de ajuste a la distribución normal",
    description=(
        "Ejecuta el análisis estadístico descriptivo y las tres pruebas de bondad de ajuste "
        "(Kolmogorov-Smirnov con p-valor calibrado por Lilliefors Monte Carlo, Anderson-Darling "
        "con valores críticos dinámicos, y Chi-cuadrada de Pearson con fusión de clases Ei >= 5), "
        "generando además una síntesis pedagógica integral."
    ),
)
def goodness_of_fit_endpoint(solicitud: GoodnessOfFitRequest) -> GoodnessOfFitResponse:
    """
    Controlador para el análisis de bondad de ajuste.
    """
    datos = solicitud.data
    alpha = solicitud.alpha

    logger.info("Procesando bondad de ajuste: n=%d, alpha=%.4f", len(datos), alpha)

    # 1. Medidas descriptivas
    metricas = motor_estadistico.calcular_metricas_descriptivas(datos)

    # 2. Kolmogorov-Smirnov
    ks = motor_estadistico.prueba_kolmogorov_smirnov_normal(datos, alpha=alpha)

    # 3. Anderson-Darling
    ad = motor_estadistico.prueba_anderson_darling_normal(datos, alpha=alpha)

    # 4. Chi-cuadrada de Pearson (puede resultar en available=False sin generar error HTTP)
    chi2 = motor_estadistico.prueba_chi_cuadrada_normal(datos, alpha=alpha)

    # 5. Síntesis pedagógica
    sintesis = motor_estadistico.generar_sintesis_pedagogica(ks, ad, chi2)

    return GoodnessOfFitResponse(
        descriptive_metrics=DescriptiveMetricsResponse(
            n=metricas["n"],
            mean=metricas["mean"],
            variance=metricas["variance"],
            std_dev=metricas["std_dev"],
            skewness=metricas["skewness"],
            kurtosis=metricas["kurtosis"],
        ),
        goodness_of_fit=GoodnessOfFitContainer(
            kolmogorov_smirnov=KolmogorovSmirnovResponse(
                statistic=ks["statistic"],
                p_value=ks["p_value"],
                rejected=ks["rejected"],
                academic_verdict=ks["academic_verdict"],
                calibration_method=ks.get("calibration_method"),
                alpha=ks.get("alpha"),
            ),
            anderson_darling=AndersonDarlingResponse(
                statistic=ad["statistic"],
                critical_value=ad["critical_value"],
                rejected=ad["rejected"],
                academic_verdict=ad["academic_verdict"],
                significance_level=ad.get("significance_level"),
                alpha=ad.get("alpha"),
                p_value=ad.get("p_value"),
            ),
            chi_square=ChiSquareResponse(
                available=chi2["available"],
                statistic=chi2.get("statistic"),
                degrees_of_freedom=chi2.get("degrees_of_freedom"),
                critical_value=chi2.get("critical_value"),
                p_value=chi2.get("p_value"),
                merged_classes_count=chi2.get("merged_classes_count", 0),
                rejected=chi2.get("rejected"),
                academic_verdict=chi2["academic_verdict"],
                reason=chi2.get("reason"),
                initial_classes_count=chi2.get("initial_classes_count"),
                merged_classes=chi2.get("merged_classes"),
            ),
        ),
        pedagogical_synthesis=sintesis,
    )


@app.post(
    "/api/v1/compare-samples",
    response_model=CompareSamplesResponse,
    status_code=status.HTTP_200_OK,
    tags=["Estadística"],
    summary="Comparación de dos muestras independientes",
    description=(
        "Evalúa la igualdad de varianzas mediante la prueba de Levene al 5% fijo, "
        "aplica la prueba t-Student correspondiente (estándar con homocedasticidad "
        "o Welch con heterocedasticidad) y la prueba no paramétrica U de Mann-Whitney bilateral, "
        "generando una interpretación pedagógica rigurosa."
    ),
)
def compare_samples_endpoint(solicitud: CompareSamplesRequest) -> CompareSamplesResponse:
    """
    Controlador para la comparación inferencial de dos muestras.
    """
    sample_a = solicitud.sample_a
    sample_b = solicitud.sample_b
    alpha = solicitud.alpha

    logger.info(
        "Procesando comparación de muestras: n_a=%d, n_b=%d, alpha=%.4f",
        len(sample_a),
        len(sample_b),
        alpha,
    )

    # Delegación completa en el motor estadístico
    res = motor_estadistico.comparar_muestras(sample_a, sample_b, alpha=alpha)

    levene_info = res["levene"]
    levene_verdict = (
        "Se rechaza la hipótesis de igualdad de varianzas (p <= 0.05). Las muestras presentan heterocedasticidad; se procede con Welch t-test."
        if levene_info["rejected"]
        else "No se rechaza la hipótesis de igualdad de varianzas (p > 0.05). Las muestras presentan homocedasticidad; se procede con Student t-test estándar."
    )

    return CompareSamplesResponse(
        sample_sizes=SampleSizesResponse(
            sample_a=res["n_a"],
            sample_b=res["n_b"],
        ),
        levene=LeveneResponse(
            statistic=levene_info["statistic"],
            p_value=levene_info["p_value"],
            equal_variances=levene_info["equal_var"],
            academic_verdict=levene_verdict,
            significance_level=levene_info.get("significance_level", 0.05),
            rejected=levene_info.get("rejected"),
        ),
        student_t=StudentTResponse(
            statistic=res["t_test"]["statistic"],
            p_value=res["t_test"]["p_value"],
            equal_var=res["t_test"]["equal_var"],
            rejected=res["t_test"]["rejected"],
            method=res["t_test"].get("method"),
            verdict=res["t_test"].get("verdict"),
        ),
        mann_whitney_u=MannWhitneyResponse(
            statistic=res["mann_whitney_u"]["statistic"],
            p_value=res["mann_whitney_u"]["p_value"],
            rejected=res["mann_whitney_u"]["rejected"],
            verdict=res["mann_whitney_u"].get("verdict"),
        ),
        pedagogical_synthesis=res["academic_interpretation"],
    )

