import React from 'react';
import { Group, Button, Paper, Text, Badge, Alert, Stack } from '@mantine/core';
import { IconDatabase, IconInfoCircle } from '@tabler/icons-react';
import { PRESET_SCENARIOS } from '../../data/presets';

export function PresetSelector({ selectedPresetId, onSelectPreset, disabled }) {
  const selectedPreset = selectedPresetId ? PRESET_SCENARIOS[selectedPresetId] : null;

  return (
    <Paper withBorder p="md" radius="md" mb="md" style={{ backgroundColor: 'var(--mantine-color-default-hover)' }}>
      <Stack gap="xs">
        <Group justify="space-between" align="center" wrap="wrap">
          <Group gap="xs">
            <IconDatabase size={18} color="var(--mantine-color-blue-6)" />
            <Text fw={600} size="sm">
              Escenarios Precargados y Deterministas
            </Text>
          </Group>
          {selectedPreset && (
            <Badge variant="dot" color="blue" size="sm">
              {selectedPreset.title}
            </Badge>
          )}
        </Group>

        <Text size="xs" c="dimmed">
          Seleccione un escenario académico de referencia con datos sintéticos reproducibles o ingrese sus propias observaciones.
        </Text>

        <Group gap="sm" mt="xs" wrap="wrap">
          <Button
            size="xs"
            variant={selectedPresetId === 'ecommerce' ? 'filled' : 'light'}
            color="indigo"
            onClick={() => onSelectPreset('ecommerce')}
            disabled={disabled}
          >
            Cargar escenario de Latencias E-Commerce
          </Button>

          <Button
            size="xs"
            variant={selectedPresetId === 'rubricNormal' ? 'filled' : 'light'}
            color="teal"
            onClick={() => onSelectPreset('rubricNormal')}
            disabled={disabled}
          >
            Cargar Escenario 1 - Rúbrica (Normal)
          </Button>

          <Button
            size="xs"
            variant={selectedPresetId === 'rubricGamma' ? 'filled' : 'light'}
            color="orange"
            onClick={() => onSelectPreset('rubricGamma')}
            disabled={disabled}
          >
            Cargar Escenario 2 - Rúbrica (Gamma)
          </Button>
        </Group>

        {selectedPreset && (
          <Alert
            icon={<IconInfoCircle size={16} />}
            color={selectedPresetId === 'rubricNormal' ? 'teal' : selectedPresetId === 'ecommerce' ? 'indigo' : 'orange'}
            variant="light"
            mt="xs"
            title={
              selectedPresetId === 'ecommerce'
                ? 'Datos simulados de latencias E-Commerce'
                : selectedPreset.title
            }
          >
            <Text size="xs">{selectedPreset.description}</Text>
          </Alert>
        )}
      </Stack>
    </Paper>
  );
}

