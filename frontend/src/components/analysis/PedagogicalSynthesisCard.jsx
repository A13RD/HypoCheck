import React from 'react';
import { Paper, Title, Text, Stack, Alert, Box, ThemeIcon, Group, Divider } from '@mantine/core';
import { IconSchool, IconAlertTriangle, IconNotes } from '@tabler/icons-react';

export function PedagogicalSynthesisCard({ synthesisText, warnings = [] }) {
  if (!synthesisText) return null;

  return (
    <Paper
      withBorder
      p="lg"
      radius="md"
      mb="xl"
      style={{
        borderLeft: '4px solid var(--mantine-color-indigo-6)',
        backgroundColor: 'var(--mantine-color-default-hover)',
      }}
    >
      <Stack gap="md">
        <Group justify="space-between" align="center" wrap="wrap">
          <Group gap="sm">
            <ThemeIcon color="indigo" size="lg" radius="md">
              <IconSchool size={20} />
            </ThemeIcon>
            <div>
              <Title order={4} style={{ letterSpacing: '-0.01em' }}>
                Síntesis Académica y Guía de Sustentación
              </Title>
              <Text size="xs" c="dimmed">
                Dictamen estadístico integral generado dinámicamente por el motor de inferencia
              </Text>
            </div>
          </Group>
        </Group>

        <Divider />

        <Box className="synthesis-content">
          <Text size="sm" style={{ whiteSpace: 'pre-line', lineHeight: 1.7 }}>
            {synthesisText}
          </Text>
        </Box>

        {warnings && warnings.length > 0 && (
          <Alert
            icon={<IconAlertTriangle size={16} />}
            color="orange"
            variant="light"
            title="Advertencias metodológicas registradas en el análisis"
          >
            <Stack gap={4}>
              {warnings.map((w, idx) => (
                <Text size="xs" key={idx}>
                  • {w}
                </Text>
              ))}
            </Stack>
          </Alert>
        )}

        <Alert
          icon={<IconNotes size={16} />}
          color="blue"
          variant="subtle"
          title="Claves metodológicas para la sustentación evaluativa"
        >
          <Text size="xs" c="dimmed">
            1. <strong>Regla del valor-p</strong>: si valor-p &lt; α, se rechaza H₀ con significancia estadística.
            <br />
            2. <strong>Principio epistemológico</strong>: la ausencia de rechazo demuestra <em>compatibilidad</em> con el modelo normal, jamás que la población sea estrictamente normal.
            <br />
            3. <strong>Discrepancias entre pruebas</strong>: no se aplican votaciones por mayoría; las diferencias reflejan sensibilidades diferenciadas (colas en A-D vs. centro en K-S vs. correlación de cuantiles en S-W).
          </Text>
        </Alert>
      </Stack>
    </Paper>
  );
}

