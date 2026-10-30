import React from 'react';
import {
  Stack,
  SimpleGrid,
  Paper,
  Text,
  Title,
  Alert,
  Button,
  Group,
  useComputedColorScheme,
  Badge,
} from '@mantine/core';
import {
  IconChartBar,
  IconInfoCircle,
  IconArrowLeft,
  IconLayersLinked,
} from '@tabler/icons-react';
import { HistogramNormalPlot } from './HistogramNormalPlot';
import { BoxplotPlot } from './BoxplotPlot';

export function VisualizationsTab({
  analyzedSample,
  descriptiveMetrics,
  onGoToAnalysis,
}) {
  const computedColorScheme = useComputedColorScheme('light');
  const isDarkMode = computedColorScheme === 'dark';

  if (!analyzedSample || analyzedSample.length === 0 || !descriptiveMetrics) {
    return (
      <Paper withBorder p="xl" radius="md" ta="center">
        <Stack align="center" gap="md" py="xl">
          <IconChartBar size={48} color="var(--mantine-color-blue-5)" />
          <Title order={3}>No hay observaciones analizadas</Title>
          <Text size="sm" c="dimmed" maw={520}>
            Para generar el histograma con curva normal teórica y el diagrama de cajas y bigotes,
            primero ingrese o cargue una muestra y ejecute el análisis en la pestaña de{' '}
            <strong>Bondad de Ajuste</strong>.
          </Text>
          <Button
            variant="light"
            color="blue"
            leftSection={<IconArrowLeft size={16} />}
            onClick={onGoToAnalysis}
          >
            Ir a Análisis de Normalidad
          </Button>
        </Stack>
      </Paper>
    );
  }

  return (
    <Stack gap="lg">
      <Group justify="space-between" align="center" wrap="wrap">
        <div>
          <Title order={3} style={{ letterSpacing: '-0.01em' }}>
            Visualizaciones Estadísticas de la Muestra
          </Title>
          <Text size="xs" c="dimmed">
            Exploración gráfica de simetría, colas, dispersión y concordancia con la distribución teórica
          </Text>
        </div>
        <Badge color="blue" variant="light" size="lg">
          n = {analyzedSample.length} observaciones analizadas
        </Badge>
      </Group>

      <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg">
        <HistogramNormalPlot
          data={analyzedSample}
          mean={descriptiveMetrics.mean}
          stdDev={descriptiveMetrics.std_dev}
          isDarkMode={isDarkMode}
        />
        <BoxplotPlot
          data={analyzedSample}
          isDarkMode={isDarkMode}
        />
      </SimpleGrid>

      <Alert
        icon={<IconInfoCircle size={18} />}
        color="indigo"
        variant="light"
        title="Orientación Pedagógica sobre la Interpretación Gráfica"
      >
        <Text size="xs" style={{ lineHeight: 1.6 }}>
          • <strong>Histograma vs. Curva Normal</strong>: Permite evaluar visualmente si la concentración central
          y el decrecimiento en las colas coinciden con la campana de Gauss ajustada.
          <br />
          • <strong>Diagrama de Cajas (Boxplot)</strong>: Si la línea de la mediana no se encuentra centrada en la
          caja o los bigotes tienen longitudes asimétricas, la muestra exhibe sesgo. Los puntos aislados denotan
          observaciones atípicas que pueden alterar significativamente pruebas sensibles en colas como Anderson-Darling.
          <br />
          • <strong>Importante</strong>: Las representaciones gráficas son herramientas exploratorias complementarias.
          La decisión inferencial formal se basa exclusivamente en los estadísticos y valores-p de las pruebas de hipótesis.
        </Text>
      </Alert>
    </Stack>
  );
}

