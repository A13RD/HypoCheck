import React from 'react';
import {
  Table,
  Paper,
  Text,
  Badge,
  Group,
  Stack,
  Alert,
  Accordion,
  Box,
  Tooltip,
} from '@mantine/core';
import {
  IconCheck,
  IconX,
  IconAlertCircle,
  IconInfoCircle,
  IconLayersLinked,
} from '@tabler/icons-react';

function formatVal(val, decimals = 5) {
  if (val === null || val === undefined || Number.isNaN(val)) {
    return 'N/D';
  }
  const num = Number(val);
  if (num !== 0 && Math.abs(num) < Math.pow(10, -decimals)) {
    return num.toExponential(3);
  }
  return num.toFixed(decimals);
}

export function GoodnessOfFitTable({ goodnessOfFit, alpha }) {
  if (!goodnessOfFit) return null;

  const {
    kolmogorov_smirnov: ks,
    anderson_darling: ad,
    shapiro_wilk: sw,
    chi_square: chi2,
  } = goodnessOfFit;

  // Renderizador de badge de decisión
  const renderDecisionBadge = (testResult, testName) => {
    // Si la prueba expone disponibilidad y es falsa
    if (testResult?.available === false) {
      return (
        <Tooltip label={testResult.reason || 'Prueba no aplicable con los datos suministrados'}>
          <Badge color="gray" variant="filled">
            No disponible
          </Badge>
        </Tooltip>
      );
    }

    if (testResult?.rejected === true) {
      return (
        <Tooltip label="Existe evidencia suficiente para rechazar H0 de normalidad">
          <Badge color="red" variant="filled" leftSection={<IconX size={12} />}>
            Se rechaza H₀ (No normal)
          </Badge>
        </Tooltip>
      );
    }

    if (testResult?.rejected === false) {
      return (
        <Tooltip label="No se detectó evidencia para descartar la normalidad (compatibilidad empírica)">
          <Badge color="teal" variant="filled" leftSection={<IconCheck size={12} />}>
            No se rechaza H₀
          </Badge>
        </Tooltip>
      );
    }

    return (
      <Badge color="gray" variant="light">
        Indeterminado
      </Badge>
    );
  };

  return (
    <Paper withBorder p="md" radius="md" mb="lg">
      <Stack gap="md">
        <Group justify="space-between" align="center" wrap="wrap">
          <div>
            <Text fw={600} size="md">
              Batería Comparativa de Pruebas de Bondad de Ajuste
            </Text>
            <Text size="xs" c="dimmed">
              Contraste formal de las cuatro metodologías al nivel de significancia α = {alpha} (
              {(alpha * 100).toFixed(1)}%).
            </Text>
          </div>
          <Badge variant="outline" color="blue">
            Nivel evaluado: α = {alpha}
          </Badge>
        </Group>

        <Table.ScrollContainer minWidth={650}>
          <Table striped highlightOnHover withTableBorder withColumnBorders className="scientific-table">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Prueba Estadística</Table.Th>
                <Table.Th>Estadístico</Table.Th>
                <Table.Th>Valor Crítico</Table.Th>
                <Table.Th>Valor-p</Table.Th>
                <Table.Th>Decisión Formal</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {/* Kolmogorov-Smirnov */}
              <Table.Tr>
                <Table.Td>
                  <Text fw={600} size="sm">
                    Kolmogorov-Smirnov (Lilliefors)
                  </Text>
                  <Text size="xs" c="dimmed">
                    Calibración Monte Carlo con reestimación
                  </Text>
                </Table.Td>
                <Table.Td>
                  <Text ff="monospace" fw={600}>
                    D = {formatVal(ks?.statistic)}
                  </Text>
                </Table.Td>
                <Table.Td>
                  <Text size="xs" c="dimmed">
                    Calibración empírica (9999 réplicas)
                  </Text>
                </Table.Td>
                <Table.Td>
                  <Text ff="monospace" fw={600} c={ks?.p_value < alpha ? 'red' : 'teal'}>
                    p = {formatVal(ks?.p_value)}
                  </Text>
                </Table.Td>
                <Table.Td>{renderDecisionBadge(ks, 'Kolmogorov-Smirnov')}</Table.Td>
              </Table.Tr>

              {/* Anderson-Darling */}
              <Table.Tr>
                <Table.Td>
                  <Text fw={600} size="sm">
                    Anderson-Darling
                  </Text>
                  <Text size="xs" c="dimmed">
                    Ponderación cuadrática en colas
                  </Text>
                </Table.Td>
                <Table.Td>
                  <Text ff="monospace" fw={600}>
                    A² = {formatVal(ad?.statistic)}
                  </Text>
                </Table.Td>
                <Table.Td>
                  <Text ff="monospace" fw={600}>
                    VC = {formatVal(ad?.critical_value, 4)}
                  </Text>
                </Table.Td>
                <Table.Td>
                  <Tooltip label="Anderson-Darling evalúa la decisión contra valores críticos tabulados; el backend reporta null">
                    <Text size="xs" c="dimmed" fs="italic">
                      No reportado
                    </Text>
                  </Tooltip>
                </Table.Td>
                <Table.Td>{renderDecisionBadge(ad, 'Anderson-Darling')}</Table.Td>
              </Table.Tr>

              {/* Shapiro-Wilk */}
              <Table.Tr>
                <Table.Td>
                  <Group gap="xs">
                    <div>
                      <Text fw={600} size="sm">
                        Shapiro-Wilk
                      </Text>
                      <Text size="xs" c="dimmed">
                        Estadísticos de orden y linealidad
                      </Text>
                    </div>
                    {sw?.warnings && sw.warnings.length > 0 && (
                      <Tooltip label={sw.warnings.join(' | ')}>
                        <Badge color="orange" size="xs" variant="light">
                          Aviso
                        </Badge>
                      </Tooltip>
                    )}
                  </Group>
                </Table.Td>
                <Table.Td>
                  {sw?.available ? (
                    <Text ff="monospace" fw={600}>
                      W = {formatVal(sw?.statistic)}
                    </Text>
                  ) : (
                    <Text size="xs" c="dimmed">
                      N/D
                    </Text>
                  )}
                </Table.Td>
                <Table.Td>
                  <Text size="xs" c="dimmed" fs="italic">
                    No aplica
                  </Text>
                </Table.Td>
                <Table.Td>
                  {sw?.available ? (
                    <Text ff="monospace" fw={600} c={sw?.p_value < alpha ? 'red' : 'teal'}>
                      p = {formatVal(sw?.p_value)}
                    </Text>
                  ) : (
                    <Text size="xs" c="dimmed">
                      N/D
                    </Text>
                  )}
                </Table.Td>
                <Table.Td>{renderDecisionBadge(sw, 'Shapiro-Wilk')}</Table.Td>
              </Table.Tr>

              {/* Chi-cuadrada de Pearson */}
              <Table.Tr>
                <Table.Td>
                  <Text fw={600} size="sm">
                    Chi-cuadrada de Pearson
                  </Text>
                  <Text size="xs" c="dimmed">
                    Fusión de clases con garantía Eᵢ ≥ 5
                  </Text>
                </Table.Td>
                <Table.Td>
                  {chi2?.available ? (
                    <Text ff="monospace" fw={600}>
                      EP = {formatVal(chi2?.statistic)}
                    </Text>
                  ) : (
                    <Text size="xs" c="dimmed">
                      N/D
                    </Text>
                  )}
                </Table.Td>
                <Table.Td>
                  {chi2?.available ? (
                    <Text ff="monospace" fw={600}>
                      χ² = {formatVal(chi2?.critical_value, 4)} (ν = {chi2?.degrees_of_freedom})
                    </Text>
                  ) : (
                    <Text size="xs" c="dimmed">
                      {chi2?.degrees_of_freedom !== null ? `ν = ${chi2?.degrees_of_freedom}` : 'N/D'}
                    </Text>
                  )}
                </Table.Td>
                <Table.Td>
                  {chi2?.available ? (
                    <Text ff="monospace" fw={600} c={chi2?.p_value < alpha ? 'red' : 'teal'}>
                      p = {formatVal(chi2?.p_value)}
                    </Text>
                  ) : (
                    <Text size="xs" c="dimmed">
                      N/D
                    </Text>
                  )}
                </Table.Td>
                <Table.Td>{renderDecisionBadge(chi2, 'Chi-cuadrada')}</Table.Td>
              </Table.Tr>
            </Table.Tbody>
          </Table>
        </Table.ScrollContainer>

        {/* Advertencias específicas de las pruebas */}
        {sw?.warnings && sw.warnings.length > 0 && (
          <Alert
            icon={<IconAlertCircle size={16} />}
            color="orange"
            variant="light"
            title="Advertencia metodológica en Shapiro-Wilk"
          >
            {sw.warnings.map((warn, i) => (
              <Text size="xs" key={i}>
                • {warn}
              </Text>
            ))}
          </Alert>
        )}

        {/* Diagnóstico si Chi-cuadrada no estuvo disponible */}
        {chi2 && !chi2.available && (
          <Alert
            icon={<IconInfoCircle size={16} />}
            color="gray"
            variant="light"
            title="Condición de no aplicabilidad en Chi-cuadrada"
          >
            <Text size="xs">{chi2.reason || chi2.academic_verdict}</Text>
          </Alert>
        )}

        {/* Acordeón de detalles metodológicos y dictámenes académicos individuales */}
        <Accordion variant="separated" radius="md">
          <Accordion.Item value="verdicts">
            <Accordion.Control icon={<IconInfoCircle size={18} />}>
              <Text size="xs" fw={600}>
                Ver dictámenes académicos individuales por prueba
              </Text>
            </Accordion.Control>
            <Accordion.Panel>
              <Stack gap="xs">
                {ks && (
                  <Box p="xs" style={{ borderLeft: '3px solid var(--mantine-color-blue-5)' }}>
                    <Text fw={600} size="xs" c="blue">
                      Kolmogorov-Smirnov:
                    </Text>
                    <Text size="xs" style={{ whiteSpace: 'pre-line' }}>
                      {ks.academic_verdict}
                    </Text>
                  </Box>
                )}
                {ad && (
                  <Box p="xs" style={{ borderLeft: '3px solid var(--mantine-color-teal-5)' }}>
                    <Text fw={600} size="xs" c="teal">
                      Anderson-Darling:
                    </Text>
                    <Text size="xs" style={{ whiteSpace: 'pre-line' }}>
                      {ad.academic_verdict}
                    </Text>
                  </Box>
                )}
                {sw && (
                  <Box p="xs" style={{ borderLeft: '3px solid var(--mantine-color-violet-5)' }}>
                    <Text fw={600} size="xs" c="violet">
                      Shapiro-Wilk:
                    </Text>
                    <Text size="xs" style={{ whiteSpace: 'pre-line' }}>
                      {sw.academic_verdict}
                    </Text>
                  </Box>
                )}
                {chi2 && (
                  <Box p="xs" style={{ borderLeft: '3px solid var(--mantine-color-orange-5)' }}>
                    <Text fw={600} size="xs" c="orange">
                      Chi-cuadrada de Pearson:
                    </Text>
                    <Text size="xs" style={{ whiteSpace: 'pre-line' }}>
                      {chi2.academic_verdict}
                    </Text>
                  </Box>
                )}
              </Stack>
            </Accordion.Panel>
          </Accordion.Item>

          {/* Si Chi-cuadrada tiene clases fusionadas, permitir inspeccionar la tabla de frecuencias */}
          {chi2 && chi2.merged_classes && chi2.merged_classes.length > 0 && (
            <Accordion.Item value="chi2-classes">
              <Accordion.Control icon={<IconLayersLinked size={18} />}>
                <Text size="xs" fw={600}>
                  Detalle de clases fusionadas de Chi-cuadrada (k = {chi2.merged_classes_count}, todas con Eᵢ ≥ 5)
                </Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Table.ScrollContainer minWidth={450}>
                  <Table striped withTableBorder size="xs">
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th>Clase</Table.Th>
                        <Table.Th>Intervalo [Límite Inf, Límite Sup)</Table.Th>
                        <Table.Th>Frecuencia Obs. (Oᵢ)</Table.Th>
                        <Table.Th>Frecuencia Esp. (Eᵢ)</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {chi2.merged_classes.map((cls) => (
                        <Table.Tr key={cls.class_index}>
                          <Table.Td>{cls.class_index}</Table.Td>
                          <Table.Td>
                            [{cls.lower_limit === null ? '-∞' : cls.lower_limit.toFixed(2)},{' '}
                            {cls.upper_limit === null ? '+∞' : cls.upper_limit.toFixed(2)})
                          </Table.Td>
                          <Table.Td ff="monospace" fw={600}>
                            {cls.observed_frequency}
                          </Table.Td>
                          <Table.Td ff="monospace">
                            {cls.expected_frequency ? cls.expected_frequency.toFixed(4) : 'N/D'}
                          </Table.Td>
                        </Table.Tr>
                      ))}
                    </Table.Tbody>
                  </Table>
                </Table.ScrollContainer>
              </Accordion.Panel>
            </Accordion.Item>
          )}
        </Accordion>
      </Stack>
    </Paper>
  );
}

