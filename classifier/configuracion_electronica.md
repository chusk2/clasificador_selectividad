# Clasificador de ejercicios · Química · Configuración electrónica

Vas a recibir el enunciado de un ejercicio de selectividad (PEvAU/EBAU de Andalucía). Clasifícalo en **una sola** de las etiquetas definidas abajo.

```python
'Conf. Electrónica': {
        'verdader' : 'Verdadero o Falso',
        'veracidad' : 'Verdadero o Falso',
        'radio' : 'Propiedades periódicas',
        'energía de ionización' : 'Propiedades periódicas',
        'afinidad electrónica' : 'Propiedades periódicas',
        'electronegatividad' : 'Propiedades periódicas',
        'primera energía de ionización' : 'Comparación energías de ionización',
        'Na+' : 'Radio|energía ionización Na+ y Ne',
        'estable' : 'Ion más estable',
        'números cuánticos' : 'Combinaciones de números cuánticos',
        'posibles' : 'Combinaciones de números cuánticos',
        'período' : 'Situar elementos en tabla periódica (grupo y período)',
		'periodo' : 'Situar elementos en tabla periódica (grupo y período)'
    }
```

El diccionario de python anterior contiene como keys las palabras claves que te permitirán identificar a los ejercicios usando los enunciados. Como valor para cada key (palabra clave contenida en el enunciado), le corresponde un value (tipo_ejercicio, que devolverás como value para el key "tipo_ejercicio" en el json).

Algunos ejercicios pueden clasificarse en varias categorías al mismo tiempo. En dicho caso, separa las categorías usando " | ".
## Nivel de confianza

- **alta:** aparecen palabras clave de la etiqueta y el contexto no deja dudas.
- **media:** el contexto encaja, pero faltan palabras clave o el ejercicio mezcla aspectos de varias etiquetas.
- **baja:** se ha asignado la etiqueta por defecto sin indicios claros, o el texto está demasiado dañado para interpretarlo con seguridad.

## Formato de respuesta

Responde SOLO con un JSON en una línea, sin texto adicional ni bloques de código:

{"tipo_ejercicio": "<{{etiqueta_1}}|{{etiqueta_2}}|{{ETIQUETA_POR_DEFECTO}}>", "confianza": "alta|media|baja"}
