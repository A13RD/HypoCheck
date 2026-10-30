import React from 'react';
import { SimpleGrid, Paper, Text, Group, Box, Tooltip } from '@mantine/core';

function formatNumber(val, decimals = 4) {
  if (val === null || val === undefined || Number.isNaN(val)) {
    return 'N/D';
  }
  return Number(val).toLocaleString('es-CO', {
    minimumFractionDigits: 2,
    maximumFractionDigits: decimals,
  });
}

export function DescriptiveMetricsGrid({ metrics }) {
  if (!metrics) return null;

  const cards = [
    {
      title: 'Tamaño muestral (n)',
      value: metrics.n,
      description: 'Total de observaciones válidas procesadas por el motor estadístico.',
      symbol: 'n',
    },
    {
      title: 'Media muestral (x̄)',
      value: formatNumber(metrics.mean),
      description: 'Centro de gravedad y estimador insesgado de la media poblacional (μ).',
      symbol: 'x̄',
    },
    {
      title: 'Varianza muestral (s²)',
      value: formatNumber(metrics.variance),
      description: 'Dispersión cuadrática respecto a la media con corrección de Bessel (ddof=1).',
      symbol: 's²',
    },
    {
      title: 'Desviación estándar (s)',
      value: formatNumber(metrics.std_dev),
      description: 'Dispersión típica en las unidades originales de la muestra (√s²).',
      symbol: 's',
    },
    {
      title: 'Asimetría (Fisher g₁)',
      value: formatNumber(metrics.skewness),
      description: 'Mide la simetría de la distribución. Normal teórica = 0. Positiva: cola a la derecha.',
      symbol: 'g₁',
    },
    {
      title: 'Exceso de Curtosis (g₂)',
      value: formatNumber(metrics.kurtosis),
      description: 'Puntualidad y peso en colas respecto a la normal (Fisher: normal teórica = 0).',
      symbol: 'g₂',
    },
  ];

  return (
    <Box mb="lg">
      <Text fw={600} size="sm" mb="xs" c="dimmed" style={{ textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Métricas Descriptivas de la Muestra
      </Text>
      <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="sm">
        {cards.map((card, idx) => (
          <Paper
            key={idx}
            withBorder
            p="md"
            radius="md"
            className="stat-card"
          >
            <Group justify="space-between" align="flex-start" mb="xs">
              <Text size="xs" c="dimmed" fw={600}>
                {card.title}
              </Text>
              <Text size="xs" c="blue" fw={700} ff="monospace">
                [{card.symbol}]
              </Text>
            </Group>
            <Text fw={700} size="xl" style={{ letterSpacing: '-0.02em' }}>
              {card.value}
            </Text>
            <Text size="xs" c="dimmed" mt="xs">
              {card.description}
            </Text>
          </Paper>
        ))}
      </SimpleGrid>
    </Box>
  );
}

