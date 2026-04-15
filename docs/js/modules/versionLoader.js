/**
 * versionLoader.js - Carga la versión desde el archivo VERSION
 */

/**
 * Carga la versión desde el archivo VERSION
 * @returns {Promise<string>} La versión del proyecto
 */
export async function loadVersion() {
  try {
    const response = await fetch('../VERSION');
    if (!response.ok) {
      throw new Error(`Error loading VERSION file: ${response.status}`);
    }
    const version = await response.text();
    return version.trim();
  } catch (error) {
    console.error('Error loading version:', error);
    return 'unknown';
  }
}

/**
 * Actualiza el footer con la versión cargada
 * @param {string} version - La versión a mostrar
 */
export function updateFooterVersion(version) {
  const footer = document.querySelector('.footer p');
  if (footer) {
    const versionSpan = footer.querySelector('.version') || document.createElement('span');
    versionSpan.className = 'version';
    versionSpan.textContent = `V${version}`;
    
    // Si no existe el span de versión, insertarlo
    if (!footer.querySelector('.version')) {
      // Encontrar el lugar donde insertar (después de "Cívicos Burgos. ")
      const text = footer.innerHTML;
      footer.innerHTML = text.replace(
        'Cívicos Burgos. ',
        `Cívicos Burgos. <span class="version">V${version}</span> `
      );
    }
  }
}
