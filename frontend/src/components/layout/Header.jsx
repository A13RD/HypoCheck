import React from 'react';
import {
  Group,
  Title,
  Text,
  Badge,
  ActionIcon,
  useMantineColorScheme,
  useComputedColorScheme,
  Container,
  Paper,
  Box,
  Tooltip,
} from '@mantine/core';
import { IconSun, IconMoon, IconSchool } from '@tabler/icons-react';
import classes from '../../styles/Dashboard.module.css';

export function Header({ apiHealth }) {
  const { setColorScheme } = useMantineColorScheme();
  const computedColorScheme = useComputedColorScheme('light', { getInitialValueInEffect: true });

  const toggleColorScheme = () => {
    setColorScheme(computedColorScheme === 'dark' ? 'light' : 'dark');
  };

  const renderHealthBadge = () => {
    if (!apiHealth) {
      return (
        <Badge
          color="yellow"
          variant="light"
          leftSection={<span className="status-dot-loading" />}
        >
          Comprobando conexión...
        </Badge>
      );
    }

    if (apiHealth.available) {
      return (
        <Tooltip label={`FastAPI v${apiHealth.version || '1.0.0'} en línea`}>
          <Badge
            color="teal"
            variant="light"
            size="md"
            leftSection={<span className="status-dot-active" />}
          >
            API disponible
          </Badge>
        </Tooltip>
      );
    }

    return (
      <Tooltip label={apiHealth.message || 'No fue posible comunicar con el servidor'}>
        <Badge
          color="red"
          variant="light"
          size="md"
          leftSection={<span className="status-dot-inactive" />}
        >
          API no disponible
        </Badge>
      </Tooltip>
    );
  };

  return (
    <Paper shadow="xs" p="md" withBorder className={classes.headerPaper}>
      <Container size="xl">
        <Group justify="space-between" align="center" wrap="wrap">
          <Box>
            <Group gap="xs" align="center" wrap="nowrap">
              <IconSchool size={28} color="var(--mantine-color-blue-6)" style={{ flexShrink: 0 }} />
              <div>
                <Title order={2} className={classes.headerTitle}>
                  Suite de Inferencia Estadística y Bondad de Ajuste
                </Title>
                <Text size="sm" c="dimmed">
                  Proyecto de Aula 2026-2 | Estadística para Ingeniería — <strong>Universidad de Medellín</strong>
                </Text>
              </div>
            </Group>
          </Box>

          <Group gap="md">
            {renderHealthBadge()}

            <Tooltip label={`Cambiar a modo ${computedColorScheme === 'dark' ? 'claro' : 'oscuro'}`}>
              <ActionIcon
                onClick={toggleColorScheme}
                variant="default"
                size="lg"
                aria-label="Alternar esquema de color"
              >
                {computedColorScheme === 'dark' ? <IconSun size={18} /> : <IconMoon size={18} />}
              </ActionIcon>
            </Tooltip>
          </Group>
        </Group>
      </Container>
    </Paper>
  );
}

