import React, { useState, useEffect, useCallback, useRef, Suspense, lazy } from 'react';
import {
  Container,
  Tabs,
  Stack,
  Alert,
  Loader,
  Center,
  Text,
} from '@mantine/core';
import {
  IconChecklist,
  IconChartBar,
  IconGitCompare,
  IconAlertTriangle,
} from '@tabler/icons-react';

import { Header } from './components/layout/Header';
import { Footer } from './components/layout/Footer';
import { PresetSelector } from './components/analysis/PresetSelector';
import { DataInputPanel } from './components/analysis/DataInputPanel';
import { DescriptiveMetricsGrid } from './components/analysis/DescriptiveMetricsGrid';
import { GoodnessOfFitTable } from './components/analysis/GoodnessOfFitTable';
import { PedagogicalSynthesisCard } from './components/analysis/PedagogicalSynthesisCard';
import { ComparisonTab } from './components/comparison/ComparisonTab';

// Carga diferida / bajo demanda (lazy loading) del módulo de gráficos Plotly
const VisualizationsTab = lazy(() =>
  import('./components/charts/VisualizationsTab').then((module) => ({
    default: module.VisualizationsTab,
  }))
);

import { checkApiHealth, analyzeGoodnessOfFit } from './services/api';
import { PRESET_SCENARIOS } from './data/presets';
import classes from './styles/Dashboard.module.css';

