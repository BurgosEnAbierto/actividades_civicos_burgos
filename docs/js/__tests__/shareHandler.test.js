/**
 * shareHandler.test.js - Tests para funcionalidad de compartir
 */

import {
  generateActivityId,
  generateActivityShareUrl,
  generateWebShareUrl,
  generateShareLinks
} from '../modules/shareHandler.js';

describe('shareHandler', () => {
  describe('generateActivityId', () => {
    test('debería generar ID correctamente con formato DD/MM/YYYY', () => {
      const activity = {
        civico: 'Capiscol',
        fecha: '31/03/2026'
      };
      const id = generateActivityId(activity, 0);
      expect(id).toBe('capiscol_20260331');
    });

    test('debería generar ID correctamente con formato DD-MM-YYYY', () => {
      const activity = {
        civico: 'Rio Vena',
        fecha: '04-02-2026'
      };
      const id = generateActivityId(activity, 0);
      expect(id).toBe('rio_vena_20260204');
    });

    test('debería generar ID correctamente con formato YYYY-MM-DD', () => {
      const activity = {
        civico: 'San Juan',
        fecha: '2026-02-15'
      };
      const id = generateActivityId(activity, 0);
      expect(id).toBe('san_juan_20260215');
    });

    test('debería incluir índice cuando index > 0', () => {
      const activity = {
        civico: 'Huelgas',
        fecha: '01/01/2026'
      };
      const id = generateActivityId(activity, 2);
      expect(id).toBe('huelgas_20260101_2');
    });

    test('debería convertir espacios en civico a underscores', () => {
      const activity = {
        civico: 'San Agustín Centro',
        fecha: '10/03/2026'
      };
      const id = generateActivityId(activity, 0);
      expect(id).toBe('san_agustín_centro_20260310');
    });

    test('debería normalizar el civico a minúsculas', () => {
      const activity = {
        civico: 'GAMONAL NORTE',
        fecha: '20/05/2026'
      };
      const id = generateActivityId(activity, 0);
      expect(id).toBe('gamonal_norte_20260520');
    });

    test('debería manejar espacios con trim', () => {
      const activity = {
        civico: 'Vista Alegre',
        fecha: '  15/06/2026  '
      };
      const id = generateActivityId(activity, 0);
      expect(id).toBe('vista_alegre_20260615');
    });
  });

  describe('generateActivityShareUrl', () => {
    test('debería generar URL compartible correctamente', () => {
      const activity = {
        civico: 'Capiscol',
        fecha: '31/03/2026'
      };
      const baseUrl = 'https://ejemplo.com/docs/';
      const url = generateActivityShareUrl(activity, '202603', 0, baseUrl);
      
      expect(url).toContain('month=202603');
      expect(url).toContain('activity=capiscol_20260331');
      expect(url).not.toContain('undefined');
    });

    test('debería incluir índice en la URL cuando index > 0', () => {
      const activity = {
        civico: 'Rio Vena',
        fecha: '04/02/2026'
      };
      const baseUrl = 'https://ejemplo.com/docs/';
      const url = generateActivityShareUrl(activity, '202602', 2, baseUrl);
      
      expect(url).toContain('activity=rio_vena_20260204_2');
    });
  });

  describe('generateWebShareUrl', () => {
    test('debería generar URL de la web sin parámetros', () => {
      const baseUrl = 'https://ejemplo.com/docs/';
      const url = generateWebShareUrl(baseUrl);
      
      expect(url).toBe(baseUrl);
      expect(url).not.toContain('?');
      expect(url).not.toContain('&');
    });
  });

  describe('generateShareLinks', () => {
    const shareUrl = 'https://ejemplo.com/docs/?month=202603&activity=capiscol_20260331';
    const title = 'Actividad en Capiscol';
    const text = 'Mira esta actividad';

    test('debería generar enlaces para todas las plataformas', () => {
      const links = generateShareLinks(shareUrl, title, text);
      
      expect(links).toHaveProperty('whatsapp');
      expect(links).toHaveProperty('twitter');
      expect(links).toHaveProperty('facebook');
      expect(links).toHaveProperty('email');
      expect(links).toHaveProperty('copy');
    });

    test('whatsapp link debería tener la URL y texto correcto', () => {
      const links = generateShareLinks(shareUrl, title, text);
      
      expect(links.whatsapp).toContain('wa.me');
      expect(links.whatsapp).toContain(encodeURIComponent(text));
      expect(links.whatsapp).toContain(encodeURIComponent(shareUrl));
    });

    test('twitter link debería tener título y URL', () => {
      const links = generateShareLinks(shareUrl, title, text);
      
      expect(links.twitter).toContain('twitter.com/intent/tweet');
      expect(links.twitter).toContain(encodeURIComponent(title));
      expect(links.twitter).toContain(encodeURIComponent(shareUrl));
    });

    test('facebook link debería tener la URL encoded', () => {
      const links = generateShareLinks(shareUrl, title, text);
      
      expect(links.facebook).toContain('facebook.com/sharer');
      expect(links.facebook).toContain(encodeURIComponent(shareUrl));
    });

    test('email link debería ser un mailto con asunto y cuerpo', () => {
      const links = generateShareLinks(shareUrl, title, text);
      
      expect(links.email).toContain('mailto:');
      expect(links.email).toContain(encodeURIComponent(title));
      expect(links.email).toContain(encodeURIComponent(shareUrl));
    });

    test('copy debería retornar la URL sin formatear', () => {
      const links = generateShareLinks(shareUrl, title, text);
      
      expect(links.copy).toBe(shareUrl);
    });
  });
});
