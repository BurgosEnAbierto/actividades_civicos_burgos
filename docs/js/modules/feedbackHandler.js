/**
 * feedbackHandler.js - Manejo de feedback y reportes de problemas
 */

const FEEDBACK_EMAIL = 'burgosenabierto@proton.me';

/**
 * Genera un enlace mailto para reportar un problema en una actividad
 * @param {Object} activity - Objeto de actividad
 * @param {string} civicName - Nombre del cívico
 * @param {string} month - Mes en formato YYYYMM
 * @returns {string} URL mailto con el email precompletado
 */
export function generateActivityReportMailto(activity, civicName, month) {
  const subject = `Problema en actividad: ${activity.nombre}`;
  
  // Construir el cuerpo del email con información de la actividad
  const bodyLines = [
    'Información de la actividad:',
    `- Nombre: ${activity.nombre}`,
    `- Centro: ${civicName}`,
    `- Mes: ${month}`,
    `- Fecha: ${activity.fecha}`,
    activity.hora ? `- Hora: ${activity.hora}` : '',
    activity.publico ? `- Público: ${activity.publico}` : '',
    '',
    'Problema encontrado:',
    '[Describe aquí qué problema has encontrado en los datos]',
    '',
    'Observaciones adicionales:',
    '[Añade cualquier información adicional que consideres]'
  ]
    .filter(line => line !== '')
    .join('\n');

  const encodedSubject = encodeURIComponent(subject);
  const encodedBody = encodeURIComponent(bodyLines);

  return `mailto:${FEEDBACK_EMAIL}?subject=${encodedSubject}&body=${encodedBody}`;
}

/**
 * Crea un manejador de click para el botón "Reportar problema"
 * @param {Object} activity - Objeto de actividad
 * @param {string} civicName - Nombre del cívico
 * @param {string} month - Mes en formato YYYYMM
 * @returns {Function} Función manejadora del evento click
 */
export function createReportClickHandler(activity, civicName, month) {
  return (e) => {
    e.preventDefault();
    const mailtoUrl = generateActivityReportMailto(activity, civicName, month);
    window.location.href = mailtoUrl;
  };
}
