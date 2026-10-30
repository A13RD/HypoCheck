import React, { useMemo } from 'react';
import {
  Paper,
  Textarea,
  Select,
  Group,
  Button,
  Stack,
  Text,
  Badge,
  Alert,
  Box,
} from '@mantine/core';
import {
  IconCalculator,
  IconTrash,
  IconAlertTriangle,
  IconCheck,
} from '@tabler/icons-react';

/**
 * Parsea el contenido de texto separando por comas, espacios o saltos de línea.
 * Devuelve arreglo de números válidos y lista de errores de parseo si los hay.
 */
export function parseSampleInput(text) {
  if (!text || !text.trim()) {
    return { numbers: [], invalidTokens: [], count: 0 };
  }

  // Divide por comas, saltos de línea o espacios múltiples
  const tokens = text
    .split(/[\s,\n\r]+/)
    .map((t) => t.trim())
    .filter((t) => t.length > 0);

  const numbers = [];
  const invalidTokens = [];

  for (const token of tokens) {
    const num = Number(token);
    if (!Number.isNaN(num) && Number.isFinite(num)) {
      numbers.push(num);
    } else {
      invalidTokens.push(token);
    }
  }

  return { numbers, invalidTokens, count: numbers.length };
}

export function DataInputPanel({
  value,
  onChange,
  onClear,
  alpha,
  onAlphaChange,
  onAnalyze,
  isLoading,
  isStale,
  hasExistingResults,
}) {
  const { numbers, invalidTokens, count } = useMemo(() => parseSampleInput(value), [value]);

  const isValidSize = count >= 10;
  const hasInvalidTokens = invalidTokens.length > 0;
  const canAnalyze = isValidSize && !hasInvalidTokens && !isLoading;

  return (
    <Paper withBorder p="md" radius="md" mb="lg">
      <Stack gap="sm">
        <Group justify="space-between" align="center" wrap="wrap">
          <Text fw={600} size="sm">
            Entrada de Muestra Numérica Unidimensional
          </Text>
          <Group gap="xs">
            <Badge
              color={count === 0 ? 'gray' : isValidSize ? 'teal' : 'red'}
              variant="light"
            >
              n = {count} observaciones {isValidSize ? '(Válido)' : '(Mínimo 10)'}
            </Badge>
          </Group>
        </Group>

        <Textarea
          placeholder="Ingrese números separados por comas o saltos de línea. Ej: 160.2, 172.5, 180.1, 165.8, 190.3, 175.0, 168.9, 183.2, 170.4, 177.1"
          minRows={4}
          maxRows={8}
          autosize
          value={value}
          onChange={(e) => onChange(e.currentTarget.value)}
          disabled={isLoading}
          error={
            hasInvalidTokens
              ? `Tokens no numéricos detectados (${invalidTokens.slice(0, 5).join(', ')}${
                  invalidTokens.length > 5 ? '...' : ''
                })`
              : !isValidSize && count > 0
              ? `Muestra insuficiente: contiene ${count} observaciones (se requieren al menos 10).`
              : null
          }
        />

        <Group justify="space-between" align="flex-end" wrap="wrap" mt="xs">
          <Box style={{ minWidth: '200px' }}>
            <Select
              label="Nivel de significancia (α)"
              description="Nivel de corte para la regla de decisión de las pruebas"
              value={String(alpha)}
              onChange={(val) => onAlphaChange(Number(val))}
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
              onClick={onClear}
              disabled={isLoading || (!value && count === 0)}
              size="sm"
            >
              Limpiar datos
            </Button>

            <Button
              variant="filled"
              color="blue"
              leftSection={<IconCalculator size={16} />}
              onClick={() => onAnalyze(numbers)}
              loading={isLoading}
              disabled={!canAnalyze}
              size="sm"
            >
              Analizar muestra
            </Button>
          </Group>
        </Group>

        {isStale && hasExistingResults && (
          <Alert
            icon={<IconAlertTriangle size={16} />}
            color="yellow"
            variant="light"
            title="Datos modificados"
          >
            <Text size="xs">
              Los datos en el editor o el nivel de significancia han cambiado. Los resultados visualizados corresponden al análisis previo. Pulse <strong>Analizar muestra</strong> para actualizar.
            </Text>
          </Alert>
        )}
      </Stack>
    </Paper>
  );
}

