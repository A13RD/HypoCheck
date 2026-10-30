import React from 'react';
import { Container, Text, Group, Box, Anchor } from '@mantine/core';

export function Footer() {
  return (
    <Box
      component="footer"
      mt="3rem"
      py="xl"
      style={{
        borderTop: '1px solid var(--mantine-color-default-border)',
        backgroundColor: 'var(--mantine-color-body)',
      }}
    >
      <Container size="xl">
        <Group justify="space-between" align="center" wrap="wrap">
          <Text size="xs" c="dimmed">
            Suite de Inferencia Estadística y Bondad de Ajuste &copy; 2026-2.
            Universidad de Medellín — Facultad de Ingenierías.
          </Text>
          <Text size="xs" c="dimmed">
            Desarrollado con React 18, Vite, Mantine UI, Plotly.js y FastAPI.
          </Text>
        </Group>
      </Container>
    </Box>
  );
}

