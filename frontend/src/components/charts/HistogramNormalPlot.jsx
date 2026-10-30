import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import { Paper, Text, Stack } from '@mantine/core';

export function HistogramNormalPlot({ data, mean, stdDev, isDarkMode }) {
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return [];

    const traces = [];

    // 1. Trace del histograma con normalización 'probability density'
    traces.push({
      x: data,
      type: 'histogram',
      histnorm: 'probability density',
      name: 'Densidad empírica (Muestra)',
      opacity: 0.65,
      marker: {
        color: isDarkMode ? '#4dabf7' : '#339af0',
        line: {
          color: isDarkMode ? '#1971c2' : '#1c7ed6',
          width: 1.2,
        },
      },
      autobinx: true,
      hoverinfo: 'x+y',
    });

    // 2. Trace de la curva normal teórica superpuesta (solo si stdDev > 0 y finito)
    if (
      typeof mean === 'number' &&
      typeof stdDev === 'number' &&
      Number.isFinite(mean) &&
      Number.isFinite(stdDev) &&
      stdDev > 0
    ) {
      const minX = Math.min(...data, mean - 3.5 * stdDev);
      const maxX = Math.max(...data, mean + 3.5 * stdDev);
      const numPoints = 150;
      const step = (maxX - minX) / (numPoints - 1);

      const xCurve = [];
      const yCurve = [];
      const factor = 1 / (stdDev * Math.sqrt(2 * Math.PI));

      for (let i = 0; i < numPoints; i++) {
        const x = minX + i * step;
        const z = (x - mean) / stdDev;
        const y = factor * Math.exp(-0.5 * z * z);
        xCurve.push(x);
        yCurve.push(y);
      }

      traces.push({
        x: xCurve,
        y: yCurve,
        type: 'scatter',
        mode: 'lines',
        name: `Densidad Teórica N(μ=${mean.toFixed(2)}, σ=${stdDev.toFixed(2)})`,
        line: {
          color: '#fa5252',
          width: 2.5,
        },
        hoverinfo: 'x+y',
      });
    }

    return traces;
  }, [data, mean, stdDev, isDarkMode]);

  const layout = useMemo(
    () => ({
      autosize: true,
      title: {
        text: 'Histograma de Frecuencias con Curva Normal Teórica Superpuesta',
        font: {
          size: 14,
          color: isDarkMode ? '#e9ecef' : '#212529',
          family: 'Inter, sans-serif',
        },
      },
      xaxis: {
        title: {
          text: 'Valores de la variable (x)',
          font: { size: 12, color: isDarkMode ? '#adb5bd' : '#495057' },
        },
        color: isDarkMode ? '#adb5bd' : '#495057',
        gridcolor: isDarkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
        zerolinecolor: isDarkMode ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.12)',
      },
      yaxis: {
        title: {
          text: 'Densidad de probabilidad f(x)',
          font: { size: 12, color: isDarkMode ? '#adb5bd' : '#495057' },
        },
        color: isDarkMode ? '#adb5bd' : '#495057',
        gridcolor: isDarkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
        zerolinecolor: isDarkMode ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.12)',
      },
      legend: {
        orientation: 'h',
        y: -0.22,
        x: 0.1,
        font: { size: 11, color: isDarkMode ? '#ced4da' : '#343a40' },
      },
      margin: { l: 55, r: 25, t: 45, b: 65 },
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
          La curva roja ilustra la función de densidad de probabilidad normal teórica paramétrica
          ajustada con la media muestral ({mean !== null ? mean.toFixed(2) : 'N/D'}) y desviación típica (
          {stdDev !== null ? stdDev.toFixed(2) : 'N/D'}). Las barras representan la densidad empírica de los datos.
        </Text>
      </Stack>
    </Paper>
  );
}

