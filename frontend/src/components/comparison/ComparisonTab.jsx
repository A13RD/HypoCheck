import React, { useState, useMemo, useRef, useEffect } from 'react';
import {
  Stack,
  SimpleGrid,
  Paper,
  Text,
  Title,
  Textarea,
  Select,
  Group,
  Button,
  Badge,
  Alert,
  Table,
  Divider,
  Box,
  ThemeIcon,
  Tooltip,
} from '@mantine/core';
import {
  IconGitCompare,
  IconTrash,
  IconCheck,
  IconX,
  IconAlertTriangle,
  IconInfoCircle,
  IconDatabase,
  IconScale,
} from '@tabler/icons-react';
import { parseSampleInput } from '../analysis/DataInputPanel';
import { PRESET_TWO_SAMPLES } from '../../data/presets';
import { compareIndependentSamples } from '../../services/api';

function formatVal(val, decimals = 4) {
  if (val === null || val === undefined || Number.isNaN(val)) return 'N/D';
  const num = Number(val);
  if (num !== 0 && Math.abs(num) < Math.pow(10, -decimals)) {
    return num.toExponential(3);
  }
  return num.toFixed(decimals);
}

export function ComparisonTab({ onHealthUpdate }) {
  const [sampleAText, setSampleAText] = useState('');
  const [sampleBText, setSampleBText] = useState('');
  const [alpha, setAlpha] = useState(0.05);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [analyzedAlpha, setAnalyzedAlpha] = useState(0.05);
  const [isStale, setIsStale] = useState(false);

  const abortControllerRef = useRef(null);

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const parsedA = useMemo(() => parseSampleInput(sampleAText), [sampleAText]);
  const parsedB = useMemo(() => parseSampleInput(sampleBText), [sampleBText]);

  const isValidA = parsedA.count >= 5 && parsedA.invalidTokens.length === 0;
  const isValidB = parsedB.count >= 5 && parsedB.invalidTokens.length === 0;
  const canCompare = isValidA && isValidB && !isLoading;

  const handleLoadPreset = () => {
    setSampleAText(PRESET_TWO_SAMPLES.sampleA.join(', '));
    setSampleBText(PRESET_TWO_SAMPLES.sampleB.join(', '));
    setError(null);
    if (result) setIsStale(true);
  };

  const handleClear = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsLoading(false);
    setSampleAText('');
    setSampleBText('');
    setResult(null);
    setError(null);
    setIsStale(false);
  };

  const handleInputChangeA = (val) => {
    setSampleAText(val);
    if (result) setIsStale(true);
  };

  const handleInputChangeB = (val) => {
    setSampleBText(val);
    if (result) setIsStale(true);
  };

  const handleAlphaChange = (val) => {
    setAlpha(val);
    if (result) setIsStale(true);
  };

  const handleCompare = async () => {
    if (!canCompare) return;

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setIsLoading(true);
    setError(null);

    try {
      const data = await compareIndependentSamples(
        parsedA.numbers,
        parsedB.numbers,
        alpha,
        controller.signal
      );
      if (abortControllerRef.current !== controller) return;
      setResult(data);
      setAnalyzedAlpha(alpha);
      setIsStale(false);
      if (onHealthUpdate) {
        onHealthUpdate((prev) =>
          prev?.available ? prev : { available: true, status: 'healthy', version: '1.0.0' }
        );
      }
    } catch (err) {
      if (err.name === 'AbortError' || abortControllerRef.current !== controller) return;
      setError(err.message || 'Ocurrió un error al procesar la comparación de muestras.');
      if (err.status === null && onHealthUpdate) {
        onHealthUpdate({ available: false, status: 'offline', message: err.message });
      }
    } finally {
      if (abortControllerRef.current === controller) {
        setIsLoading(false);
      }
    }
  };

  return (
    <Stack gap="lg">
      <Group justify="space-between" align="center" wrap="wrap">
        <div>
          <Title order={3} style={{ letterSpacing: '-0.01em' }}>
            Comparación de Dos Muestras Independientes
          </Title>
          <Text size="xs" c="dimmed">
            Evaluación de homocedasticidad (Levene) y contrastes de hipótesis paramétricos (t-Student / Welch) y no paramétricos (Mann-Whitney U)
          </Text>
        </div>
        <Button
          variant="light"
          color="indigo"
          size="xs"
          leftSection={<IconDatabase size={14} />}
          onClick={handleLoadPreset}
        >
          Cargar muestras reproducibles de ejemplo
        </Button>
      </Group>

      {/* Panel de entrada de datos de ambos grupos */}
      <Paper withBorder p="md" radius="md">
        <Stack gap="md">
          <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
            {/* Grupo A */}
            <Box>
              <Group justify="space-between" align="center" mb={4}>
                <Text size="sm" fw={600}>
                  Grupo A (Control / Referencia)
                </Text>
                <Badge
                  color={parsedA.count === 0 ? 'gray' : isValidA ? 'teal' : 'red'}
                  variant="light"
                  size="sm"
                >
                  n_A = {parsedA.count} (Mínimo 5)
                </Badge>
              </Group>
              <Textarea
                placeholder="Observaciones de A separadas por comas o saltos de línea. Ej: 50.2, 53.1, 49.8, 54.3, 51.7"
                minRows={4}
                maxRows={7}
                autosize
                value={sampleAText}
                onChange={(e) => handleInputChangeA(e.currentTarget.value)}
                disabled={isLoading}
                error={
                  parsedA.invalidTokens.length > 0
                    ? `Tokens no numéricos (${parsedA.invalidTokens.slice(0, 3).join(', ')})`
                    : null
                }
              />
            </Box>

            {/* Grupo B */}
            <Box>
              <Group justify="space-between" align="center" mb={4}>
                <Text size="sm" fw={600}>
                  Grupo B (Tratamiento / Modificado)
                </Text>
                <Badge
                  color={parsedB.count === 0 ? 'gray' : isValidB ? 'teal' : 'red'}
                  variant="light"
                  size="sm"
                >
                  n_B = {parsedB.count} (Mínimo 5)
                </Badge>
              </Group>
              <Textarea
                placeholder="Observaciones de B separadas por comas o saltos de línea. Ej: 60.5, 62.1, 58.7, 63.4, 61.2"
                minRows={4}
                maxRows={7}
                autosize
                value={sampleBText}
                onChange={(e) => handleInputChangeB(e.currentTarget.value)}
                disabled={isLoading}
                error={
                  parsedB.invalidTokens.length > 0
                    ? `Tokens no numéricos (${parsedB.invalidTokens.slice(0, 3).join(', ')})`
                    : null
                }
              />
            </Box>
          </SimpleGrid>

          <Group justify="space-between" align="flex-end" wrap="wrap">
            <Box style={{ minWidth: '220px' }}>
              <Select
                label="Nivel de significancia (α)"
                description="Para t-Student y Mann-Whitney U (Levene evalúa al 5% fijo)"
                value={String(alpha)}
                onChange={(val) => handleAlphaChange(Number(val))}
                data={[
                  { value: '0.01', label: 'α = 0.01 (99% confianza)' },
                  { value: '0.05', label: 'α = 0.05 (95% confianza - Estándar)' },
                  { value: '0.10', label: 'α = 0.10 (90% confianza)' },
                ]}
                disabled={isLoading}
                size="sm"
              />
            </Box>

            <Group gap="sm">
              <Button
                variant="subtle"
                color="gray"
                leftSection={<IconTrash size={16} />}
                onClick={handleClear}
                disabled={isLoading || (!sampleAText && !sampleBText)}
                size="sm"
              >
                Limpiar muestras
              </Button>

              <Button
                variant="filled"
                color="blue"
                leftSection={<IconGitCompare size={16} />}
                onClick={handleCompare}
                loading={isLoading}
                disabled={!canCompare}
                size="sm"
              >
                Comparar muestras
              </Button>
            </Group>
          </Group>

          {isStale && result && (
            <Alert
              icon={<IconAlertTriangle size={16} />}
              color="yellow"
              variant="light"
              title="Entradas modificadas"
            >
              <Text size="xs">
                Las observaciones o el nivel de significancia fueron modificados. Los resultados abajo corresponden al análisis previo. Pulse <strong>Comparar muestras</strong> para recalcular con FastAPI.
              </Text>
            </Alert>
          )}

          {error && (
            <Alert
              icon={<IconAlertTriangle size={16} />}
              color="red"
              variant="light"
              title="Error al comparar muestras"
            >
              <Text size="xs">{error}</Text>
            </Alert>
          )}
        </Stack>
      </Paper>

      {/* Resultados de la comparación */}
      {result && (
        <Stack gap="md">
          <Group justify="space-between" align="center" wrap="wrap">
            <Group gap="xs">
              <Badge color="blue" variant="light" size="md">
                Grupo A: n = {result.sample_sizes?.sample_a}
              </Badge>
              <Badge color="indigo" variant="light" size="md">
                Grupo B: n = {result.sample_sizes?.sample_b}
              </Badge>
            </Group>
            <Badge variant="outline" color="blue">
              Nivel evaluado: α = {analyzedAlpha}
            </Badge>
          </Group>

          <SimpleGrid cols={{ base: 1, md: 3 }} spacing="md">
            {/* 1. Levene */}
            <Paper withBorder p="md" radius="md" className="stat-card">
              <Stack gap="xs">
                <Group justify="space-between" align="flex-start">
                  <div>
                    <Text size="xs" c="dimmed" fw={600} style={{ textTransform: 'uppercase' }}>
                      Prueba de Levene
                    </Text>
                    <Text fw={700} size="md">
                      Homocedasticidad (Varianzas)
                    </Text>
                  </div>
                  <ThemeIcon color="cyan" variant="light" size="md">
                    <IconScale size={16} />
                  </ThemeIcon>
                </Group>

                <Divider />

                <Group justify="space-between">
                  <Text size="xs" c="dimmed">
                    Estadístico W:
                  </Text>
                  <Text size="xs" ff="monospace" fw={600}>
                    {formatVal(result.levene.statistic)}
                  </Text>
                </Group>

                <Group justify="space-between">
                  <Text size="xs" c="dimmed">
                    Valor-p (α = 0.05):
                  </Text>
                  <Text
                    size="xs"
                    ff="monospace"
                    fw={700}
                    c={result.levene.p_value < 0.05 ? 'orange' : 'teal'}
                  >
                    {formatVal(result.levene.p_value)}
                  </Text>
                </Group>

                <Group justify="space-between" align="center" mt="xs">
                  <Text size="xs" fw={600}>
                    Decisión:
                  </Text>
                  <Badge
                    color={result.levene.equal_variances ? 'teal' : 'orange'}
                    variant="filled"
                    size="sm"
                  >
                    {result.levene.equal_variances
                      ? 'Varianzas Homogéneas'
                      : 'Varianzas Heterogéneas'}
                  </Badge>
                </Group>

                <Text size="xs" c="dimmed" mt="xs">
                  {result.levene.academic_verdict}
                </Text>
              </Stack>
            </Paper>

            {/* 2. Student's t / Welch */}
            <Paper withBorder p="md" radius="md" className="stat-card">
              <Stack gap="xs">
                <Group justify="space-between" align="flex-start">
                  <div>
                    <Text size="xs" c="dimmed" fw={600} style={{ textTransform: 'uppercase' }}>
                      Prueba Paramétrica
                    </Text>
                    <Text fw={700} size="md">
                      t-Student / Welch
                    </Text>
                  </div>
                  <Badge
                    color={result.student_t.equal_var ? 'blue' : 'indigo'}
                    variant="light"
                    size="xs"
                  >
                    {result.student_t.equal_var ? 't Clásica (Pooled)' : 't de Welch'}
                  </Badge>
                </Group>

                <Divider />

                <Group justify="space-between">
                  <Text size="xs" c="dimmed">
                    Estadístico t:
                  </Text>
                  <Text size="xs" ff="monospace" fw={600}>
                    {formatVal(result.student_t.statistic)}
                  </Text>
                </Group>

                <Group justify="space-between">
                  <Text size="xs" c="dimmed">
                    Valor-p bilateral:
                  </Text>
                  <Text
                    size="xs"
                    ff="monospace"
                    fw={700}
                    c={result.student_t.p_value < analyzedAlpha ? 'red' : 'teal'}
                  >
                    {formatVal(result.student_t.p_value)}
                  </Text>
                </Group>

                <Group justify="space-between" align="center" mt="xs">
                  <Text size="xs" fw={600}>
                    Decisión (α = {analyzedAlpha}):
                  </Text>
                  <Badge
                    color={result.student_t.rejected ? 'red' : 'teal'}
                    variant="filled"
                    size="sm"
                    leftSection={
                      result.student_t.rejected ? <IconX size={12} /> : <IconCheck size={12} />
                    }
                  >
                    {result.student_t.rejected ? 'Rechaza H₀ (Medias ≠)' : 'No rechaza H₀'}
                  </Badge>
                </Group>

                <Text size="xs" c="dimmed" mt="xs">
                  {result.student_t.verdict || result.student_t.method}
                </Text>
              </Stack>
            </Paper>

            {/* 3. Mann-Whitney U */}
            <Paper withBorder p="md" radius="md" className="stat-card">
              <Stack gap="xs">
                <Group justify="space-between" align="flex-start">
                  <div>
                    <Text size="xs" c="dimmed" fw={600} style={{ textTransform: 'uppercase' }}>
                      Prueba No Paramétrica
                    </Text>
                    <Text fw={700} size="md">
                      Mann-Whitney U
                    </Text>
                  </div>
                  <Badge color="violet" variant="light" size="xs">
                    Basada en Rangos
                  </Badge>
                </Group>

                <Divider />

                <Group justify="space-between">
                  <Text size="xs" c="dimmed">
                    Estadístico U:
                  </Text>
                  <Text size="xs" ff="monospace" fw={600}>
                    {formatVal(result.mann_whitney_u.statistic)}
                  </Text>
                </Group>

                <Group justify="space-between">
                  <Text size="xs" c="dimmed">
                    Valor-p bilateral:
                  </Text>
                  <Text
                    size="xs"
                    ff="monospace"
                    fw={700}
                    c={result.mann_whitney_u.p_value < analyzedAlpha ? 'red' : 'teal'}
                  >
                    {formatVal(result.mann_whitney_u.p_value)}
                  </Text>
                </Group>

                <Group justify="space-between" align="center" mt="xs">
                  <Text size="xs" fw={600}>
                    Decisión (α = {analyzedAlpha}):
                  </Text>
                  <Badge
                    color={result.mann_whitney_u.rejected ? 'red' : 'teal'}
                    variant="filled"
                    size="sm"
                    leftSection={
                      result.mann_whitney_u.rejected ? <IconX size={12} /> : <IconCheck size={12} />
                    }
                  >
                    {result.mann_whitney_u.rejected ? 'Rechaza H₀ (Rangos ≠)' : 'No rechaza H₀'}
                  </Badge>
                </Group>

                <Text size="xs" c="dimmed" mt="xs">
                  {result.mann_whitney_u.verdict ||
                    'Evalúa si una distribución domina estocásticamente a la otra mediante la suma de rangos conjuntos.'}
                </Text>
              </Stack>
            </Paper>
          </SimpleGrid>

          {/* Síntesis pedagógica de la comparación */}
          <Paper
            withBorder
            p="lg"
            radius="md"
            style={{
              borderLeft: '4px solid var(--mantine-color-blue-6)',
              backgroundColor: 'var(--mantine-color-default-hover)',
            }}
          >
            <Stack gap="sm">
              <Group gap="xs">
                <IconInfoCircle size={18} color="var(--mantine-color-blue-6)" />
                <Text fw={600} size="sm">
                  Síntesis Metodológica de la Comparación
                </Text>
              </Group>

              <Text size="sm" style={{ whiteSpace: 'pre-line', lineHeight: 1.65 }}>
                {result.pedagogical_synthesis}
              </Text>

              <Alert
                color="indigo"
                variant="subtle"
                title="Directrices para la sustentación sobre dos muestras"
              >
                <Text size="xs" c="dimmed">
                  1. <strong>Levene no evalúa normalidad</strong>: únicamente evalúa si las varianzas poblacionales son homogéneas (H₀: σ₁² = σ₂²).
                  <br />
                  2. <strong>Selección t vs. Welch</strong>: si Levene rechaza la igualdad de varianzas, se selecciona la prueba t de Welch; no es correcto saltar a Mann-Whitney únicamente por heterocedasticidad si la normalidad se cumple.
                  <br />
                  3. <strong>Alcance de Mann-Whitney</strong>: contrasta la distribución de rangos (dominancia estocástica). Sólo puede interpretarse como prueba estricta de medianas si se asume que ambas distribuciones tienen exactamente la misma forma geométrica.
                </Text>
              </Alert>
            </Stack>
          </Paper>
        </Stack>
      )}
    </Stack>
  );
}

