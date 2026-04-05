/**
 * shareHandler.js - Manejo de funcionalidad de compartir
 */

/**
 * Genera un ID único para una actividad
 * Formato: {civico_id}_{fecha_yyyymmdd}_{index}
 * @param {Object} activity - Objeto de actividad
 * @param {number} index - Índice de la actividad en la lista (para desambiguar)
 * @returns {string} ID único de la actividad
 */
export function generateActivityId(activity, index = 0) {
  const civicId = activity.civico.toLowerCase().replace(/\s+/g, '_');
  
  // Normalizar fecha a formato YYYYMMDD
  // Maneja formatos: YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY
  let dateStr = '';
  const fecha = activity.fecha.trim();
  
  if (fecha.includes('-')) {
    const parts = fecha.split('-');
    if (parts[0].length === 4) {
      // YYYY-MM-DD
      dateStr = `${parts[0]}${parts[1]}${parts[2]}`;
    } else {
      // DD-MM-YYYY
      dateStr = `${parts[2]}${parts[1]}${parts[0]}`;
    }
  } else if (fecha.includes('/')) {
    // DD/MM/YYYY
    const parts = fecha.split('/');
    dateStr = `${parts[2]}${parts[1]}${parts[0]}`;
  } else {
    // Asumir que ya está en YYYYMMDD
    dateStr = fecha;
  }
  
  return `${civicId}_${dateStr}${index > 0 ? `_${index}` : ''}`;
}

/**
 * Genera una URL compartible para una actividad
 * @param {Object} activity - Objeto de actividad
 * @param {string} monthStr - Mes en formato YYYYMM
 * @param {number} index - Índice de la actividad
 * @param {string} baseUrl - URL base del sitio (default: ubicación actual)
 * @returns {string} URL compartible
 */
export function generateActivityShareUrl(activity, monthStr, index = 0, baseUrl = '') {
  if (!baseUrl) {
    baseUrl = `${window.location.protocol}//${window.location.host}${window.location.pathname}`;
  }
  
  const activityId = generateActivityId(activity, index);
  return `${baseUrl}?month=${monthStr}&activity=${activityId}`;
}

/**
 * Genera una URL compartible para la página principal
 * @param {string} baseUrl - URL base del sitio
 * @returns {string} URL compartible
 */
export function generateWebShareUrl(baseUrl = '') {
  if (!baseUrl) {
    baseUrl = `${window.location.protocol}//${window.location.host}${window.location.pathname}`;
  }
  return baseUrl;
}

/**
 * Genera los enlaces de compartición para diferentes plataformas
 * @param {string} shareUrl - URL a compartir
 * @param {string} title - Título para compartir
 * @param {string} text - Texto adicional para compartir
 * @returns {Object} Objeto con URLs para cada plataforma
 */
export function generateShareLinks(shareUrl, title = '', text = '') {
  const encodedUrl = encodeURIComponent(shareUrl);
  const encodedTitle = encodeURIComponent(title);
  const encodedText = encodeURIComponent(text);
  
  return {
    whatsapp: `https://wa.me/?text=${encodedText}%20${encodedUrl}`,
    twitter: `https://twitter.com/intent/tweet?text=${encodedTitle}&url=${encodedUrl}`,
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`,
    email: `mailto:?subject=${encodedTitle}&body=${encodedText}%0A%0A${encodedUrl}`,
    copy: shareUrl
  };
}

/**
 * Copia un texto al portapapeles
 * @param {string} text - Texto a copiar
 * @returns {Promise<boolean>} true si se copió correctamente
 */
export async function copyToClipboard(text) {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    } else {
      // Fallback para navegadores antiguos
      const textarea = document.createElement('textarea');
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      const success = document.execCommand('copy');
      document.body.removeChild(textarea);
      return success;
    }
  } catch (err) {
    console.error('Error al copiar al portapapeles:', err);
    return false;
  }
}

/**
 * Maneja un clic en un botón de compartir
 * @param {string} platform - Plataforma ('whatsapp', 'twitter', 'facebook', 'email', 'copy')
 * @param {string} shareUrl - URL a compartir
 * @param {string} title - Título para compartir
 * @param {string} text - Texto adicional
 * @returns {Promise<void>}
 */
export async function handleShareClick(platform, shareUrl, title = '', text = '') {
  const links = generateShareLinks(shareUrl, title, text);
  
  if (platform === 'copy') {
    const success = await copyToClipboard(shareUrl);
    if (success) {
      // Feedback visual (opcional: mostrar notificación)
      console.log('Enlace copiado al portapapeles');
    }
  } else if (links[platform]) {
    window.open(links[platform], '_blank', 'width=600,height=400');
  }
}
