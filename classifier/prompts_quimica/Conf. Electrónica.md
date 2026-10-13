Usa estas directrices para clasificar cada ejercicio (cada línea es un ejercicio) del archivo csv.

```python
'Conf. Electrónica': {
        'verdader' : 'Verdadero o Falso',
        'veracidad' : 'Verdadero o Falso',
        'radio' : 'Propiedades periódicas',
        'energía de ionización' : 'Propiedades periódicas',
        'afinidad electrónica' : 'Propiedades periódicas',
        'electronegatividad' : 'Propiedades periódicas',
        'primera energía de ionización' : 'Comparación energías de ionización',
        'Na+' : 'Radio / energía ionización Na+ y Ne',
        'estable' : 'Ion más estable',
        'números cuánticos' : 'Combinaciones de números cuánticos',
        'posibles' : 'Combinaciones de números cuánticos',
        'período' : 'Situar elementos en tabla periódica (grupo y período)',
        'energía reticular' : 'Ciclo de Born-Haber',
        'Br2 es líquido y el I2 es sólido' : 'Fuerzas de London',
        'agua es líquida' : 'Puentes de hidrógeno',
        'fusión' : 'Ecuación de Born-Landé',
        'dureza' : 'Ecuación de Born-Landé',
        'mayor energía reticular' : 'Ecuación de Born-Landé',
    }
```

El diccionario de python anterior contiene como keys las palabras claves que te permitirán identificar a los ejercicios usando los enunciados (statement dentro del archivo csv). Como valor para cada key, está el tipo de ejercicio (tipo_ejercicio).

A la hora de clasificar, genera un archivo csv una columna adicional al final, llamada "tipo_ejercicio", que contenga el valor del tipo de ejercicio. Los valores posibles para "tipo_ejercicio" son los values del python dict anterior. No generes la columna "statement" en el csv de salida.

Algunos ejercicios pueden clasificarse en varias categorías al mismo tiempo. En dicho caso, separa las categorías usando " | ".