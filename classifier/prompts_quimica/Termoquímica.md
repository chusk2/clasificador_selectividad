Usa estas directrices para clasificar cada ejercicio (cada línea es un ejercicio) del archivo csv.

```python
'Termoquímica' : {
	'verdader' : 'Verdadero o Falso',
	'C-C': 'Entalpías de enlace',
	'S*' : 'Cálculo de entropía',
	"S'":  'Cálculo de entropía',
	'[' : 'Entalpías de formación',
	'a partir de los siguientes datos' : 'Ley de Hess',
	'a volumen constante' : 'Relación entalpía y energía interna',
	'trabajo' : '1er Principio de la Termodinámica',
	'interna' : '1er Principio de la Termodinámica',
	'entalpías de combustión' : 'Ley de Hess',
	'temperatura' : 'Energía libre de Gibbs teórico',
	}
```
El diccionario de python anterior contiene como keys las palabras claves que te permitirán identificar a los ejercicios usando los enunciados (statement dentro del archivo csv). Como valor para cada key, está el tipo de ejercicio (tipo_ejercicio).

A la hora de clasificar, genera un archivo csv una columna adicional al final, llamada "tipo_ejercicio", que contenga el valor del tipo de ejercicio. Los valores posibles para "tipo_ejercicio" son los values del python dict anterior. No generes la columna "statement" en el csv de salida.

Algunos ejercicios pueden clasificarse en varias categorías al mismo tiempo. En dicho caso, separa las categorías usando " | ".