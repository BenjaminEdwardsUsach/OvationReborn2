# thresholds.py - UMBRALES EXACTOS DEL PAPER NEWELL ET AL. (1996)
PAPER_THRESHOLDS = {
    'b1e': {
        'min_jump': 2.0,           # Factor de salto mínimo normal
        'high_flux_jump': 1.6,     # Factor de salto para flujo alto
        'high_flux_thresh': 8.0,   # log10(eV/cm² s sr) - umbral flujo alto
        'very_high_flux': 8.25,    # log10(eV/cm² s sr) - detección directa
        'background_window': 10    # Ventana para cálculo de fondo
    },
    'b1i': {
        'min_jump': 2.0,
        'high_flux_jump': 1.6,
        'high_flux_thresh': 6.5,
        'very_high_flux': 6.9,
        'background_window': 10
    },
    'b2e': {
        'low_flux_thresh': 11.0,   # log10(eV/cm² s sr)
        'energy_thresh': 1000,     # eV
        'lookahead': 9,            # segundos para verificar aumento
        'verification_window': 30   # segundos para verificación adicional
    },
    'b2i': {
        'min_flux': 10.5,          # log10(eV/cm² s sr) - mínimo aceptable
        'min_energy': 3000,        # eV - límite inferior para iones
        'max_energy': 30000,       # eV - límite superior para iones
        'avg_window': 2,           # ventana de promediado
        'lookahead': 10            # segundos para buscar máximos
    },
    'b4s': {
        'min_corr': 0.6,           # coeficiente de correlación mínimo
        'sum_threshold': 4.0,      # suma umbral de 7 correlaciones
        'subvisual_thresh': 10.7,  # 0.25 erg/cm² s en log10
        'n_corr': 5,               # número de espectros anteriores
        'n_sum': 7                 # ventana para suma móvil
    },
    'b5e': {
        'min_flux': 10.5,          # log10(eV/cm² s sr)
        'drop_factor': 4,          # factor de caída (4x)
        'window': 12,              # ventana de promediado
        'lookahead': 30            # segundos de verificación
    },
    'b5i': {
        'min_flux': 9.7,
        'drop_factor': 4,
        'window': 12,
        'lookahead': 35
    },
    'b6': {
        'min_flux_e': 10.4,        # log10(eV/cm² s sr)
        'min_flux_i': 9.6,
        'max_energy': 500,         # eV - para verificación física
        'min_flux_physical': 10.0  # flujo mínimo físico
    }
}