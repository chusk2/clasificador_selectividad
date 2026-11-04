# Clasificador de ejercicios · Física · Campo eléctrico y magnético

Vas a recibir el enunciado de un ejercicio de selectividad (PEvAU/EBAU de Andalucía). Clasifícalo en **una sola** de las etiquetas definidas abajo.

```python
'Conf. Electrónica': {
        'verdader' : 'Verdadero o Falso',
        'veracidad' : 'Verdadero o Falso',
        
        # campo eléctrico
        "puntos A" : "distribución de cargas",
        "trabajo" : "distribución de cargas",
        "tercera carga" : "distribución de cargas",
        "se desplaza al punto" : "distribución de cargas",
        "potencial eléctrico" : "campo eléctrico",
        "superficie equipotencial" : "superficie equipotencial teoría",
        'energía potencial' : 'distribución de cargas',
        '10 - 9 C' : "distribución de cargas",
        '10 - 6 C' : "distribución de cargas",
        '10 - 4 C' : "distribución de cargas",
        "trasladar" : "distrubución de cargas",
        "cargas puntuales" : "distribución de cargas",
        "en el origen" : "distribución de cargas",
        "situadas en los puntos" : "distribución de cargas",
        'trabajo' : 'distribución de cargas',
        "campo eléctrico uniforme" : "fuerza campo eléctrico",
        
        # campo magnético
        'radio' : 'campo magnético trayectoria',
        "parte del reposo" : 'acelerado diferencia de potencial',
        "parte del resposo es acelerado" : 'acelerado diferencia de potencial',
        'trayectoria' : 'trayectoria campo magnético',
        'periodo': 'trayectoria campo magnético',

        "bobina" : "flujo magnético",
        "B ( t )" : "flujo magnético",
        "B ( t )" : "flujo magnético campo varía tiempo",
        "flujo magnético" : "flujo magnético",
        "fuerza electromotriz" : "flujo magnético",
        "f.e.m." : "flujo magnético",
        'espira' : 'flujo magnético',
        "girar" : "flujo magnético ángulo varía tiempo",
        "velocidad angular" : "flujo magnético ángulo varía tiempo",
        "Hz" : "flujo magnético ángulo varía tiempo",
        "acelerado" : "trayectoria campo magnético",
        
        "perpendiculares entre sí" : "carga no se desvíe",
        "corriente inducida' : 'inducción magnética',
        "imán" : "corriente inducida por imán",
        "campo magnético uniforme" : "sentido corriente inducida"
        
        'móvil': 'experimento de Henry',
        'lado móvil' : 'experimento de Henry',
        
        "dos conductores rectlilíneos, muy largos" : "fuerza entre conductores",
        'conductor rectilíneo': 'campo magnético conductor rectilíneo',
        'hilo rectilíneo': 'campo magnético conductor rectilíneo',
        'conductores rectilíneos': "fuerza entre conductores",
        'segundo hilo': "fuerza entre conductores",
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
