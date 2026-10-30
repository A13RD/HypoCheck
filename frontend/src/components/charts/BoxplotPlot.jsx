import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import { Paper, Text, Stack } from '@mantine/core';

export function BoxplotPlot({ data, isDarkMode }) {
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return [];

    return [
      {
        y: data,
        type: 'box',
        name: 'Muestra analizada',
        boxpoints: 'outliers',
        jitter: 0.3,
        pointpos: -1.8,
        marker: {
          color: isDarkMode ? '#ff8787' : '#e03131',
          size: 6,
        },
        line: {
          color: isDarkMode ? '#20c997' : '#0ca678',
          width: 2,
        },
        fillcolor: isDarkMode ? 'rgba(32, 201, 151, 0.25)' : 'rgba(12, 166, 120, 0.2)',
        hoverinfo: 'y+name',
      },
    ];
  }, [data, isDarkMode]);

  const layout = useMemo(
    () => ({
      autosize: true,
      title: {
        text: 'Diagrama de Cajas y Bigotes (Boxplot) de la Muestra',
        font: {
          size: 14,
          color: isDarkMode ? '#e9ecef' : '#212529',
          family: 'Inter, sans-serif',
        },
      },
      yaxis: {
        title: {
          text: 'Valores observados',
          font: { size: 12, color: isDarkMode ? '#adb5bd' : '#495057' },
        },
        color: isDarkMode ? '#adb5bd' : '#495057',
        gridcolor: isDarkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
        zerolinecolor: isDarkMode ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.12)',
      },
      xaxis: {
        showticklabels: false,
        color: isDarkMode ? '#adb5bd' : '#495057',
      },
      margin: { l: 55, r: 25, t: 45, b: 35 },
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
    }),
    [isDarkMode]
  );

  return (
    <Paper withBorder p="md" radius="md">
      <Stack gap="xs">
        <div style={{ width: '100%', height: '380px' }}>
          <Plot
            data={chartData}
            layout={layout}
            useResizeHandler
            style={{ width: '100%', height: '100%' }}
            config={{
              responsive: true,
              displayModeBar: true,
              displaylogo: false,
              modeBarButtonsToRemove: ['lasso2d', 'select2d'],
            }}
          />
        </div>
        <Text size="xs" c="dimmed">
          Permite inspeccionar la mediana (Q2), los cuartiles inferior (Q1) y superior (Q3), el rango
          intercuartílico (IQR), la longitud de los bigotes (1.5 × IQR) y los puntos aislados (valores atípicos / outliers).
        </Text>
      </Stack>
    </Paper>
  );
}