export function App() {
  // Estado de conexión con la API
  const [apiHealth, setApiHealth] = useState(null);

  // Navegación por pestañas
  const [activeTab, setActiveTab] = useState('analysis');

  // Estado de la sección 1 (Bondad de ajuste)
  const [rawInput, setRawInput] = useState('');
  const [selectedPresetId, setSelectedPresetId] = useState(null);
  const [alpha, setAlpha] = useState(0.05);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analyzedSample, setAnalyzedSample] = useState(null);
  const [analyzedAlpha, setAnalyzedAlpha] = useState(0.05);
  const [isStale, setIsStale] = useState(false);

  const abortControllerRef = useRef(null);

  // Verificación periódica de salud de la API
  const pollHealth = useCallback(async () => {
    try {
      const health = await checkApiHealth();
      setApiHealth(health);
    } catch {
      setApiHealth({ available: false, status: 'offline' });
    }
  }, []);

  useEffect(() => {
    pollHealth();
    const interval = setInterval(pollHealth, 15000);
    return () => {
      clearInterval(interval);
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [pollHealth]);

  // Manejo de selección de presets
  const handleSelectPreset = (presetId) => {
    const preset = PRESET_SCENARIOS[presetId];
    if (!preset) return;

    setSelectedPresetId(presetId);
    setRawInput(preset.data.join(', '));
    setAnalysisError(null);
    if (analysisResult) {
      setIsStale(true);
    }
  };

  // Manejo de cambios manuales en el editor
  const handleInputChange = (val) => {
    setRawInput(val);
    setSelectedPresetId(null);
    if (analysisResult) {
      setIsStale(true);
    }
  };

  const handleAlphaChange = (val) => {
    setAlpha(val);
    if (analysisResult) {
      setIsStale(true);
    }
  };

  const handleClear = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsAnalyzing(false);
    setRawInput('');
    setSelectedPresetId(null);
    setAnalysisResult(null);
    setAnalyzedSample(null);
    setAnalysisError(null);
    setIsStale(false);
  };

  // Ejecución de análisis de bondad de ajuste con FastAPI
  const handleAnalyze = async (numbers) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setIsAnalyzing(true);
    setAnalysisError(null);

    try {
      const data = await analyzeGoodnessOfFit(numbers, alpha, controller.signal);
      if (abortControllerRef.current !== controller) return;
      setAnalysisResult(data);
      setAnalyzedSample(numbers);
      setAnalyzedAlpha(alpha);
      setIsStale(false);
      setApiHealth((prev) =>
        prev?.available ? prev : { available: true, status: 'healthy', version: '1.0.0' }
      );
    } catch (err) {
      if (err.name === 'AbortError' || abortControllerRef.current !== controller) return;
      setAnalysisError(err.message || 'Error desconocido al procesar la muestra.');
      if (err.status === null) {
        setApiHealth({ available: false, status: 'offline', message: err.message });
      }
    } finally {
      if (abortControllerRef.current === controller) {
        setIsAnalyzing(false);
      }
    }
  };

  return (
    <div className={classes.appWrapper}>
      <Header apiHealth={apiHealth} />

      <Container size="xl" className={classes.mainContainer}>
        <Tabs value={activeTab} onChange={setActiveTab} variant="outline" radius="md">
          <Tabs.List mb="lg" className={classes.tabsList}>
            <Tabs.Tab
              value="analysis"
              leftSection={<IconChecklist size={16} />}
              className={classes.tabItem}
            >
              Bondad de Ajuste y Normalidad
            </Tabs.Tab>

            <Tabs.Tab
              value="charts"
              leftSection={<IconChartBar size={16} />}
              className={classes.tabItem}
            >
              Visualizaciones Estadísticas
              {analyzedSample && (
                <Text component="span" size="xs" c="dimmed" ml={6}>
                  ({analyzedSample.length})
                </Text>
              )}
            </Tabs.Tab>

            <Tabs.Tab
              value="comparison"
              leftSection={<IconGitCompare size={16} />}
              className={classes.tabItem}
            >
              Comparación de Dos Muestras
            </Tabs.Tab>
          </Tabs.List>

          {/* =========================================================================
              SECCIÓN 1: ANÁLISIS DE NORMALIDAD Y BONDAD DE AJUSTE
             ========================================================================= */}
          <Tabs.Panel value="analysis">
            <Stack gap="md">
              <PresetSelector
                selectedPresetId={selectedPresetId}
                onSelectPreset={handleSelectPreset}
                disabled={isAnalyzing}
              />

              <DataInputPanel
                value={rawInput}
                onChange={handleInputChange}
                onClear={handleClear}
                alpha={alpha}
                onAlphaChange={handleAlphaChange}
                onAnalyze={handleAnalyze}
                isLoading={isAnalyzing}
                isStale={isStale}
                hasExistingResults={!!analysisResult}
              />

              {analysisError && (
                <Alert
                  icon={<IconAlertTriangle size={16} />}
                  color="red"
                  variant="light"
                  title="No fue posible completar el análisis"
                >
                  <Text size="xs">{analysisError}</Text>
                </Alert>
              )}

              {isAnalyzing && !analysisResult && (
                <Center py="xl">
                  <Stack align="center" gap="sm">
                    <Loader size="lg" color="blue" />
                    <Text size="sm" c="dimmed">
                      Ejecutando calibración Monte Carlo y batería de pruebas con FastAPI...
                    </Text>
                  </Stack>
                </Center>
              )}

              {analysisResult && (
                <Stack gap="lg">
                  <DescriptiveMetricsGrid metrics={analysisResult.descriptive_metrics} />

                  <GoodnessOfFitTable
                    goodnessOfFit={analysisResult.goodness_of_fit}
                    alpha={analyzedAlpha}
                  />

                  <PedagogicalSynthesisCard
                    synthesisText={analysisResult.pedagogical_synthesis}
                    warnings={analysisResult.goodness_of_fit?.shapiro_wilk?.warnings}
                  />
                </Stack>
              )}
            </Stack>
          </Tabs.Panel>

          {/* =========================================================================
              SECCIÓN 2: VISUALIZACIONES ESTADÍSTICAS (PLOTLY)
             ========================================================================= */}
          <Tabs.Panel value="charts">
            <Suspense
              fallback={
                <Center py="xl">
                  <Stack align="center" gap="sm">
                    <Loader size="lg" color="blue" />
                    <Text size="sm" c="dimmed">
                      Cargando módulo de gráficos estadísticos (Plotly)...
                    </Text>
                  </Stack>
                </Center>
              }
            >
              <VisualizationsTab
                analyzedSample={analyzedSample}
                descriptiveMetrics={analysisResult?.descriptive_metrics}
                onGoToAnalysis={() => setActiveTab('analysis')}
              />
            </Suspense>
          </Tabs.Panel>

          {/* =========================================================================
              SECCIÓN 3: COMPARACIÓN DE DOS MUESTRAS
             ========================================================================= */}
          <Tabs.Panel value="comparison">
            <ComparisonTab onHealthUpdate={setApiHealth} />
          </Tabs.Panel>
        </Tabs>
      </Container>

      <Footer />
    </div>
  );
}

